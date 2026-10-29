import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Knowledge Base RAG Chatbot"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # NVIDIA AI Endpoints
    NVIDIA_API_KEY: str = ""
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_MODEL: str = "nvidia/nemotron-3.5-bolt-e4b"
    NVIDIA_EMBEDDING_MODEL: str = "nvidia/nemotron-3.5-embed-1b"

    # Embedding Settings
    EMBEDDING_PROVIDER: str = "nvidia"  # 'nvidia' or 'deterministic'
    EMBEDDING_DIMENSION: int = 2048

    # Qdrant Vector DB
    QDRANT_LOCATION: str = "local"  # 'local', 'memory', or 'remote'
    QDRANT_PATH: str = "./qdrant_storage"
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_NAME: str = "knowledge_base"

    # Document Processing
    DOCUMENTS_DIR: str = "./documents"
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 100

    # RAG Retrieval & Prompting
    TOP_K: int = 5
    SIMILARITY_SCORE_THRESHOLD: float = 0.10
    REFUSAL_MESSAGE: str = (
        "We’re happy to help you take the next step in your child’s educational journey at "
        "Baldwin Boys’ High School (BBHS)! 😊 "
        "For further information about your query, our school team will be delighted to guide you "
        "and help you find the information you’re looking for. "
        "📞 Call us: 080-49363866"
    )

    # Security
    REINDEX_API_KEY: str = "reindex-secret-key-change-me"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
