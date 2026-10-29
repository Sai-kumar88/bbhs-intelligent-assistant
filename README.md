# BBHS AI ASSISTANT 🎓

A high-performance, production-ready Retrieval-Augmented Generation (RAG) chatbot and web application for **Baldwin Boys' High School**, built with **FastAPI**, **LangChain**, **Qdrant Vector Database**, and **NVIDIA AI Endpoints** (`nvidia/nemotron-3.5-bolt-e4b`).

The chatbot strictly answers queries based on official PDF documents stored in the `documents/` folder. When questions fall outside the knowledge base or cannot be verified from the document context, it provides a standardized refusal message, completely preventing hallucinations and outside knowledge leaks.

---

## 🌟 Key Features

- **Built-in Web Interface**: Includes a responsive, modern frontend themed in Baldwin Boys' High School colors (Royal Navy Blue & Crimson Red) with a clean white background, accessible directly at `http://127.0.0.1:8000/`.
- **Natural Chatbot Experience**: Answers are formatted with Markdown support (lists, headings, bold text) in a clean, uncluttered conversational bubble.
- **Strict Knowledge Grounding**: Answers are generated strictly from verified facts extracted from school PDFs.
- **Automated Refusal Guardrails**: Immediately detects ungrounded queries or topics missing from the documents and returns a polite, authoritative refusal with school admissions contact details.
- **Dynamic PDF Synchronization**:
  - Automatically identifies **new**, **modified** (via SHA-256 hash comparison), and **deleted** PDFs.
  - Automatically removes orphan/stale vector chunks in Qdrant when documents are updated or deleted to prevent duplicate answers.
- **Ultra-Fast Generation with NVIDIA AI**:
  - **LLM**: `nvidia/nemotron-3.5-bolt-e4b` (fast, low-latency generation).
  - **Embedding Model**: `nvidia/nemotron-3.5-embed-1b` (2048-dimensional dense vector embeddings).
  - **Offline Fallback**: Includes deterministic fallback embeddings for fast, offline unit testing.
- **Enterprise Security & Reliability**:
  - Re-indexing endpoint (`POST /api/documents/reindex`) is secured with `X-API-Key` authentication.
  - Full automated test suite with 8 unit tests (`pytest`).
  - Comprehensive CORS, health checks, and Pydantic schema validation.

---

## 📁 Project Structure

```
knowledge-base-chatbot/
├── .env                       # Local environment variables & NVIDIA API keys
├── .env.example               # Template environment configuration
├── .gitignore                 # Git ignore rules (env, cache, storage, venv)
├── README.md                  # Complete project documentation
├── requirements.txt           # Python dependencies
├── run.py                     # Convenience launcher (starts server at 127.0.0.1:8000)
├── app/
│   ├── __init__.py
│   ├── config.py              # Pydantic BaseSettings & configuration loader
│   ├── main.py                # FastAPI app, static mounting, lifespan & health
│   ├── database/
│   │   ├── __init__.py
│   │   └── qdrant_client.py   # Qdrant client singleton (local / memory / remote)
│   ├── prompts/
│   │   ├── __init__.py
│   │   └── system_prompt.py   # Strict grounding prompt templates & guardrails
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── chat.py            # POST /api/chat endpoint
│   │   └── documents.py       # GET /api/documents/status & POST /api/documents/reindex
│   ├── services/
│   │   ├── __init__.py
│   │   ├── answer_service.py  # RAG answer generation & guardrails enforcement
│   │   ├── document_service.py# PDF text extraction, sliding chunking & auto-sync
│   │   ├── embedding_service.py# Dense embeddings (NVIDIA API / offline fallback)
│   │   └── retrieval_service.py# Qdrant vector search & similarity thresholding
│   └── static/
│       ├── app.js             # Frontend chat application logic
│       ├── index.html         # BBHS AI Assistant web page
│       └── style.css          # Modern white executive theme
├── documents/
│   └── knowledge_base.pdf     # Official school knowledge base PDF
├── scripts/
│   └── reindex_documents.py   # Standalone CLI document re-indexer script
└── tests/
    ├── __init__.py
    ├── conftest.py            # PyTest fixtures (in-memory Qdrant & deterministic embeddings)
    ├── test_chat.py           # Chat API endpoints & health check tests
    ├── test_documents.py      # Synchronization lifecycle & security tests
    └── test_refusal.py        # Guardrails & out-of-scope query tests
```

---

## 🚀 Setup & Installation

### 1. Prerequisites
- Python 3.10+
- NVIDIA API Key from [build.nvidia.com](https://build.nvidia.com) (for live LLM generation and embeddings)

### 2. Clone & Install Dependencies
```powershell
# Clone the repository
git clone <repository-url>
cd knowledge-base-chatbot

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

> **Note for Windows Users**: Ensure no Python server is running before executing `pip install`, as Windows locks binary `.pyd` files while in use.

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
copy .env.example .env
```

Edit `.env` with your settings:
```env
# NVIDIA AI Endpoints
NVIDIA_API_KEY=nvapi-your-key-here
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=nvidia/nemotron-3.5-bolt-e4b
NVIDIA_EMBEDDING_MODEL=nvidia/nemotron-3.5-embed-1b

# Embedding Provider: 'nvidia' (production) or 'deterministic' (offline tests)
EMBEDDING_PROVIDER=nvidia
EMBEDDING_DIMENSION=2048

# Qdrant Vector DB (Location: 'local', 'memory', or 'remote')
QDRANT_LOCATION=local
QDRANT_PATH=./qdrant_storage
QDRANT_COLLECTION_NAME=knowledge_base

# Document Processing
DOCUMENTS_DIR=./documents
CHUNK_SIZE=800
CHUNK_OVERLAP=100

# Retrieval & Guardrails
TOP_K=5
SIMILARITY_SCORE_THRESHOLD=0.10
REFUSAL_MESSAGE="We’re happy to help you take the next step in your child’s educational journey at Baldwin Boys’ High School (BBHS)! 😊 For further information about your query, our school team will be delighted to guide you and help you find the information you’re looking for. 📞 Call us: 080-49363866"

# Security Key for Reindexing
REINDEX_API_KEY=reindex-secret-key-change-me
```

---

## 💻 Running the Application

### Option A: Using the Convenience Script (Recommended)
```powershell
python run.py
```

### Option B: Using Uvicorn Directly
```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Once running, open your web browser:
- 🌐 **Web Chat Interface**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- 📖 **Interactive API Documentation (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 📡 API Reference

### 1. Chat Query
`POST /api/chat`

Query the school knowledge base.

**Request Body:**
```json
{
  "query": "explain about the school"
}
```

**Response (Grounded Answer):**
```json
{
  "answer": "Baldwin Boys' High School is a boys' school founded in 1880, located at #14 Hosur Road, Richmond Town, Bangalore. It is run by the Baldwin Methodist Educational Society...",
  "sources": [
    {
      "source": "knowledge_base.pdf",
      "page": 1
    },
    {
      "source": "knowledge_base.pdf",
      "page": 2
    }
  ],
  "refusal": false
}
```

**Response (Out-of-Scope Query):**
```json
{
  "answer": "We’re happy to help you take the next step in your child’s educational journey at Baldwin Boys’ High School (BBHS)! 😊 For further information about your query, our school team will be delighted to guide you and help you find the information you’re looking for. 📞 Call us: 080-49363866",
  "sources": [],
  "refusal": true
}
```

---

### 2. Document Status
`GET /api/documents/status`

Retrieve information about indexed PDF files, SHA-256 hashes, and chunk counts.

**Response:**
```json
{
  "total_documents": 1,
  "documents": {
    "knowledge_base.pdf": {
      "hash": "1d8dddf49f5974caa79cc1771ba237fbcd24833cc9cee69a5cbd19ea0b373ec7",
      "chunk_count": 56
    }
  }
}
```

---

### 3. Synchronize Documents
`POST /api/documents/reindex`

Re-scan the `documents/` folder, detect changes, and update Qdrant vectors. Requires the `X-API-Key` header.

**Headers:**
```
X-API-Key: reindex-secret-key-change-me
```

**Query Parameters (Optional):**
- `force=true`: Force re-indexing of all documents even if hashes match.

**Response:**
```json
{
  "status": "success",
  "new_files": [],
  "modified_files": [],
  "deleted_files": [],
  "unchanged_files": ["knowledge_base.pdf"],
  "chunks_indexed": 0,
  "total_documents": 1
}
```

---

### 4. Health Check
`GET /api/health`

Verifies that FastAPI is running and connected to the Qdrant vector database.

**Response:**
```json
{
  "status": "healthy",
  "qdrant": "connected",
  "collection_exists": true,
  "total_documents": 1,
  "environment": "development"
}
```

---

## 🧪 Running Automated Tests

The project includes unit and integration tests using `pytest`:

```powershell
pytest -v
```

All 8 tests run offline using in-memory vector storage and deterministic mock embeddings:
- `tests/test_chat.py`: Health checks, empty query validation, grounded RAG answers.
- `tests/test_documents.py`: Document synchronization lifecycle, modified/deleted file detection, `X-API-Key` authentication.
- `tests/test_refusal.py`: Strict guardrails enforcement for out-of-scope and ungrounded queries.

---

## 🔒 Security Best Practices

- `.env` is excluded in `.gitignore` to prevent API keys from leaking into version control.
- `REINDEX_API_KEY` prevents unauthorized re-indexing attacks.
- Inputs are strictly validated with Pydantic models.
- Document text is safely formatted to prevent prompt injection.

---

## 📄 License
Internal use for Baldwin Boys' High School AI Knowledge Base System.
