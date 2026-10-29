import pytest
from app.config import settings
import app.database.qdrant_client as qc_mod


@pytest.fixture(autouse=True)
def configure_test_qdrant(monkeypatch):
    """Ensure tests run in isolated in-memory Qdrant instance so they do not collide with running server."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "test")
    monkeypatch.setattr(settings, "QDRANT_LOCATION", "memory")
    monkeypatch.setattr(settings, "QDRANT_COLLECTION_NAME", "test_knowledge_base")
    # Reset singleton client to memory instance
    qc_mod._qdrant_client = None
    yield
    qc_mod.close_qdrant_client()
