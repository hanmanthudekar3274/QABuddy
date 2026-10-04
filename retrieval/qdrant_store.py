"""Qdrant vector store: collection management, upsert, hybrid search."""
import os
import uuid
from typing import Any

from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "sparse"
VECTOR_DIM = 1024  # bge-large-en-v1.5 (use 768 for bge-base)

_client: QdrantClient | None = None


def get_client() -> QdrantClient:
    global _client
    if _client is not None:
        return _client

    mode = os.environ.get("QDRANT_MODE", "local").lower()
    if mode == "local":
        # Embedded mode — no server, no Docker, persists to disk
        path = os.environ.get("QDRANT_LOCAL_PATH", "./data/qdrant_db")
        _client = QdrantClient(path=path)
    else:
        host = os.environ.get("QDRANT_HOST", "localhost")
        port = int(os.environ.get("QDRANT_PORT", 6333))
        _client = QdrantClient(host=host, port=port)
    return _client


def get_collection_name() -> str:
    return os.environ.get("QDRANT_COLLECTION", "qabuddy")


def ensure_collection(client: QdrantClient, collection: str) -> None:
    existing = [c.name for c in client.get_collections().collections]
    if collection in existing:
        return

    logger.info(f"Creating Qdrant collection: {collection}")
    client.create_collection(
        collection_name=collection,
        vectors_config={
            DENSE_VECTOR_NAME: qm.VectorParams(
                size=VECTOR_DIM,
                distance=qm.Distance.COSINE,
                on_disk=True,
            )
        },
        sparse_vectors_config={
            SPARSE_VECTOR_NAME: qm.SparseVectorParams(
                index=qm.SparseIndexParams(on_disk=True)
            )
        },
        optimizers_config=qm.OptimizersConfigDiff(
            indexing_threshold=10000,
        ),
    )


def upsert_chunks(
    client: QdrantClient,
    collection: str,
    chunks: list[dict],
    dense_vectors: list[list[float]],
    sparse_vectors: list[dict],  # list of {"indices": [...], "values": [...]}
) -> None:
    points = []
    for chunk, dense, sparse in zip(chunks, dense_vectors, sparse_vectors):
        point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, chunk["text"][:200]))
        points.append(
            qm.PointStruct(
                id=point_id,
                vector={
                    DENSE_VECTOR_NAME: dense,
                    SPARSE_VECTOR_NAME: qm.SparseVector(
                        indices=sparse["indices"],
                        values=sparse["values"],
                    ),
                },
                payload={"text": chunk["text"], **chunk["metadata"]},
            )
        )

    batch_size = 100
    for i in range(0, len(points), batch_size):
        client.upsert(collection_name=collection, points=points[i : i + batch_size])
    logger.info(f"Upserted {len(points)} chunks into {collection}")


def hybrid_search(
    client: QdrantClient,
    collection: str,
    dense_vector: list[float],
    sparse_vector: dict,
    top_k: int = 8,
    filter_condition: Any = None,
) -> list[dict]:
    """Run Qdrant hybrid query (dense + sparse) with RRF fusion."""
    prefetch = [
        qm.Prefetch(
            query=dense_vector,
            using=DENSE_VECTOR_NAME,
            limit=top_k * 3,
        ),
        qm.Prefetch(
            query=qm.SparseVector(
                indices=sparse_vector["indices"],
                values=sparse_vector["values"],
            ),
            using=SPARSE_VECTOR_NAME,
            limit=top_k * 3,
        ),
    ]

    results = client.query_points(
        collection_name=collection,
        prefetch=prefetch,
        query=qm.FusionQuery(fusion=qm.Fusion.RRF),
        limit=top_k,
        query_filter=filter_condition,
        with_payload=True,
    )

    return [
        {"score": r.score, **r.payload}
        for r in results.points
    ]
