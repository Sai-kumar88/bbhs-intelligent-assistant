import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services.answer_service import answer_service

client = TestClient(app)


def test_refusal_for_unrelated_queries():
    """Verify unrelated questions return the fixed refusal message."""
    unrelated_queries = [
        "What is the capital of France?",
        "How do you bake a chocolate cake from scratch?",
        "Explain Einstein's theory of general relativity."
    ]

    for q in unrelated_queries:
        response = client.post("/api/chat", json={"query": q})
        assert response.status_code == 200
        data = response.json()
        assert data["refusal"] is True
        assert data["answer"] == settings.REFUSAL_MESSAGE
        assert data["sources"] == []


def test_refusal_service_direct():
    """Verify answer_service directly returns refusal message when no chunks match."""
    result = answer_service.generate_answer(
        query="Completely unrelated astronomical astrophysical query about distant supernova",
        score_threshold=0.99  # Guaranteed no match
    )
    assert result["refusal"] is True
    assert result["answer"] == settings.REFUSAL_MESSAGE
    assert result["sources"] == []
