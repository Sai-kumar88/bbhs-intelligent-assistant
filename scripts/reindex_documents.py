import sys
import os

# Add parent directory to path so app modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.document_service import document_service
from app.database.qdrant_client import close_qdrant_client


def main():
    print("=" * 60)
    print("Starting document synchronization with Qdrant vector database...")
    print("=" * 60)

    try:
        result = document_service.sync_documents()
        print(f"Status: {result['status']}")
        print(f"New files indexed:      {result['new_files']}")
        print(f"Modified files updated: {result['modified_files']}")
        print(f"Deleted files removed:  {result['deleted_files']}")
        print(f"Unchanged files:        {result['unchanged_files']}")
        print(f"New chunks indexed:     {result['chunks_indexed']}")
        print(f"Total documents active: {result['total_documents']}")
        print("=" * 60)
        print("Synchronization completed successfully.")
    except Exception as e:
        print(f"Error during synchronization: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        close_qdrant_client()


if __name__ == "__main__":
    main()
