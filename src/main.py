import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")
API_KEY = os.getenv("API_KEY")
CHAT_MODEL = os.getenv("CHAT_MODEL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")


def main():
    print("=" * 50)
    print("PolicyPilot RAG Assistant")
    print("=" * 50)
    print("Environment loaded successfully.")
    print()
    print(f"API Base URL: {'configured' if API_BASE_URL else 'not configured'}")
    print(f"API Key: {'configured' if API_KEY else 'not configured'}")
    print(f"Chat Model: {CHAT_MODEL or 'not configured'}")
    print(f"Embedding Model: {EMBEDDING_MODEL or 'not configured'}")
    print()
    print("PolicyPilot foundation is running successfully.")


if __name__ == "__main__":
    main()
