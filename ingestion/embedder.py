"""Batched embedding using BAAI/bge-large-en-v1.5 via sentence-transformers."""
import os

import numpy as np
from loguru import logger
from sentence_transformers import SentenceTransformer

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        # bge-base: 430 MB, 768-dim — good quality, runs on CPU
        # bge-large: 1.3 GB, 1024-dim — better quality, needs more RAM
        model_name = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
        device = os.environ.get("EMBEDDING_DEVICE", "cpu")
        logger.info(f"Loading embedding model {model_name} on {device} (downloads from HuggingFace on first run)")
        _model = SentenceTransformer(model_name, device=device)
    return _model


def embed_texts(texts: list[str], batch_size: int = 32) -> np.ndarray:
    """Return (N, dim) float32 array. bge-large requires query prefix for retrieval."""
    model = _get_model()
    # bge models perform better with instruction prefix during indexing
    prefixed = [f"Represent this document for retrieval: {t}" for t in texts]
    vectors = model.encode(
        prefixed,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,  # cosine similarity
    )
    return vectors.astype(np.float32)


def embed_query(query: str) -> np.ndarray:
    """Embed a single query string with query-specific prefix."""
    model = _get_model()
    vec = model.encode(
        [f"Represent this query for searching relevant documents: {query}"],
        normalize_embeddings=True,
    )
    return vec[0].astype(np.float32)
