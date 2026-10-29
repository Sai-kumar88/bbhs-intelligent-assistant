import os
import json
import uuid
import hashlib
from typing import Dict, List, Any, Tuple, Optional
import pymupdf
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest_models
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import settings
from app.database.qdrant_client import get_qdrant_client, init_collection, delete_points_by_source
from app.services.embedding_service import embedding_service


def compute_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of a file to detect content modifications."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class DocumentService:
    def __init__(self, manifest_path: Optional[str] = None):
        self.documents_dir = settings.DOCUMENTS_DIR
        self.manifest_path = manifest_path or os.path.join(
            settings.QDRANT_PATH if settings.QDRANT_LOCATION == "local" else ".",
            "document_manifest.json"
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def _load_manifest(self) -> Dict[str, Any]:
        """Load document synchronization manifest from disk."""
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_manifest(self, manifest: Dict[str, Any]):
        """Save updated synchronization manifest to disk."""
        os.makedirs(os.path.dirname(os.path.abspath(self.manifest_path)), exist_ok=True)
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

    def extract_pdf_chunks(self, file_path: str, filename: str, doc_hash: str) -> List[Dict[str, Any]]:
        """Extract text page-by-page from a PDF with cross-page context to preserve tables and continuous sections."""
        chunks = []
        doc = pymupdf.open(file_path)
        prev_tail = ""
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_text = page.get_text()
            page_num = page_idx + 1  # 1-indexed

            if not page_text or not page_text.strip():
                continue

            # Carry over up to 250 characters of trailing context from previous page so cross-page tables and sentences retain headers
            if prev_tail:
                full_text = f"[Continued context from Page {page_num - 1}: {prev_tail}]\n{page_text}"
            else:
                full_text = page_text

            prev_tail = page_text[-250:].replace("\n", " ").strip()

            split_texts = self.text_splitter.split_text(full_text)
            for split_idx, split_text in enumerate(split_texts):
                chunks.append({
                    "text": split_text,
                    "metadata": {
                        "source": filename,
                        "page": page_num,
                        "chunk_index": split_idx,
                        "doc_hash": doc_hash
                    }
                })
        doc.close()
        return chunks

    def sync_documents(self, force: bool = False) -> Dict[str, Any]:
        """
        Synchronize Qdrant vector database with PDFs in the documents folder.
        Detects new, modified, and deleted PDFs and updates Qdrant without duplicate or stale chunks.
        """
        client = get_qdrant_client()
        init_collection(client, vector_size=embedding_service.get_dimension())

        manifest = self._load_manifest()
        os.makedirs(self.documents_dir, exist_ok=True)

        current_files = {}
        for entry in os.listdir(self.documents_dir):
            if entry.lower().endswith(".pdf"):
                full_path = os.path.join(self.documents_dir, entry)
                if os.path.isfile(full_path):
                    current_files[entry] = {
                        "path": full_path,
                        "hash": compute_file_hash(full_path)
                    }

        new_files = []
        modified_files = []
        deleted_files = []
        unchanged_files = []

        # 1. Identify deleted files
        for filename in list(manifest.keys()):
            if filename not in current_files:
                deleted_files.append(filename)
                delete_points_by_source(client, filename)
                del manifest[filename]

        # 2. Identify new and modified files
        for filename, info in current_files.items():
            file_hash = info["hash"]
            if force:
                modified_files.append(filename)
                delete_points_by_source(client, filename)
            elif filename not in manifest:
                new_files.append(filename)
            elif manifest[filename].get("hash") != file_hash:
                modified_files.append(filename)
                delete_points_by_source(client, filename)
            else:
                unchanged_files.append(filename)

        files_to_index = new_files + modified_files
        total_chunks_indexed = 0

        for filename in files_to_index:
            file_path = current_files[filename]["path"]
            file_hash = current_files[filename]["hash"]

            chunks = self.extract_pdf_chunks(file_path, filename, file_hash)
            if not chunks:
                manifest[filename] = {
                    "hash": file_hash,
                    "chunk_count": 0
                }
                continue

            texts = [c["text"] for c in chunks]
            vectors = embedding_service.embed_documents(texts)

            points = []
            for i, chunk in enumerate(chunks):
                point_id = str(uuid.uuid5(
                    uuid.NAMESPACE_DNS,
                    f"{filename}_{chunk['metadata']['page']}_{chunk['metadata']['chunk_index']}_{i}"
                ))
                points.append(rest_models.PointStruct(
                    id=point_id,
                    vector=vectors[i],
                    payload={
                        "text": chunk["text"],
                        "source": chunk["metadata"]["source"],
                        "page": chunk["metadata"]["page"],
                        "chunk_index": chunk["metadata"]["chunk_index"],
                        "doc_hash": chunk["metadata"]["doc_hash"]
                    }
                ))

            # Upsert in batches of 100
            batch_size = 100
            for b_idx in range(0, len(points), batch_size):
                client.upsert(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    points=points[b_idx:b_idx + batch_size]
                )

            total_chunks_indexed += len(points)
            manifest[filename] = {
                "hash": file_hash,
                "chunk_count": len(points)
            }

        self._save_manifest(manifest)

        return {
            "status": "success",
            "new_files": new_files,
            "modified_files": modified_files,
            "deleted_files": deleted_files,
            "unchanged_files": unchanged_files,
            "chunks_indexed": total_chunks_indexed,
            "total_documents": len(manifest),
            "manifest": manifest
        }

    def get_status(self) -> Dict[str, Any]:
        """Get the current document index status."""
        manifest = self._load_manifest()
        return {
            "total_documents": len(manifest),
            "documents": manifest
        }


document_service = DocumentService()
