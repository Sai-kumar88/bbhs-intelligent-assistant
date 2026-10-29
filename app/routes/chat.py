from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from app.services.answer_service import answer_service

router = APIRouter(prefix="", tags=["Chat"])


class SourceItem(BaseModel):
    source: str = Field(..., description="Document filename")
    page: int = Field(..., description="Page number in document (1-indexed)")


class ChatRequest(BaseModel):
    query: Optional[str] = Field(None, description="Query to ask the knowledge base")
    question: Optional[str] = Field(None, description="Alternative alias for query")
    top_k: Optional[int] = Field(None, ge=1, le=20, description="Number of chunks to retrieve")
    score_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Similarity threshold")

    def get_text(self) -> str:
        text = self.query or self.question
        if not text or not text.strip():
            raise ValueError("Query or question must be provided and not empty.")
        return text.strip()


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceItem]
    refusal: bool


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    """
    Query the PDF knowledge base.
    Answers strictly from PDF content with citations, or returns a fixed refusal message.
    """
    try:
        query_text = request.get_text()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(e)
        )

    try:
        result = answer_service.generate_answer(
            query=query_text,
            top_k=request.top_k,
            score_threshold=request.score_threshold
        )
        return ChatResponse(
            answer=result["answer"],
            sources=[SourceItem(**s) for s in result["sources"]],
            refusal=result["refusal"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating chat answer: {str(e)}"
        )
