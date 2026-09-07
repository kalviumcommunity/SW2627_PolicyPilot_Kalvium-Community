# PolicyPilot — RAG Assistant Foundation

PolicyPilot is an internal **Retrieval-Augmented Generation (RAG) assistant** designed to answer staff questions using information stored in a knowledge base.

This project establishes the initial foundation for the RAG system by providing an isolated Python environment, reproducible dependencies, a structured workspace, secure environment-variable management, and documented setup instructions.

## Project Structure

```text
SW2627_PolicyPilot_Kalvium-Community/
│
├── data/
│   └── .gitkeep
│
├── src/
│   ├── __init__.py
│   └── main.py
│
├── prompts/
│   └── .gitkeep
│
├── outputs/
│   └── .gitkeep
│
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

### Directory Purpose

| Directory  | Purpose                                 |
| ---------- | --------------------------------------- |
| `data/`    | Local knowledge-base documents and data |
| `src/`     | Application source code                 |
| `prompts/` | RAG prompts and prompt templates        |
| `outputs/` | Generated or local application outputs  |

## Requirements

* Python 3.x
* pip
* Git

## Setup

### 1. Clone the repository

```bash
git clone <YOUR-GITHUB-REPOSITORY-URL>
cd SW2627_PolicyPilot_Kalvium-Community
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

For Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

You should see `(.venv)` at the beginning of your terminal prompt.

### 4. Install dependencies

Install all project dependencies from the reproducible dependency file:

```bash
pip install -r requirements.txt
```

The project uses packages including:

* `openai` — access to OpenAI-compatible language and embedding models
* `chromadb` — vector database for RAG retrieval
* `python-dotenv` — loading configuration from environment variables

Exact installed versions are captured in `requirements.txt`.

### 5. Configure environment variables

Copy the example environment file:

**Windows PowerShell:**

```powershell
Copy-Item .env.example .env
```

The `.env` file should contain the required configuration:

```env
API_BASE_URL=
API_KEY=
CHAT_MODEL=
EMBEDDING_MODEL=
```

Replace the empty values with the appropriate local configuration.

**Never commit `.env` or expose API keys in source code.**

### 6. Run the application

With the virtual environment activated:

```bash
python src/main.py
```

A successful run should display:

```text
==================================================
PolicyPilot RAG Assistant
==================================================
Environment loaded successfully.

API Base URL: ...
API Key: ...
Chat Model: ...
Embedding Model: ...

PolicyPilot foundation is running successfully.
```

## Dependency Reproducibility

Project dependencies are stored in `requirements.txt` with version constraints.

A teammate can recreate the environment using:

```bash
python -m venv .venv
```

```powershell
.venv\Scripts\Activate.ps1
```

```bash
pip install -r requirements.txt
```

This ensures that the project does not depend on packages installed globally on a developer's machine.

## Security

PolicyPilot uses environment variables for configuration and API credentials.

The repository follows these security practices:

* `.env` is excluded from Git.
* `.venv/` is excluded from Git.
* Local `data/` files are excluded from Git.
* Generated local outputs are excluded from Git.
* API keys are never hardcoded into source code.
* `.env.example` documents required variables without containing real credentials.

To verify that `.env` is ignored:

```bash
git check-ignore -v .env
```

To verify that the virtual environment is ignored:

```bash
git check-ignore -v .venv
```

## Clean-Run Verification

The project was verified using an isolated Python virtual environment.

The verification process was:

1. Created a fresh `.venv` environment.
2. Activated the environment.
3. Installed dependencies using `requirements.txt`.
4. Created `.env` from `.env.example`.
5. Ran the application using:

```bash
python src/main.py
```

6. Confirmed that the PolicyPilot foundation started successfully without errors.

This confirms that a teammate can reproduce the project setup from scratch using the documented instructions.

## Git Workflow

The project uses Git for version control.

Before committing, verify that sensitive or local files are not staged:

```bash
git status
```

The following files/directories must **not** be committed:

```text
.env
.venv/
data/ local documents
outputs/ generated local files
```

The `.env.example` file is safe to commit because it contains variable names only and no real credentials.

## Retrieval Settings Tuning & Evaluation (Sprint 2)

PolicyPilot includes a comprehensive retrieval evaluation and tuning framework (`src/services/retrieval_service.py`) to benchmark nearest-neighbor vector search, metadata filters, score cutoffs, and top-$k$ configurations against ground-truth query-source pairs.

### 1. Ground-Truth Test Queries & Expected Sources

| Query ID | User Search Query | Expected Ground-Truth Source | Target Domain |
| --- | --- | --- | --- |
| `Q1` | *How can a learner reset their password?* | `account-guide.md` | Authentication & Account Support |
| `Q2` | *When does the cafeteria menu change?* | `campus-guide.md` | Campus Life & Dining |
| `Q3` | *What evidence is required for project submission?* | `submission-rubric.md` | Academic Evaluation |
| `Q4` | *How many days per week can employees work remotely?* | `remote_policy.txt` | HR & Workplace Policy |
| `Q5` | *What is the monthly limit for home internet allowance?* | `stipend_faq.html` | Finance & Reimbursements |
| `Q6` | *What are the rules for overtime approval and daily work hours?* | `work_hours.md` | Operations & Work Hours |
| `Q7` | *What is the daily meal per diem for business travel?* | `sample_policy.pdf` | Travel & Expense Policies |

### 2. Retrieval Settings Compared

We systematically evaluate 6 distinct configurations:

1. **`baseline_k3`**: Top-$k=3$, no metadata filter, no score threshold (`min_score=0.0`).
2. **`filtered_k3`**: Top-$k=3$, hard metadata filter strictly on `{"doc_type": "guide"}`.
3. **`strict_k5`**: Top-$k=5$, strict score cutoff (`min_score=0.72`).
4. **`minimal_k1`**: Top-$k=1$, no filter, testing rank-1 precision vs risk of dropped context.
5. **`expanded_k5`**: Top-$k=5$, no filter, testing recall gains vs token noise overhead.
6. **`calibrated_optimal_k3`**: Top-$k=3$, calibrated noise-filtering threshold (`min_score=0.30`).

### 3. Summary Results & Relevance Metrics

| Setting Name | $k$ | Metadata Filter | Min Score | Hit Rate (Recall@k) | Top-1 Accuracy | MRR | Avg Chunks Returned |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `baseline_k3` | 3 | None | 0.00 | **100.0%** | 100.0% | 1.0000 | 3.00 |
| `filtered_k3` | 3 | `{'doc_type': 'guide'}` | 0.00 | **28.6%** | 28.6% | 0.2857 | 1.86 |
| `strict_k5` | 5 | None | 0.72 | **0.0%** | 0.0% | 0.0000 | 0.00 |
| `minimal_k1` | 1 | None | 0.00 | **100.0%** | 100.0% | 1.0000 | 1.00 |
| `expanded_k5` | 5 | None | 0.00 | **100.0%** | 100.0% | 1.0000 | 5.00 |
| `calibrated_optimal_k3` | 3 | None | 0.30 | **100.0%** | 100.0% | 1.0000 | 1.00 |

### 4. Running the Retrieval Tuning Demo

Run the automated experiment runner to evaluate all settings and export reports:

```bash
python src/run_retrieval_tuning_demo.py
```

Generated artifact outputs:
- `outputs/retrieval_eval_queries.json`: Ground-truth test query dataset.
- `outputs/retrieval_tuning_results.json`: Machine-readable evaluation metrics and row-level details.
- `outputs/retrieval_tuning_report.md`: Detailed markdown evaluation report.

### 5. Running the Test Suite

Run the full automated test suite with pytest:

```bash
pytest
```

---

## Chunk Re-Ranking for Precision (Sprint 2 - Concept 3.35)

PolicyPilot implements a high-precision **two-stage retrieval and re-ranking pipeline** (`src/services/reranking_service.py`):
1. **Stage 1 (Vector Candidate Retrieval):** Quickly retrieves an expanded pool of candidates ($k_{\text{candidates}}=10$) using fast nearest-neighbor embedding search.
2. **Stage 2 (Cross-Attention & LLM Re-Ranking):** Jointly scores each query-chunk pair on a $0–10$ relevance scale, promoting the exact factual answer to Rank 1 and selecting the top $k_{\text{final}}=3$ chunks for the LLM context.

### 1. Sample Query: *"What evidence is required for project submission?"*

#### Before Re-Ranking (Initial Vector Retrieval — Top 3 of 10):
```text
rank: 1 | vector_score: 0.5419 | rerank_score: None | source: submission-rubric.md
text: Academic Project Submission Rubric: What evidence is required for project submission? Required evidence includes a public GitHub...
rank: 2 | vector_score: 0.2331 | rerank_score: None | source: submission-rubric.md
text: Project Submission Deadlines and Extensions: All project milestone deliverables must be uploaded to the LMS before Sunday...
rank: 3 | vector_score: 0.1823 | rerank_score: None | source: team-project-policy.md
text: Collaborative Team Project Guidelines: Team projects require evidence of equitable task distribution via individual git...
```

#### After Re-Ranking (Cross-Scored Precision Order — Final Context 3):
```text
rank: 1 | vector_score: 0.5419 | rerank_score: 7.90 | source: submission-rubric.md
text: Academic Project Submission Rubric: What evidence is required for project submission? Required evidence includes a public GitHub...
rank: 2 | vector_score: 0.2331 | rerank_score: 4.71 | source: submission-rubric.md
text: Project Submission Deadlines and Extensions: All project milestone deliverables must be uploaded to the LMS before Sunday...
rank: 3 | vector_score: 0.1823 | rerank_score: 3.21 | source: team-project-policy.md
text: Collaborative Team Project Guidelines: Team projects require evidence of equitable task distribution via individual git...
```

### 2. Cost & Latency Trade-Off Analysis

| Stage | Mechanism | Computational Complexity | Latency | Primary Role |
| --- | --- | --- | --- | --- |
| **Stage 1: Retrieval** | Dense Bi-Encoder HNSW | $O(\log N)$ dot products | ~2 ms | **High Recall:** Narrows entire corpus to top 10 candidates |
| **Stage 2: Re-Ranking** | Joint Cross-Scorer / LLM | $O(K \cdot L^2)$ cross-scoring | ~0.2–20 ms | **High Precision:** Ranks exact evidence at the top |

**When is Re-Ranking worth the extra latency?**
- In compliance, academic evaluation, and policy QA where answering with a generic clause causes errors.
- When knowledge bases contain dense keyword overlap across different sections.
- To reduce generative LLM costs by sending only 3 verified chunks instead of 10 unranked chunks.

### 3. Running the Re-Ranking Demo

```bash
python src/run_reranking_demo.py
```

Generated outputs:
- `outputs/reranking_results.json`: Complete machine-readable pipeline trace.
- `outputs/reranking_report.md`: Detailed before-and-after evaluation report.

---

## 3-5 Minute Video Demonstration Guide

For the video submission walkthrough:
1. **Why Re-Ranking is Useful (0:00 - 0:45):** Bi-encoders encode queries and documents independently; re-ranking performs joint attention to capture exact semantic alignment.
2. **Difference Between Retrieval and Re-Ranking (0:45 - 1:30):** Retrieval searches the whole database quickly; re-ranking deeply scores a small candidate pool ($k=10$).
3. **Live Execution & Before/After (1:30 - 2:45):** Run `python src/run_reranking_demo.py` and show `show("before re-ranking", candidates[:final_k])` vs `show("after re-ranking", final_context)`.
4. **Cost Trade-Offs (2:45 - 3:45):** Re-ranking adds minimal compute on 10 chunks while saving LLM prompt context tokens.
5. **Follow-Up Analysis (3:45 - 4:45):** When is re-ranking worth it? (High-stakes precision, overlapping document vocabularies, context compression).

---

## Prompt Augmentation & Context Injection (Sprint 2 - Concept 3.36)

PolicyPilot implements robust **Prompt Augmentation and Context Injection** (`src/services/prompt_service.py`) to transform retrieved evidence chunks into structured, token-bounded, grounded prompts for the generator model.

### 1. Key Capabilities

1. **Chunk Labeling & Source Citation Markers:**
   - Formats each retrieved chunk as `[{index}] {source}#{chunk_index}\n{text}`.
   - Example:
     ```text
     [1] account-guide.md#0
     How can a learner reset their password? Learners can reset their password by navigating to the login portal...
     ```
2. **Strict Token Budgeting (`MAX_CONTEXT_TOKENS`):**
   - Automatically packs highest-ranked chunks first using `tiktoken` (cl100k_base).
   - Enforces a hard context cap (e.g. 5,000 tokens) reserving headroom for instructions, question, and generated output.
3. **Grounded Instruction & Refusal Fallback:**
   - Explicitly instructs the model to answer strictly from the provided context and cite source markers (`[1]`, `[2]`).
   - Mandates refusal when context is insufficient: *"I don't have enough information in the provided context."*

### 2. Running the Prompt Augmentation Demo

```bash
python src/run_prompt_augmentation_demo.py
```

Generated outputs:
- `outputs/prompt_augmentation_results.json`: Prompt assembly records and token usage metadata.
- `outputs/prompt_augmentation_report.md`: Markdown documentation of context formatting and token budgeting.

---

## Hallucination Guardrails & Refusal Handling (Sprint 2 - Concept 3.41)

PolicyPilot implements robust pre-generation **Hallucination Guardrails and Safe Refusal Mechanisms** (`src/services/response_service.py`):
1. **Detect Weak or Missing Retrieval:** Evaluates retrieved chunks against a calibrated relevance score threshold (`min_score=0.35`) and minimum supporting chunk count (`min_supporting_chunks=1`) before invoking the generator.
2. **Safe Refusal on Weak Context:** If retrieval yields empty results or scores below threshold, execution halts immediately and returns a safe refusal message (`"I don't have enough reliable context to answer that."`, `status="refused_weak_context"`), avoiding unsupported hallucinations.
3. **Preserve Confident Grounded Answers:** When strong evidence exists, generates grounded, factual responses with source markers (`[1]`, `[2]`) (`status="answered"`).

### 1. Guardrail Evaluation Summary Table

| Test ID | Query Type | Question | Top Similarity Score | Status | Result | Answer / Safe Refusal Output |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TC1` | `answer_case` | *What evidence is required for project submission?* | `0.6445` | **`answered`** | **PASS** | *"Based on the provided context, the required evidence for project submission includes a public GitHub repository link, clean code, test reports, and a 3-5 min video [1]."* |
| `TC2` | `answer_case` | *How can a learner reset their password?* | `0.6183` | **`answered`** | **PASS** | *"To reset their password, a learner should navigate to the login portal, select 'Forgot Password', enter their registered email address, and follow instructions [1]."* |
| `TC3` | `answer_case` | *How many days per week are employees permitted to work remotely?* | `0.5710` | **`answered`** | **PASS** | *"Employees are permitted to work remotely up to three days per week [1]."* |
| `TC4` | `refusal_case` | *What is the refund policy for a product not in this corpus?* | `0.2041` | **`refused_weak_context`** | **PASS** | *"I don't have enough reliable context to answer that."* |
| `TC5` | `refusal_case` | *What are the health insurance dental coverage tiers and copay amounts?* | `0.1909` | **`refused_weak_context`** | **PASS** | *"I don't have enough reliable context to answer that."* |
| `TC6` | `refusal_case` | *How do employees book international flights using the Concur travel portal?* | `0.1564` | **`refused_weak_context`** | **PASS** | *"I don't have enough reliable context to answer that."* |

### 2. Refusing vs. Answering Trade-Off Analysis

| Strategy | Strengths | Risks / Drawbacks | Ideal Use Case |
| :--- | :--- | :--- | :--- |
| **Aggressive Answering** | Minimizes user friction; handles edge cases | High hallucination rate; confident misinformation | Open-ended brainstorming, creative writing, casual chatbots |
| **Aggressive Refusal** | 0% hallucination rate; highest factual reliability | Higher false-refusal rate on valid questions | Medical diagnostics, legal contracts, regulatory compliance |
| **Calibrated Guardrail (PolicyPilot)** | 100% recall on indexed policies; immediate refusal on unindexed topics | Requires empirical threshold calibration per domain | Internal company handbooks, academic rubrics, enterprise policies |

### 3. Running the Guardrails Demo

```bash
python src/run_guardrails_demo.py
```

Generated outputs:
- `outputs/guardrail_refusal_results.json`: Complete test case records with scores, statuses, and outputs.
- `outputs/guardrail_refusal_report.md`: Markdown evaluation report with trade-off analysis and video script.

---

## 3–5 Minute Video Demonstration Guide (Concept 3.41)

For your video submission:
1. **What is Hallucination & Why is it Dangerous? (0:00 – 0:45):**
   - Explain that a hallucination is an unsupported answer that sounds confident and plausible.
   - In corporate and academic policies, a hallucination can mislead employees or students on grading, leave, or compliance rules.
2. **How PolicyPilot Decides When to Refuse (0:45 – 1:45):**
   - Walk through `retrieval_is_strong()` in `src/services/response_service.py`.
   - Explain the relevance threshold (`min_score = 0.35`) and supporting chunk count.
3. **Live Demonstration of Answered vs. Refusal Cases (1:45 – 2:45):**
   - Run `python src/run_guardrails_demo.py`.
   - Show `TC1` (*"What evidence is required for project submission?"* -> `status="answered"` with `[1]` citation).
   - Show `TC4` (*"What is the refund policy for a product not in this corpus?"* -> `status="refused_weak_context"` with `"I don't have enough reliable context to answer that."`).
4. **The Trade-Off Between Refusing and Answering (2:45 – 3:45):**
   - Discuss why refusing too often frustrates users, while answering too freely causes misinformation.
5. **Follow-Up: Why Refusing is Safer in High-Stakes Domains (3:45 – 4:45):**
   - Explain that in high-stakes domains (legal, healthcare, finance, policy), an explicit refusal prompts the user to verify with human HR/support, avoiding severe liability and compliance breaches.

---

**Project:** PolicyPilot  
**Repository:** `SW2627_PolicyPilot_Kalvium-Community`  
**Branch:** `feature/hallucination-guardrails`  
**Purpose:** Pre-generation retrieval quality verification, safe refusal handling, and hallucination reduction for enterprise RAG.

