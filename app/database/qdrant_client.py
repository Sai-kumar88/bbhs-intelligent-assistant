import os
from typing import Optional, List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest_models
from app.config import settings

_qdrant_client: Optional[QdrantClient] = None


def get_qdrant_client() -> QdrantClient:
    """Singleton getter for Qdrant client based on configuration."""
    global _qdrant_client
    if _qdrant_client is not None:
        return _qdrant_client

    if settings.QDRANT_LOCATION == "memory":
        _qdrant_client = QdrantClient(location=":memory:")
    elif settings.QDRANT_LOCATION == "remote" and settings.QDRANT_URL:
        _qdrant_client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY
        )
    else:
        # Default local persistent disk storage
        os.makedirs(settings.QDRANT_PATH, exist_ok=True)
        _qdrant_client = QdrantClient(path=settings.QDRANT_PATH)

    return _qdrant_client


def init_collection(client: QdrantClient, vector_size: int, collection_name: Optional[str] = None):
    """Ensure the target collection exists with the appropriate vector dimension."""
    col_name = collection_name or settings.QDRANT_COLLECTION_NAME
    collections = client.get_collections().collections
    existing = [c.name for c in collections]

    if col_name not in existing:
        client.create_collection(
            collection_name=col_name,
            vectors_config=rest_models.VectorParams(
                size=vector_size,
                distance=rest_models.Distance.COSINE
            )
        )


def delete_points_by_source(client: QdrantClient, source_filename: str, collection_name: Optional[str] = None):
    """Delete all chunks belonging to a specific source file to prevent stale data."""
    col_name = collection_name or settings.QDRANT_COLLECTION_NAME
    client.delete(
        collection_name=col_name,
        points_selector=rest_models.FilterSelector(
            filter=rest_models.Filter(
                must=[
                    rest_models.FieldCondition(
                        key="source",
                        match=rest_models.MatchValue(value=source_filename)
                    )
                ]
            )
        )
    )


def close_qdrant_client():
    """Explicitly close Qdrant client connection."""
    global _qdrant_client
    if _qdrant_client is not None:
        try:
            _qdrant_client.close()
        except Exception:
            pass
        _qdrant_client = None

