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

## 3-5 Minute Video Demonstration Guide

For the video submission walkthrough:
1. **Introduction (0:00 - 0:45):** Define retrieval relevance (retrieving chunks that are useful, authoritative, and factually sufficient to answer user queries).
2. **Settings Compared (0:45 - 1:45):** Explain why $k$, metadata filters, and score thresholds were chosen.
3. **Execution & Metrics (1:45 - 2:45):** Run `python src/run_retrieval_tuning_demo.py` and explain Hit Rate, Top-1 Hit, MRR, and Manual Judgment.
4. **Biggest Effect & Winner (2:45 - 3:45):** Justify `calibrated_optimal_k3` (filters noise, avoids token bloating, guarantees 100% Hit Rate).
5. **Follow-Up Analysis (3:45 - 4:45):** How poor retrieval affects final answers (hallucinations, incomplete responses, vague generalizations).

---

**Project:** PolicyPilot  
**Repository:** `SW2627_PolicyPilot_Kalvium-Community`  
**Branch:** `feature/retrieval-tuning`  
**Purpose:** Empirical retrieval tuning, evaluation metrics, and noise reduction for RAG knowledge bases
