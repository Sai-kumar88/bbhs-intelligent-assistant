import os
import pymupdf
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services.document_service import DocumentService, compute_file_hash
from app.database.qdrant_client import get_qdrant_client

client = TestClient(app)


def create_dummy_pdf(path: str, title: str, pages_content: list):
    doc = pymupdf.open()
    for text in pages_content:
        page = doc.new_page()
        page.insert_text((50, 72), f"{title}\n{text}")
    doc.save(path)
    doc.close()


def test_reindex_auth_failure():
    """Verify reindex endpoint rejects unauthorized requests."""
    response = client.post("/api/documents/reindex")
    assert response.status_code == 401

    response = client.post("/api/documents/reindex", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401


def test_reindex_auth_success():
    """Verify reindex endpoint accepts valid X-API-Key."""
    response = client.post(
        "/api/documents/reindex",
        headers={"X-API-Key": settings.REINDEX_API_KEY}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "new_files" in data
    assert "total_documents" in data


def test_document_sync_lifecycle(tmp_path):
    """
    Test document service automatically detects:
    1. New PDFs
    2. Unchanged PDFs
    3. Modified PDFs
    4. Deleted PDFs
    """
    doc_dir = tmp_path / "test_docs"
    doc_dir.mkdir()
    manifest_file = tmp_path / "manifest.json"

    doc_service = DocumentService(manifest_path=str(manifest_file))
    doc_service.documents_dir = str(doc_dir)

    # 1. Add new PDF
    pdf_path = os.path.join(doc_dir, "test_doc_1.pdf")
    create_dummy_pdf(pdf_path, "Test Document 1", ["Page 1 content about science.", "Page 2 content about math."])

    res1 = doc_service.sync_documents()
    assert "test_doc_1.pdf" in res1["new_files"]
    assert res1["chunks_indexed"] > 0
    assert res1["total_documents"] == 1

    # 2. Sync again without changes - should be unchanged
    res2 = doc_service.sync_documents()
    assert "test_doc_1.pdf" in res2["unchanged_files"]
    assert len(res2["new_files"]) == 0
    assert len(res2["modified_files"]) == 0

    # 3. Modify PDF - should detect modification
    create_dummy_pdf(pdf_path, "Updated Document 1", ["Page 1 updated content.", "Page 2 new math syllabus."])
    res3 = doc_service.sync_documents()
    assert "test_doc_1.pdf" in res3["modified_files"]
    assert len(res3["new_files"]) == 0

    # 4. Delete PDF - should detect deletion and purge
    os.remove(pdf_path)
    res4 = doc_service.sync_documents()
    assert "test_doc_1.pdf" in res4["deleted_files"]
    assert res4["total_documents"] == 0
