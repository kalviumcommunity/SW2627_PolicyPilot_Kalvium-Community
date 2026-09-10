# API-Based Embeddings Generation and Storage Report

This report documents the implementation and verification of PolicyPilot's OpenAI-compatible embeddings generation and metadata-attached storage system.

## 1. Summary of Completed Tasks

| Task | Description | Status | Verification Detail |
| --- | --- | --- | --- |
| **Task 1** | Generate embeddings through API | Complete | Generated dense vectors with expected dimension (1536) |
| **Task 2** | Store vectors with source chunks & metadata | Complete | Attached text, source, chunk_index, token count |
| **Task 3** | Environment-based configuration | Complete | Read `OPENAI_API_KEY`, `EMBEDDING_MODEL`, `OPENAI_BASE_URL` |
| **Task 4** | Verification output | Complete | Model: `text-embedding-3-small`, Dim: 1536, Sample values printed |
| **Task 5** | Commit with sample corpus output | Complete | Exported to `outputs/embedding_records.json` |

## 2. Verification Output

```text
model: text-embedding-3-small
records: 4
vector length: 1536
sample values: [-0.035598, -0.035597, -0.029324, -0.034729, -0.022697]
```

## 3. Stored Records Sample Table

| Source | Chunk Index | Text Preview | Vector Dimension | Sample Vector Values (First 5) |
| --- | --- | --- | --- | --- |
| `account-guide.md` | 0 | Password reset instructions for learner accou... | 1536 | `[-0.0356, -0.0356, -0.0293, -0.0347, -0.0227]` |
| `account-guide.md` | 1 | Learners can recover access using their regis... | 1536 | `[-0.0236, 0.0138, 0.0342, -0.0354, -0.0356]` |
| `work_hours.md` | 0 | Standard Working Hours: The core team operate... | 1536 | `[-0.0266, 0.0119, -0.0349, -0.0151, 0.0359]` |
| `sample_policy.pdf` | 0 | Travel Reimbursements: Employees traveling on... | 1536 | `[0.0186, -0.0343, 0.0098, 0.0199, -0.0125]` |
| `remote_policy.txt` | 0 | Company Remote Work Policy Effective: January... | 1536 | `[-0.0273, 0.0216, 0.0363, 0.0221, -0.0359]` |
| `remote_policy.txt` | 1 | Employees must maintain standard core collab... | 1536 | `[-0.0352, 0.0131, -0.0165, -0.0163, -0.0278]` |

## 4. Key Concepts & Architecture Discussion

### A. What an Embedding Is and What Vector Dimension Represents
- **Embedding Definition:** An embedding is a dense mathematical vector of floating-point numbers that captures the semantic meaning, context, and nuance of a piece of text.
- **Dimensionality:** In `text-embedding-3-small`, each vector has **1536 dimensions**. Each dimension represents a latent semantic feature in a continuous multi-dimensional concept space.
- Texts with similar conceptual meanings point in similar directions in this 1536-dimensional space, yielding high cosine similarity.

### B. Why the Same Model Must Be Used for Documents and Queries
- Embedding models construct unique, non-interchangeable vector spaces.
- If document chunks are embedded with `text-embedding-3-small` (1536 dims) and a query is embedded with a different model (or even a different version):
  - The axes, weights, and latent concepts are misaligned.
  - Comparing them is like plotting coordinates on two completely different maps.
  - Cosine similarity scores lose all semantic meaning, resulting in retrieval failure.

### C. How Chunks Become Vectors and Stay Attached to Metadata
1. **Chunk Ingestion:** Chunks are extracted with `DocumentService` & `ChunkingService` with preserved boundaries.
2. **Batch API Call:** Texts are extracted into a batch array `[chunk['text'] for chunk in chunks]` and sent to `client.embeddings.create()`.
3. **Record Packaging:** The returned vectors are zipped with their origin chunks into composite records:
   ```json
   {
     "text": "Original chunk text for LLM generation context",
     "metadata": {
       "source": "account-guide.md",
       "chunk_index": 0,
       "token_count": 8
     },
     "embedding": [0.0312, -0.0451, ...],
     "embedding_dim": 1536,
     "model": "text-embedding-3-small"
   }
   ```
4. **Retrieval Ready:** Vector search finds the closest embedding vector, and the application immediately accesses `record['text']` and `record['metadata']` to provide grounded citations to the LLM.

### D. Cost and Latency Scaling as Corpus Grows
- **Cost Scaling:** Embedding APIs bill per token. As the corpus grows from thousands to millions of documents, embedding costs scale linearly with text volume.
- **Latency Scaling:** Network round-trips and API rate limits increase ingestion duration.
- **Production Optimization Strategies:**
  1. **Batching:** Send chunks in batches (e.g. 64-256 chunks per API call) to minimize network latency overhead.
  2. **Deduplication & Caching:** Hash chunk contents (SHA-256) and skip embedding chunks that have already been indexed.
  3. **Incremental Ingestion Manifest:** Maintain an indexing manifest mapping `file_hash + chunk_id` to timestamp so re-runs only embed modified or new files.

## 5. Video Walkthrough Script Guide (3-5 Minutes)

1. **Introduction (0:00 - 0:45):**
   - Introduce PolicyPilot and the purpose of embeddings (converting plain text chunks into semantic vector representations).
   - Explain vector dimension (1536 for `text-embedding-3-small`) as coordinates in semantic meaning space.
2. **Configuration & Security (0:45 - 1:15):**
   - Show environment variable configuration (`OPENAI_API_KEY`, `EMBEDDING_MODEL`, `OPENAI_BASE_URL`).
   - Highlight that secrets are kept outside source code for security and provider flexibility.
3. **Code Walkthrough (1:15 - 2:30):**
   - Show `EmbeddingService.embed_chunks()` in `src/services/embedding_service.py`.
   - Explain batching and how each vector is zipped with its source text and metadata dictionary.
   - Explain why metadata retention (`source`, `chunk_index`) is mandatory for answer citations.
4. **Verification Output & Query Demo (2:30 - 3:45):**
   - Run `python src/run_embedding_demo.py`.
   - Point out output: `model: text-embedding-3-small`, `records: 4`, `vector length: 1536`, and sample vector values.
   - Show query matching similarity ranking.
5. **Follow-Up Questions (3:45 - 4:45):**
   - Why same model for docs and queries? (Uniform semantic coordinate space).
   - What happens to cost and latency as corpus grows? (Linear token cost & latency; mitigated via batching, hashing, and incremental manifest caching).