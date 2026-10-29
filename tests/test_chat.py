import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify health endpoint reports healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["qdrant"] == "connected"


def test_chat_empty_query():
    """Verify empty or missing queries return 422 validation error."""
    response = client.post("/api/chat", json={})
    assert response.status_code == 422

    response = client.post("/api/chat", json={"query": "   "})
    assert response.status_code == 422


def test_chat_valid_query():
    """Verify chat endpoint returns answer and source structure."""
    # Ensure document is indexed
    client.post(
        "/api/documents/reindex",
        headers={"X-API-Key": settings.REINDEX_API_KEY}
    )

    response = client.post("/api/chat", json={"query": "When was Baldwin Boys' High School founded?"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert "refusal" in data
    assert isinstance(data["sources"], list)
    if not data["refusal"]:
        for s in data["sources"]:
            assert "source" in s
            assert "page" in s
            assert s["page"] >= 1
