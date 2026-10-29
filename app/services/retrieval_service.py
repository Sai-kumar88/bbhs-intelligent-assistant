from typing import List, Dict, Any, Optional
from app.config import settings
from app.database.qdrant_client import get_qdrant_client
from app.services.embedding_service import embedding_service

class RetrievedChunk:
    def __init__(self, text: str, source: str, page: int, score: float, chunk_index: int = 0):
        self.text = text
        self.source = source
        self.page = page
        self.score = score
        self.chunk_index = chunk_index

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "source": self.source,
            "page": self.page,
            "score": self.score,
            "chunk_index": self.chunk_index
        }

class RetrievalService:
    def __init__(self):
        self.top_k = settings.TOP_K
        self.score_threshold = settings.SIMILARITY_SCORE_THRESHOLD

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None
    ) -> List[RetrievedChunk]:
        """
        Embeds user query and searches Qdrant for matching document chunks.
        Filters out matches below the similarity score threshold.
        """
        k = top_k if top_k is not None else settings.TOP_K
        min_score = score_threshold if score_threshold is not None else settings.SIMILARITY_SCORE_THRESHOLD

        client = get_qdrant_client()
        collections = [c.name for c in client.get_collections().collections]
        if settings.QDRANT_COLLECTION_NAME not in collections:
            return []

        query_vector = embedding_service.embed_query(query)

        response = client.query_points(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            query=query_vector,
            limit=k,
            score_threshold=min_score
        )

        chunks: List[RetrievedChunk] = []
        for point in response.points:
            payload = point.payload or {}
            chunks.append(RetrievedChunk(
                text=payload.get("text", ""),
                source=payload.get("source", "unknown"),
                page=payload.get("page", 1),
                score=float(point.score),
                chunk_index=payload.get("chunk_index", 0)
            ))

        return chunks

    @staticmethod
    def format_context(chunks: List[RetrievedChunk]) -> str:
        """Format retrieved chunks into clean structured context for the prompt."""
        formatted_snippets = []
        for i, chunk in enumerate(chunks, 1):
            formatted_snippets.append(
                f"[Snippet {i} | Source: {chunk.source} | Page: {chunk.page}]\n{chunk.text.strip()}"
            )
        return "\n\n".join(formatted_snippets)


retrieval_service = RetrievalService()
