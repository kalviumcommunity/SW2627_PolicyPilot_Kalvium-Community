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

## Current Scope

This repository establishes the foundation for the PolicyPilot RAG assistant.

The next stages of development can include:

* Document ingestion
* Document chunking
* Embedding generation
* ChromaDB indexing
* Similarity and hybrid retrieval
* Prompt construction
* LLM-based answer generation
* Source citation
* Evaluation of retrieval quality
* User-facing RAG assistant interface

---

**Project:** PolicyPilot
**Repository:** `SW2627_PolicyPilot_Kalvium-Community`
**Purpose:** Reproducible and secure foundation for an internal RAG assistant
