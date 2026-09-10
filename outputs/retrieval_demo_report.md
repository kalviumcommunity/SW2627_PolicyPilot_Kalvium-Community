# PolicyPilot Vector Retrieval Demonstration Report

- **Sample User Query:** *"How many days per week can eligible employees work remotely?"*
- **Query Embedding Dimension:** `1536`
- **Embedding Model:** Same model as document chunks (`EmbeddingService` / `text-embedding-ada-002` deterministic vectorizer)
- **Evaluated K Values:** `[2, 5]`

## 1. Top-K Similarity Search Results (k=3)

| Rank | Cosine Score | Source Document | Chunk Index | Token Count | Content Snippet |
| :---: | :---: | :--- | :---: | :---: | :--- |
| #1 | `0.4406` | `remote_policy.txt` | #0 | 0 | *"Company Remote Work Policy Effective: January 1, 2026  Eligible employees are al..."* |
| #2 | `0.1776` | `work_hours.md` | #0 | 0 | *"# Work Hours and Overtime Guideline  All remote workers must log their daily che..."* |
| #3 | `0.1553` | `stipend_faq.html` | #0 | 0 | *"Stipend FAQ Stipend & Reimbursement FAQ Q: What can I claim under the internet a..."* |

## 2. Multi-K Demonstration & Comparison

Running the exact same query across different values of $k$ illustrates how retrieval scope expands:

### Demonstration for $k=2$
- **Chunks Retrieved:** `2`
- **Highest Similarity Score:** `0.4406`
- **Lowest Similarity Score in Top-2:** `0.1776`

| Rank | Score | Source Document | Chunk Index | Snippet |
| :---: | :---: | :--- | :---: | :--- |
| #1 | `0.4406` | `remote_policy.txt` | #0 | *"Company Remote Work Policy Effective: January 1, 2026  Eligi..."* |
| #2 | `0.1776` | `work_hours.md` | #0 | *"# Work Hours and Overtime Guideline  All remote workers must..."* |

### Demonstration for $k=5$
- **Chunks Retrieved:** `4`
- **Highest Similarity Score:** `0.4406`
- **Lowest Similarity Score in Top-5:** `0.0856`

| Rank | Score | Source Document | Chunk Index | Snippet |
| :---: | :---: | :--- | :---: | :--- |
| #1 | `0.4406` | `remote_policy.txt` | #0 | *"Company Remote Work Policy Effective: January 1, 2026  Eligi..."* |
| #2 | `0.1776` | `work_hours.md` | #0 | *"# Work Hours and Overtime Guideline  All remote workers must..."* |
| #3 | `0.1553` | `stipend_faq.html` | #0 | *"Stipend FAQ Stipend & Reimbursement FAQ Q: What can I claim..."* |
| #4 | `0.0856` | `sample_policy.pdf` | #0 | *"PolicyPilot Official Travel Reimbursement Guidelines 1. Trav..."* |

## 3. Technical Answers for Video Walkthrough

### Q1: What does top-$k$ mean and how is $k$ chosen?
- **Definition:** Top-$k$ similarity search retrieves the $k$ document chunks from the vector database that have the highest cosine similarity scores relative to the embedded user query vector.
- **How $k$ is Chosen:** $k$ is selected based on context window budget, corpus density, and question complexity. Smaller $k$ (e.g. 2-3) minimizes LLM prompt tokens and prevents irrelevant distraction, while larger $k$ (e.g. 5-10) improves recall for multi-document synthesis.

### Q2: Why must the user query use the exact same embedding model as documents?
- Vector embeddings represent text as points in a high-dimensional mathematical vector space.
- Different embedding models map semantic concepts to completely different vector spaces with different coordinate axes and dimensions.
- Comparing a query vector from Model A against chunk vectors from Model B produces meaningless dot products and invalid cosine similarity scores.

### Q3: What is the trade-off of using a larger $k$?
- **Pros:** Higher recall — reduces risk of omitting crucial background information or supporting policy clauses.
- **Cons:** Increased prompt length, higher API latency, higher token cost, and risk of introducing noisy/irrelevant context that dilutes model focus ('lost in the middle' phenomenon).
