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

## LLM & Tokenization Core Concepts (Viva Guide)

To prepare for your viva, here is a simple breakdown of the core concepts demonstrated in PolicyPilot:

### 1. What is a Token?
* A **token** is the basic unit of text processed by a Large Language Model (LLM). It is not always a full word; it can be a single character, a syllable, a punctuation mark, or a sub-word.
* On average, in English text, 1 token is approximately equal to 4 characters or 0.75 words (conversely, 100 English words is roughly 130–140 tokens).

### 2. Why Token Count Matters
* **Computational Cost:** LLMs process tokens sequentially. Larger token counts mean more computations, which translates directly to higher API usage costs.
* **Speed/Latency:** The processing and generation time (latency) of LLMs scale with the number of input and output tokens.
* **Context Budgeting:** LLMs have finite input capacities. Managing and tracking token counts prevents errors due to context window overflow.

### 3. How Token Count Affects Cost
* API providers charge for LLMs on a pay-per-use model based on the number of tokens processed.
* Input (prompt) tokens are priced differently from output (completion) tokens (output tokens are usually more expensive due to autoregressive generation overhead).
* PolicyPilot calculates estimated cost dynamically using the formula:
  * Input Cost = (Input Tokens / 1000) * Input Price
  * Output Cost = (Output Tokens / 1000) * Output Price
  * Total Cost = Input Cost + Output Cost

### 4. How Token Count Affects Context Limits
* The **Context Window** is the maximum total limit of combined input and output tokens that a model can process in a single API call (e.g., 4,096 tokens, 8,192 tokens, etc.).
* If your prompt (system prompt + retrieved context + user query) is larger than this limit, the API request will fail or truncate key information.
* PolicyPilot prevents this by doing a pre-execution **Context Window check** and safely truncating the retrieved context until it fits inside the maximum token limit.

### 5. Difference between System and User Messages
* **System Message (Instructions/Rules):** Establishes the persona, goals, constraints, guidelines, and safety boundaries for the chatbot. It instructs the chatbot on *how* to answer (e.g., "Answer only using the provided policy, keep it concise, and reply with a specific fallback if unsure").
* **User Message (Customer query/turn):** The specific input supplied by the user during the chat turn (e.g., "What is the return period?").
* **Context (Retrieved documents):** The official policy text fetched from `data/ecommerce_policies.txt` that is appended to the user message to ground the LLM's answer.

### 6. How PolicyPilot Uses These Concepts
* **Token Counting Utility:** Uses `tiktoken` to count tokens of prompts and responses.
* **Cost Estimation Utility:** Computes the cost of each transaction based on token usage.
* **Safe Context Window Management:** Detects if the retrieved policies exceed the context limit and truncates them, warning the user.
* **Grounded Prompts (System vs User separation):** Prompts the model to answer strictly using the retrieved text and refuse to answer if the context does not contain the answer, preventing hallucination.
* **Message History Pruner:** Dynamically drops the oldest message pairs (turns) when history tokens exceed limits, keeping the prompt within budget while preserving the system instructions.

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
git checkout -b feature/github-workflow-setup
