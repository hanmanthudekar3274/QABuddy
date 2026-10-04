"""High-level hybrid search: embed query → sparse encode → Qdrant hybrid query."""
import os
import pickle
from pathlib import Path

from loguru import logger

from ingestion.embedder import embed_query
from retrieval.qdrant_store import get_client, get_collection_name, hybrid_search
from retrieval.sparse import BM25SparseEncoder

_sparse_encoder: BM25SparseEncoder | None = None
ENCODER_PATH = Path("data/bm25_encoder.pkl")


def load_sparse_encoder() -> BM25SparseEncoder:
    global _sparse_encoder
    if _sparse_encoder is None:
        if ENCODER_PATH.exists():
            with open(ENCODER_PATH, "rb") as f:
                _sparse_encoder = pickle.load(f)
            logger.info("Loaded BM25 encoder from disk")
        else:
            logger.warning("BM25 encoder not found — sparse search disabled")
            _sparse_encoder = BM25SparseEncoder()
    return _sparse_encoder


def search(query: str, top_k: int | None = None) -> list[dict]:
    if top_k is None:
        top_k = int(os.environ.get("TOP_K", 8))

    dense_vec = embed_query(query).tolist()

    encoder = load_sparse_encoder()
    sparse_vec = encoder.encode(query)

    client = get_client()
    collection = get_collection_name()

    results = hybrid_search(
        client=client,
        collection=collection,
        dense_vector=dense_vec,
        sparse_vector=sparse_vec,
        top_k=top_k,
    )
    return results
