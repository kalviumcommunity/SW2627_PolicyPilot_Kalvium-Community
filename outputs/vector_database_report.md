# Vector Database Collection Setup and Readback Report

This report documents the implementation, configuration, and verification of PolicyPilot's Vector Database (ChromaDB) storage system, collection schema design, and insert/readback verification (Sprint 2 Concept 25).

---

## 1. Summary of Completed Tasks

| Task | Description | Status | Verification Detail |
| --- | --- | --- | --- |
| **Task 1** | Set up a reachable vector database | Complete | Connected via ChromaDB persistent/in-memory client (`outputs\chroma_db`) |
| **Task 2** | Create a correctly sized collection | Complete | Collection `rag_chunks` created with dimension `1536` & `cosine` distance |
| **Task 3** | Design the stored record schema | Complete | Schema stores `id`, `vector` (1536 floats), `text`, and rich `metadata` |
| **Task 4** | Insert and read back a test record | Complete | Successfully inserted & retrieved `account-guide.md:0` |
| **Task 5** | Commit setup & output artifacts | Complete | Exported to `outputs/vector_store_readback.json` and report |

---

## 2. Verification Output

The test record was inserted into the collection and read back:

```text
--------------------------------------------------
Verification Output:
--------------------------------------------------
readback id: account-guide.md:0
vector length: 1536
text: Password reset instructions for learner accounts.
metadata: {'token_count': 8, 'section': 'Account access', 'chunk_index': 0, 'source': 'account-guide.md'}
--------------------------------------------------
```

---

## 3. Stored Record Schema Architecture

```json
{
  "id": "account-guide.md:0",
  "vector": [0.0312, -0.0451, "... (1536 float values) ..."],
  "text": "Password reset instructions for learner accounts.",
  "metadata": {
    "source": "account-guide.md",
    "chunk_index": 0,
    "section": "Account access",
    "token_count": 8
  }
}
```

### Schema Component Roles:
1. **`id` (Unique Identifier):** A stable, deterministic string combining the document name and chunk index (`source:chunk_index`). Enables idempotent upserts, preventing duplicate indexing on re-runs.
2. **`vector` (Embedding):** Dense mathematical vector (1536 floating-point numbers) representing the semantic meaning of the chunk.
3. **`text` (Raw Chunk Text):** The original readable content required to inject into the LLM prompt context window during RAG generation.
4. **`metadata` (Dictionary):** Crucial provenance information (source filename, chunk position, token count, section headers) utilized for source citation, filtering, and access control.

---

## 4. Key Concepts & Architecture Deep Dive

### A. What a Vector Database Does Differently From a Normal Database
- **Relational / Document DBs (SQL / MongoDB):** Optimized for exact key lookups (`WHERE id = 'x'`), scalar filters (`WHERE age > 30`), structured joins, and ACID transactions. Searching for text requires lexical keyword matching (BM25, regex, full-text indexes) which fails when users use synonyms or paraphrase.
- **Vector Databases (Chroma, Qdrant, Pinecone, pgvector):** Built for **Approximate Nearest Neighbor (ANN)** search in multi-dimensional vector space. Given a query vector, it rapidly computes geometric distance (Cosine, Dot Product, Euclidean/L2) using specialized index graphs (e.g. HNSW - Hierarchical Navigable Small World) to return conceptually closest chunks in milliseconds, even if query and document share zero identical keywords.

### B. Why Collection Dimension Must Match Embedding Model
- Embedding models project language into fixed $N$-dimensional vector spaces. For OpenAI `text-embedding-3-small`, $N = 1536$.
- Geometric distance formulas (dot product sum(a_i * b_i) and cosine similarity (A . B) / (||A|| * ||B||)) require pairs of vectors to have identical dimensionality.
- If a collection expects 1536 dimensions and receives a 768 or 384-dimensional vector:
  - Vector operations cannot execute (dimension mismatch mathematical failure).
  - Attempting to compare vectors across different dimensional spaces yields meaningless garbage.
  - Fail-early dimension validation ensures indexing integrity.

### C. Why Text and Metadata Are Stored With the Vector
- Returning only an array of floats or an anonymous record ID leaves the RAG application stranded:
  1. The LLM needs the **original chunk text** to formulate a grounded, factual answer.
  2. The user interface needs **source citations** (e.g. `source: account-guide.md`, `page: 2`) so users can verify where the answer came from.
  3. Storing vector, text, and metadata in a single record avoids costly secondary round-trips to another database, minimizing retrieval latency.
  4. Vector databases support **filtered vector search** (e.g. `similarity_search(query, where={"department": "HR"})`), filtering out irrelevant documents before or during nearest-neighbor traversal.

### D. How to Choose a Vector Database for Production
When selecting a production vector database, evaluate:
1. **Scale & Corpus Size:**
   - *Small to Medium (< 1 million vectors):* Embedded vector stores like **ChromaDB** or **SQLite-vec** are simple, zero-infrastructure, and cost-effective.
   - *Large (> 10 million vectors):* Dedicated distributed vector stores like **Qdrant**, **Milvus**, or **Pinecone**.
2. **Operational & Hosting Model:**
   - *Fully Managed (SaaS):* Pinecone, Qdrant Cloud (hands-off scaling, managed backups, zero devops).
   - *Self-Hosted / Kubernetes:* Qdrant, Chroma, Milvus (full data sovereignty, VPC isolation).
   - *Hybrid Relational + Vector:* **pgvector** (PostgreSQL) if you already run Postgres and want ACID transactions alongside vector search.
3. **Filtering Requirements & Query Latency:**
   - Look for native **payload indexing** and single-stage filtered HNSW search (e.g. Qdrant) so metadata filters do not degrade query latency.
4. **Cost & Team Familiarity:**
   - Measure cost per million queries and storage footprint. Avoid over-engineering when an embedded or PostgreSQL-based vector store meets throughput SLAs.

---

## 5. Video Walkthrough Script Guide (3-5 Minutes)

1. **Introduction (0:00 - 0:45):**
   - Introduce PolicyPilot and the role of the Vector Database.
   - Explain what a vector database does differently from a standard database (semantic nearest neighbor search vs exact keyword matching).
2. **Collection Setup & Dimension Matching (0:45 - 1:30):**
   - Explain why the collection dimension must strictly match the embedding model (1536 dimensions for `text-embedding-3-small`).
   - Show `VectorStoreService` initialization and `get_or_create_collection()` with cosine distance metric.
3. **Record Schema Design (1:30 - 2:30):**
   - Explain the schema structure: `id`, `vector`, `text`, and `metadata`.
   - Explain why text and metadata belong right next to the vector (grounded LLM context generation and source citation without secondary lookups).
4. **Insert and Readback Verification (2:30 - 3:45):**
   - Run `python src/run_vector_db_demo.py`.
   - Highlight the verification output:
     - `readback id: account-guide.md:0`
     - `vector length: 1536`
     - `text: Password reset instructions for learner accounts.`
     - `metadata: {'source': 'account-guide.md', 'chunk_index': 0, 'section': 'Account access'}`
   - Show nearest-neighbor semantic search ranking top matching chunks for user queries.
5. **Production Considerations & Wrap-up (3:45 - 4:45):**
   - Address the follow-up question: How would you choose a vector database for production? (Scale, managed vs self-hosted, pgvector vs dedicated vector store, metadata filtering performance).
