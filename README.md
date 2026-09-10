# PolicyPilot

PolicyPilot is an enterprise-grade **Retrieval-Augmented Generation (RAG) application** designed to provide fast, accurate, and grounded answers to internal organizational policy and documentation questions.

The application combines a high-performance Python FastAPI backend with a modern Next.js/React streaming chat interface. It features end-to-end document ingestion, token-bounded chunking, vector similarity retrieval, cross-scoring re-ranking, hallucination guardrails, inline citation mapping, in-memory query caching, structured JSON logging, real-time SSE streaming, and token/cost usage monitoring.

---

## Features

- 📄 **Document Ingestion & Parsing:** Supports parsing and cleaning Markdown, PDF, HTML, and plain text policy documents.
- ✂️ **Text Chunking:** Splits documents into token-bounded text chunks with configurable overlap for context preservation.
- 🧠 **Embeddings & Vector Storage:** Integrates OpenAI vector embeddings with persistent ChromaDB vector collections.
- 🔍 **Vector Similarity Search & Metadata Filtering:** Hybrid retrieval supporting cosine vector similarity and metadata filtering.
- 🎯 **Chunk Re-Ranking:** Two-stage retrieval pipeline with cross-scoring candidate re-ranking for maximum top-1 accuracy.
- 🛡️ **Hallucination Guardrails & Refusal Handling:** Pre-generation threshold checks that safely refuse unanswered or low-confidence queries.
- 🤖 **Grounded RAG Pipeline:** Generates factual answers strictly grounded in retrieved evidence chunks.
- 📚 **Source Citations:** Automatic inline citation mapping (`[1]`, `[2]`) linking claims directly to source documents and excerpts.
- 💬 **Interactive Chat UI:** Next.js React frontend interface featuring responsive dark mode, collapsible source details, retry options, and incomplete badges.
- ⚡ **Real-Time Streaming Responses:** Server-Sent Events (SSE) streaming endpoint (`POST /query/stream`) emitting real-time tokens and citations.
- ⚡ **Query Cache:** In-memory query caching service using SHA-256 key hashing with 15-minute TTL and hit/miss tracking.
- 📊 **Structured Logging:** Observability service emitting JSON-formatted logs with UUID `request_id` tracking and secret redaction.
- 💰 **Usage & Cost Monitoring:** Real-time token counting via `tiktoken`, latency measurement, cost estimation, and usage summary aggregation.

---

## Project Structure

```text
SW2627_PolicyPilot_Kalvium-Community/
├── data/                      # Knowledge base document corpus
├── outputs/                   # Output reports and evaluation traces
├── prompts/                   # System prompt templates
├── src/                       # Backend Python application source code
│   ├── api.py                 # FastAPI backend server (HTTP & SSE endpoints)
│   ├── main.py                # Command-line entry point
│   └── services/              # Modular backend services
│       ├── batch_embedding_service.py    # Batch vector embedding processor
│       ├── cache_service.py              # In-memory query cache with TTL & SHA-256 hashing
│       ├── chunking_service.py           # Text chunking and splitting engine
│       ├── citation_service.py           # Citation mapping & SSE stream generator
│       ├── cleaning_service.py           # Document text cleaning and normalization
│       ├── document_service.py           # Multi-format document loader
│       ├── embedding_service.py          # Embedding vector generation client
│       ├── history_service.py            # Conversation history manager
│       ├── observability_service.py      # Structured JSON logging & request tracking
│       ├── parameter_service.py          # RAG pipeline hyperparameter manager
│       ├── prompt_service.py             # Prompt template & context builder
│       ├── rag_pipeline_service.py       # End-to-end RAG query orchestrator
│       ├── reranking_service.py          # Candidate chunk re-ranking engine
│       ├── response_service.py           # LLM answer generator & guardrail engine
│       ├── retrieval_service.py          # Vector search & hybrid retrieval service
│       ├── similarity_service.py         # Vector distance & ranking calculations
│       ├── token_service.py              # Token counter & cost calculator
│       ├── usage_monitoring_service.py   # Usage monitoring & aggregator
│       └── vector_store_service.py       # ChromaDB vector store manager
├── frontend/                  # Next.js React Frontend Web UI
│   ├── src/
│   │   ├── app/               # Next.js App Router (layout.js, page.js, globals.css)
│   │   ├── components/        # React components (ChatInterface.jsx)
│   │   └── lib/               # Frontend API utilities (api.js)
│   ├── tests/                 # Frontend unit & integration tests
│   ├── package.json           # Frontend Node package configuration
│   └── .env.example           # Frontend environment variable template
├── tests/                     # Backend Pytest test suite (120 test cases)
├── .env.example               # Backend environment variable template
├── .gitignore                 # Secret files & dependency exclusion rules
├── pytest.ini                 # Pytest test runner configuration
├── README.md                  # Comprehensive project documentation
└── requirements.txt           # Python dependency specification
```

---

## Prerequisites

- **Python:** Version 3.10 or higher (tested on Python 3.13)
- **Node.js:** Version 18.0 or higher & `npm`
- **Git:** Version 2.x

---

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd SW2627_PolicyPilot_Kalvium-Community
```

### 2. Backend Setup (Python)

Create and activate a Python virtual environment:

**Windows PowerShell:**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install backend dependencies:
```bash
pip install -r requirements.txt
```

### 3. Frontend Setup (Node.js / Next.js)

Navigate to the frontend directory and install dependencies:
```bash
cd frontend
npm install
cd ..
```

---

## Environment Variables

PolicyPilot uses environment variables for secure runtime configuration.

### Root Backend Environment Variables (`.env`)

Copy `.env.example` to create your local `.env` file:

```bash
# Windows PowerShell
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```

Environment variable specifications (`.env.example`):

```env
API_BASE_URL=https://api.openai.com/v1
API_KEY=your_openai_api_key_here
CHAT_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
CHROMA_PERSIST_DIR=./data/chroma_db
PORT=8000
```

- `API_BASE_URL`: Base URL for OpenAI or OpenAI-compatible model API.
- `API_KEY`: API key credential for model calls.
- `CHAT_MODEL`: Language model name used for RAG generation (`gpt-4o-mini`).
- `EMBEDDING_MODEL`: Embedding model name (`text-embedding-3-small`).
- `CHROMA_PERSIST_DIR`: Local disk directory for persistent ChromaDB storage.
- `PORT`: HTTP port for FastAPI backend server (default: `8000`).

### Frontend Environment Variables (`frontend/.env`)

Copy `frontend/.env.example` to `frontend/.env.local`:

```env
NEXT_PUBLIC_RAG_API_URL=http://localhost:8000/query
```

> **Security Note:** Secrets, real API keys, and credentials must **never** be committed to Git. The `.gitignore` file enforces that `.env`, `.env.local`, `.env.*`, and `*.pem` are ignored.

---

## Running the Backend

Start the FastAPI application server:

```bash
# Activate virtual environment if not already active
.venv\Scripts\activate

# Run backend server
python src/api.py
```

The backend server starts on **`http://localhost:8000`**. You can verify health status at `http://localhost:8000/health`.

---

## Running the Frontend

Start the Next.js development server:

```bash
cd frontend
npm run dev
```

The Web UI opens at **`http://localhost:3000`**.

---

## API Usage

PolicyPilot exposes the following HTTP endpoints:

### 1. `GET /health`
Returns backend health status.

**Response:**
```json
{
  "status": "ok"
}
```

### 2. `POST /query`
Standard RAG endpoint returning complete grounded response with citations and metadata.

**Request:**
```json
{
  "question": "What is the refund window?"
}
```

**Response:**
```json
{
  "question": "What is the refund window?",
  "answer": "Customers can request a refund within 14 days of purchase. [1]",
  "citations": [
    {
      "id": "refund-policy.md",
      "citation_num": 1,
      "text": "Customers can request a refund within 14 days of purchase.",
      "score": 0.89
    }
  ],
  "sources": [
    {
      "id": "refund-policy.md",
      "citation_num": 1,
      "text": "Customers can request a refund within 14 days of purchase.",
      "score": 0.89
    }
  ],
  "usage": {
    "prompt_tokens": 185,
    "completion_tokens": 18,
    "total_tokens": 203,
    "estimated_cost_usd": 0.000035,
    "latency_ms": 340,
    "cached": false
  }
}
```

### 3. `POST /query/stream`
Server-Sent Events (SSE) streaming endpoint emitting real-time JSON events (`Content-Type: text/event-stream`).

**Request:**
```json
{
  "question": "What is the refund window?"
}
```

**Stream Events:**
```text
data: {"type": "token", "text": "Customers "}

data: {"type": "token", "text": "can request a refund..."}

data: {"type": "citations", "sources": [{"id": "refund-policy.md", "citation_num": 1}]}

data: {"type": "done"}
```

---

## End-to-End Demo

Below is a demonstration of the full RAG pipeline execution:

1. **Document Upload & Ingestion:**
   Document `refund-policy.md` containing customer return guidelines is uploaded to the knowledge base.
2. **Text Ingestion & Chunking:**
   The document is parsed, cleaned, and split into 500-token chunks with 50-token overlap.
3. **Embedding & Vector Storage:**
   Vector embeddings are generated via `text-embedding-3-small` and stored in ChromaDB.
4. **User Query:**
   The user submits: *"What is the refund window?"*
5. **Retrieval & Re-ranking:**
   ChromaDB vector similarity search retrieves candidate chunks; the re-ranking service ranks `refund-policy.md` at Rank 1.
6. **RAG Answer Generation:**
   The LLM generates a grounded response enforced by context guardrails.
7. **Citations Display:**
   Source markers (`[1]`) map directly to `refund-policy.md`.

**Sample Demo Execution:**

- **Uploaded Document:** `refund-policy.md`
- **Question:** *"What is the refund window?"*
- **Answer:** *"Customers can request a refund within 14 days of purchase. [1]"*
- **Sources:** `[1] refund-policy.md, chunk #0 (Score: 89.0%)`

*(Note: Demonstration example illustrating full system workflow).*

---

## Caching, Logging & Usage Monitoring

### 1. In-Memory Query Cache (`cache_service.py`)
- **Normalized Keys:** Trims and lowercases questions; creates SHA-256 deterministic hash including active filters.
- **TTL Expiration:** Default 15-minute Time-to-Live (TTL).
- **Hit/Miss Metrics:** Tracks total queries, cache hits, cache misses, and hit ratio.

### 2. Structured JSON Logging (`observability_service.py`)
- **JSON Format:** Logs events in structured JSON containing `timestamp`, `level`, `event`, `request_id`, `latency_ms`, and `tokens`.
- **Request Tracing:** Generates a unique UUID `request_id` per query.
- **Secret Filtering:** Automatically redacts API keys, tokens, and passwords from logs.

### 3. Token & Cost Usage Monitoring (`token_service.py`, `usage_monitoring_service.py`)
- **Token Counting:** Uses `tiktoken` (`cl100k_base`) to calculate prompt and completion tokens.
- **Cost Estimation:** Calculates estimated USD cost based on model pricing tiers.
- **Usage Aggregator:** Aggregates cumulative tokens, total cost, average latency, and cache hit metrics.

---

## End-to-End Architecture & Documentation

```
[Document Upload] ──> [ingestion] ──> [cleaning_service] ──> [chunking_service]
                                                                  │
[User Query] ◄────────────────────────────────────────────────────┼─► [embedding_service]
     │                                                            │           │
     ▼                                                            ▼           ▼
[Web Chat UI] ◄── [SSE Streaming] ◄── [citation_service] ◄── [vector_store_service]
     ▲                                       ▲                    │
     │                                       │                    ▼
 [POST /query] ──> [cache_service] ──> [response_service] ◄── [retrieval_service]
                                             │
                                             ▼
                                  [observability_service]
```

1. **Upload & Ingestion:** Documents (`PDF`, `MD`, `TXT`, `HTML`) are ingested via `document_service.py`.
2. **Chunking & Embeddings:** Chunks are vectorized using `embedding_service.py` and saved to `vector_store_service.py`.
3. **Hybrid Retrieval:** `retrieval_service.py` searches ChromaDB using cosine similarity and metadata filters.
4. **Re-Ranking & Guardrails:** `reranking_service.py` re-scores candidate chunks; `response_service.py` enforces relevance thresholds (`min_score=0.35`).
5. **Generation & Citations:** `response_service.py` generates grounded answers; `citation_service.py` attaches source metadata.
6. **Streaming & Web UI:** Responses stream to Next.js `ChatInterface.jsx` via SSE `POST /query/stream`.

---

## Testing

Both backend and frontend test suites are fully automated and verified.

### 1. Running Backend Tests (Pytest)

```bash
# Execute from project root
.venv\Scripts\python.exe -m pytest
```

- **Backend Test Status:** ✅ **120 / 120 tests passed** (0 failures, 7.63s execution time).
- Tests cover API routes, query cache TTL, streaming SSE chunks, retrieval re-ranking, token counting, hallucination guardrails, and vector store operations.

### 2. Running Frontend Tests (Node test runner)

```bash
cd frontend
npm test
```

- **Frontend Test Status:** ✅ **8 / 8 tests passed** (0 failures, 237ms execution time).
- Tests cover `askQuestion`, `getStreamUrl`, error handling, and `streamQuestion` SSE token/citation parsing.

---

## Troubleshooting

- **Backend Server Port Collision (`PORT 8000`):**
  If port 8000 is occupied, set `PORT=8005` in `.env` or run `python src/api.py` after freeing port 8000.
- **Module Import Error (`ModuleNotFoundError: No module named 'src'`):**
  Ensure you execute pytest using `.venv\Scripts\python.exe -m pytest` from the workspace root folder.
- **Missing API Key Error:**
  Verify that `.env` contains a valid `API_KEY` setting.
- **Frontend Connection Error:**
  Ensure the backend is running at `http://localhost:8000` and `NEXT_PUBLIC_RAG_API_URL` in `frontend/.env.example` points to `http://localhost:8000/query`.

---

## Final Delivery Information

The final sprint delivery for this assignment is represented by the Git tag:

`sprint-2-rag-final`
