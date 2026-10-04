"""
Main ingestion pipeline. Entry point:
    python -m ingestion.pipeline --source all
    python -m ingestion.pipeline --source 01_selenium_framework
    python -m ingestion.pipeline --source 04_jira_tickets --jql "project = QA"
"""
import argparse
import os
import pickle
from pathlib import Path

import yaml
from dotenv import load_dotenv
from loguru import logger

from ingestion.chunker import chunk_blocks
from ingestion.embedder import embed_texts
from ingestion.parsers import (
    code_parser,
    csv_parser,
    jira_parser,
    log_parser,
    markdown_parser,
    pdf_parser,
    text_parser,
)
from retrieval.qdrant_store import ensure_collection, get_client, get_collection_name, upsert_chunks
from retrieval.sparse import BM25SparseEncoder

load_dotenv()

DATA_ROOT = Path("data")
CONFIG_PATH = Path("config/settings.yaml")
JQL_CONFIG_PATH = Path("config/jql_queries.yaml")
ENCODER_PATH = Path("data/bm25_encoder.pkl")

CODE_EXTENSIONS = {".py", ".java", ".ts", ".js", ".tsx", ".jsx"}
PDF_EXTENSIONS = {".pdf"}
CSV_EXTENSIONS = {".csv", ".xlsx", ".xls"}
MD_EXTENSIONS = {".md", ".markdown"}
LOG_EXTENSIONS = {".log", ".txt"}


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def load_jql_config() -> dict:
    with open(JQL_CONFIG_PATH) as f:
        return yaml.safe_load(f)


def get_chunk_params(source_folder: str, config: dict) -> tuple[int, int]:
    source_map = config.get("source_map", {})
    chunk_key = source_map.get(source_folder, "default")
    chunk_cfg = config["chunking"].get(chunk_key, config["chunking"]["default"])
    return chunk_cfg["chunk_tokens"], chunk_cfg["overlap_tokens"]


def iter_raw_blocks(source_folder: str, config: dict):
    """Yield raw text blocks from all files in a source folder."""
    folder = DATA_ROOT / source_folder

    if source_folder == "04_jira_tickets":
        # Special case: fetch from JIRA API
        jql_conf = load_jql_config()
        cache_dir = folder
        for query_name, jql in jql_conf["queries"].items():
            logger.info(f"Fetching JIRA query: {query_name}")
            yield from jira_parser.parse_live(
                jql=jql,
                cache_dir=cache_dir,
                max_results=jql_conf.get("max_results_per_query", 500),
            )
        return

    if not folder.exists():
        logger.warning(f"Source folder not found: {folder}")
        return

    rows_per_chunk = config["chunking"].get("test_cases", {}).get("rows_per_chunk", 5)

    SKIP_DIRS = {
        "node_modules", ".git", ".idea", "__pycache__", "dist",
        "build", ".gradle", "target", "vendor", ".venv", "venv",
        ".augment", ".husky", ".github",
    }

    for file_path in folder.rglob("*"):
        if not file_path.is_file():
            continue
        if any(part in SKIP_DIRS for part in file_path.parts):
            continue
        # Skip binary / large generated files
        if file_path.suffix.lower() in {
            ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff",
            ".woff2", ".ttf", ".eot", ".zip", ".jar", ".class",
            ".pyc", ".lock", ".map", ".min.js", ".min.css",
        }:
            continue
        if file_path.stat().st_size > 500_000:  # skip files > 500 KB
            logger.debug(f"Skipping large file: {file_path}")
            continue
        ext = file_path.suffix.lower()
        try:
            if ext in CODE_EXTENSIONS:
                yield from code_parser.parse(file_path)
            elif ext in CSV_EXTENSIONS:
                yield from csv_parser.parse(file_path, rows_per_chunk=rows_per_chunk)
            elif ext in PDF_EXTENSIONS:
                yield from pdf_parser.parse(file_path)
            elif ext in MD_EXTENSIONS:
                yield from markdown_parser.parse(file_path)
            elif ext in LOG_EXTENSIONS and source_folder == "10_jenkins_logs":
                yield from log_parser.parse(file_path)
            else:
                yield from text_parser.parse(file_path)
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")


def ingest_source(source_folder: str, config: dict, client, collection: str) -> list[str]:
    """Ingest one source folder. Returns list of all chunk texts (for BM25 fitting)."""
    max_tokens, overlap = get_chunk_params(source_folder, config)
    logger.info(f"Ingesting {source_folder} | chunk={max_tokens} overlap={overlap}")

    raw_blocks = iter_raw_blocks(source_folder, config)
    chunks = list(chunk_blocks(raw_blocks, max_tokens, overlap))

    if not chunks:
        logger.info(f"No chunks from {source_folder}")
        return []

    texts = [c["text"] for c in chunks]
    logger.info(f"Embedding {len(texts)} chunks from {source_folder}")
    dense_vecs = embed_texts(texts)

    # Sparse vectors built after BM25 encoder is fitted — placeholder here
    # Will be populated after global BM25 fit in full pipeline
    sparse_vecs = [{"indices": [], "values": []} for _ in chunks]

    upsert_chunks(
        client=client,
        collection=collection,
        chunks=chunks,
        dense_vectors=dense_vecs.tolist(),
        sparse_vectors=sparse_vecs,
    )
    return texts


def run(sources: list[str]) -> None:
    config = load_config()
    client = get_client()
    collection = get_collection_name()
    ensure_collection(client, collection)

    all_texts = []
    all_chunks_by_source: dict[str, list] = {}

    for source in sources:
        raw_blocks = list(iter_raw_blocks(source, config))
        max_tokens, overlap = get_chunk_params(source, config)
        chunks = list(chunk_blocks(raw_blocks, max_tokens, overlap))
        all_chunks_by_source[source] = chunks
        all_texts.extend(c["text"] for c in chunks)

    logger.info(f"Fitting BM25 encoder on {len(all_texts)} total chunks")
    encoder = BM25SparseEncoder()
    encoder.fit(all_texts)
    with open(ENCODER_PATH, "wb") as f:
        pickle.dump(encoder, f)

    for source, chunks in all_chunks_by_source.items():
        if not chunks:
            continue
        texts = [c["text"] for c in chunks]
        logger.info(f"Embedding {len(texts)} chunks from {source}")
        dense_vecs = embed_texts(texts).tolist()
        sparse_vecs = [encoder.encode(t) for t in texts]
        upsert_chunks(
            client=client,
            collection=collection,
            chunks=chunks,
            dense_vectors=dense_vecs,
            sparse_vectors=sparse_vecs,
        )

    logger.info("Ingestion complete.")


def main() -> None:
    all_sources = [
        "01_selenium_framework",
        "02_playwright_framework",
        "03_test_cases",
        "04_jira_tickets",
        "05_company_docs",
        "07_meeting_notes",
        "08_lucid_charts",
        "09_prd_srs_brd_frd",
        "10_jenkins_logs",
    ]

    parser = argparse.ArgumentParser(description="QABuddy ingestion pipeline")
    parser.add_argument(
        "--source",
        default="all",
        help='Source folder name or "all". E.g.: 01_selenium_framework',
    )
    args = parser.parse_args()

    if args.source == "all":
        sources = all_sources
    else:
        sources = [args.source]

    run(sources)


if __name__ == "__main__":
    main()
