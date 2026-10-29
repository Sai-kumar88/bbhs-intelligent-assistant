import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database.qdrant_client import get_qdrant_client, close_qdrant_client
from app.services.document_service import document_service
from app.routes import chat, documents


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure Qdrant connection and sync documents if folder has PDFs
    try:
        client = get_qdrant_client()
        sync_result = document_service.sync_documents()
        print(f"Startup document synchronization complete: {sync_result['total_documents']} documents tracked, {sync_result['chunks_indexed']} chunks newly indexed.")
        print("\n" + "=" * 65)
        print("🚀 BBHS AI ASSISTANT is LIVE! Click here to open in browser:")
        print("👉 http://127.0.0.1:8000/")
        print("👉 API Docs: http://127.0.0.1:8000/docs")
        print("=" * 65 + "\n")
    except Exception as e:
        print(f"Startup warning during document synchronization: {e}")
    yield
    # Clean shutdown
    close_qdrant_client()


app = FastAPI(
    title="BBHS AI ASSISTANT",
    description="Production-grade RAG Chatbot for Baldwin Boys' High School grounded in PDF knowledge base using NVIDIA AI endpoints and Qdrant.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static assets
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Mount routes under root and /api for compatibility
app.include_router(chat.router)
app.include_router(chat.router, prefix="/api")

app.include_router(documents.router)
app.include_router(documents.router, prefix="/api")


@app.get("/", include_in_schema=False)
def root():
    """Serve BBHS AI ASSISTANT frontend."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
def health_check():
    """Health check endpoint verifying system and Qdrant status."""
    try:
        client = get_qdrant_client()
        collections = [c.name for c in client.get_collections().collections]
        doc_status = document_service.get_status()
        return {
            "status": "healthy",
            "qdrant": "connected",
            "collection_exists": settings.QDRANT_COLLECTION_NAME in collections,
            "total_documents": doc_status.get("total_documents", 0),
            "environment": settings.ENVIRONMENT
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

