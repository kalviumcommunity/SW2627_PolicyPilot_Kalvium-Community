# PolicyPilot Filtered & Hybrid Retrieval Demonstration Report

- **Purpose:** Demonstrate metadata pre-filtering, hybrid (vector + keyword) retrieval, and precision enhancement over baseline top-k search.
- **Corpus Scope:** `remote_policy.txt`, `stipend_faq.html`, `work_hours.md`, `sample_policy.pdf`.

## 1. Task 1 & 2: Metadata Filtered vs. Unfiltered Search Comparison

### Query: *"What is the maximum reimbursement amount for home internet allowance?"*
- **Metadata Filter Applied:** `{"doc_type": "html"}`
- **Unfiltered Precision:** `33.33%` (1/3 target chunks)
- **Filtered Precision:** `100.0%` (1/1 target chunks)

#### Unfiltered Top-K Vector Search Results:
| Rank | Score | Source Document | Format | Content Snippet |
| :---: | :---: | :--- | :---: | :--- |
| #1 | `0.3895` | `stipend_faq.html` | `html` | *"Stipend FAQ Stipend & Reimbursement FAQ Q: What can I claim under the internet a..."* |
| #2 | `0.0551` | `sample_policy.pdf` | `pdf` | *"PolicyPilot Official Travel Reimbursement Guidelines 1. Travel expenses must be..."* |
| #3 | `0.0532` | `work_hours.md` | `md` | *"# Work Hours and Overtime Guideline  All remote workers must log their daily che..."* |

#### Metadata Filtered Top-K Search Results:
| Rank | Score | Source Document | Format | Content Snippet |
| :---: | :---: | :--- | :---: | :--- |
| #1 | `0.3895` | `stipend_faq.html` | `html` | *"Stipend FAQ Stipend & Reimbursement FAQ Q: What can I claim under the internet a..."* |

## 2. Task 3: Hybrid Search (Vector Similarity + Lexical Keyword Matching)

### Query: *"How many hours per day and week are standard work hours?"*
- **Algorithm:** Hybrid Score $= 0.6 \times \text{Vector Cosine Sim} + 0.4 \times \text{Keyword Match Score}$
- **Target Boost Keywords:** `['standard', 'hours', '8', '40', 'overtime']`

| Rank | Hybrid Score | Vector Score | Keyword Score | Source Document | Snippet |
| :---: | :---: | :---: | :---: | :--- | :--- |
| #1 | `0.7393` | `0.5655` | `1.0000` | `work_hours.md` | *"# Work Hours and Overtime Guideline  All remote workers must log their..."* |
| #2 | `0.6058` | `0.3430` | `1.0000` | `remote_policy.txt` | *"Company Remote Work Policy Effective: January 1, 2026  Eligible employ..."* |
| #3 | `0.0870` | `0.0783` | `0.1000` | `stipend_faq.html` | *"Stipend FAQ Stipend & Reimbursement FAQ Q: What can I claim under the..."* |

## 3. Task 4: Precision Improvement Demonstration

### Query: *"What are the rules and deadlines for travel expense reimbursement?"*
- **Applied Filter:** `{"source": "sample_policy.pdf"}`
- **Baseline Unfiltered Precision:** `33.33%` — Top-k vector search retrieves unrelated chunks from `work_hours.md` and `stipend_faq.html` due to generic word overlap ('reimbursement', 'guidelines').
- **Filtered Search Precision:** `100.0%` — Eliminates cross-document noise, ensuring 100% of retrieved chunks belong strictly to `sample_policy.pdf`.

## 4. Technical Guide for Video Walkthrough Script

### Q1: Why does metadata filtering improve retrieval precision?
- Metadata filtering pre-screens candidate vector chunks before distance/similarity calculations.
- By scoping retrieval to specific document types, sources, categories, or date ranges, it guarantees zero irrelevant chunks from outside the target domain enter the top-k context window.

### Q2: Difference between Vector Search and Keyword Search?
- **Vector Search:** Maps text to high-dimensional embeddings to capture semantic intent and synonyms (e.g. 'work from home' matches 'remote work'), but can suffer from soft semantic hallucination or keyword dilution.
- **Keyword Search:** Looks for exact string tokens, policy numbers, or IDs (e.g. '$75', 'Form 1040'), guaranteeing literal term matching but failing when word phrasing differs.

### Q3: When is Hybrid Search better than pure vector search?
- Hybrid search is superior whenever queries contain specific numeric limits (`$75`), exact policy names (`PolicyPilot`), product codes, or domain jargon alongside natural language questions.

### Q4: Follow-up — What filter would our RAG problem statement need?
- For PolicyPilot, filtering by `department` (HR vs. Travel vs. Finance), `user_role` (Employee vs. Manager), and `document_status` (Active vs. Archived) ensures staff receive only currently applicable, role-authorized policies.
