"""PolicyPilot RAG Assistant Main Application Entry Point."""

import os
import sys
from pathlib import Path

# Ensure stdout uses UTF-8 encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

from src.services.response_service import ResponseService

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")
API_KEY = os.getenv("API_KEY")
CHAT_MODEL = os.getenv("CHAT_MODEL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")


def run_single_query(response_service: ResponseService, question: str) -> None:
    """Process a single user question through PolicyPilot pipeline and display results."""
    print(f"\nQuestion: {question}")
    result = response_service.generate(question)

    print(f"Relevance Score: {result.get('max_score', 0.0)}")
    print(f"LLM Called: {result.get('llm_called', False)}")
    print("PolicyPilot Answer:")
    print(f"  {result['answer']}")
    print("-" * 60)


def main():
    print("=" * 60)
    print("PolicyPilot Internal Policy Assistant")
    print("=" * 60)
    print(f"API Base URL: {'configured' if API_BASE_URL else 'not configured'}")
    print(f"API Key: {'configured' if API_KEY else 'not configured'}")
    print(f"Chat Model: {CHAT_MODEL or 'not configured'}")
    print("=" * 60)

    response_service = ResponseService()

    # If question passed via CLI argument
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        run_single_query(response_service, question)
        return

    # Sample demo queries if run directly without arguments
    demo_questions = [
        "What is our annual leave allowance for full-time employees?",
        "Who won the FIFA 2024 World Cup?",
        "What is Python?",
        "Tell me a joke.",
        "What is the weather today?",
        "What is our refund window for employee software tool purchases?",
        "Can I carry those annual leave days into next year?",
    ]

    print("\nRunning PolicyPilot pipeline on sample queries:\n")
    for q in demo_questions:
        run_single_query(response_service, q)

    print("\nPolicyPilot foundation is running successfully.")


if __name__ == "__main__":
    main()
