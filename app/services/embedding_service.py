import math
import hashlib
from typing import List, Optional
from app.config import settings

class EmbeddingService:
    def __init__(self):
        self._dimension = settings.EMBEDDING_DIMENSION
        self._client = None
        self._cached_key = None
        self._cached_model = None

    def _get_client(self):
        """Dynamically get or refresh NVIDIA embedding client if configuration changes."""
        provider = settings.EMBEDDING_PROVIDER.lower()
        if provider == "deterministic":
            return None

        if (
            self._client is None
            or self._cached_key != settings.NVIDIA_API_KEY
            or self._cached_model != settings.NVIDIA_EMBEDDING_MODEL
        ):
            if settings.NVIDIA_API_KEY and settings.NVIDIA_API_KEY.strip():
                try:
                    from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
                    self._client = NVIDIAEmbeddings(
                        model=settings.NVIDIA_EMBEDDING_MODEL,
                        api_key=settings.NVIDIA_API_KEY,
                        base_url=settings.NVIDIA_BASE_URL
                    )
                    self._cached_key = settings.NVIDIA_API_KEY
                    self._cached_model = settings.NVIDIA_EMBEDDING_MODEL
                except Exception:
                    self._client = None
            else:
                self._client = None
        return self._client

    def get_dimension(self) -> int:
        return self._dimension

    def _deterministic_embed(self, text: str) -> List[float]:
        """Generate a deterministic, normalized unit vector for offline/testing scenarios."""
        vec = [0.0] * self._dimension
        words = text.lower().split()
        if not words:
            vec[0] = 1.0
            return vec

        for word in words:
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dimension
            sign = 1.0 if ((h >> 4) & 1) == 0 else -1.0
            vec[idx] += sign

        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        else:
            vec[0] = 1.0
        return vec

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        client = self._get_client()
        if client is not None:
            try:
                return client.embed_documents(texts)
            except Exception:
                return [self._deterministic_embed(t) for t in texts]
        return [self._deterministic_embed(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        client = self._get_client()
        if client is not None:
            try:
                return client.embed_query(text)
            except Exception:
                return self._deterministic_embed(text)
        return self._deterministic_embed(text)

embedding_service = EmbeddingService()
