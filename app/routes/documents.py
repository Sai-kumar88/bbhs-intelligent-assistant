from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Header, HTTPException, status, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from app.config import settings
from app.services.document_service import document_service

router = APIRouter(prefix="/documents", tags=["Documents"])

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_reindex_auth(x_api_key: Optional[str] = Security(api_key_header)):
    if not settings.REINDEX_API_KEY:
        # If no key configured, reject by default for security
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reindexing API key is not configured on server."
        )
    if not x_api_key or x_api_key.strip() != settings.REINDEX_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header for document reindexing."
        )
    return True


class ReindexResponse(BaseModel):
    status: str
    new_files: List[str]
    modified_files: List[str]
    deleted_files: List[str]
    unchanged_files: List[str]
    chunks_indexed: int
    total_documents: int


@router.post("/reindex", response_model=ReindexResponse)
def reindex_documents(force: bool = False, authorized: bool = Security(verify_reindex_auth)):
    """
    Secure endpoint to re-scan documents folder and synchronize Qdrant.
    Requires header: X-API-Key: <REINDEX_API_KEY>
    Optional query parameter: ?force=true to force re-indexing of all documents.
    """
    try:
        result = document_service.sync_documents(force=force)
        return ReindexResponse(
            status=result["status"],
            new_files=result["new_files"],
            modified_files=result["modified_files"],
            deleted_files=result["deleted_files"],
            unchanged_files=result["unchanged_files"],
            chunks_indexed=result["chunks_indexed"],
            total_documents=result["total_documents"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reindexing failed: {str(e)}"
        )


@router.get("/status")
def get_documents_status():
    """Retrieve current synchronization status of the knowledge base documents."""
    try:
        return document_service.get_status()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve document status: {str(e)}"
        )
