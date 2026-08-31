"""Main application entrypoint for PolicyPilot.

Runs a demonstration of e-commerce policy chatbot interactions,
token counting, cost estimation, context limit checks, and history management.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure project root is in sys.path for direct module runs
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.document_service import DocumentService
from src.services.retrieval_service import RetrievalService
from src.services.response_service import ResponseService
from src.services.token_service import estimate_cost, get_token_count
from src.services.history_service import ConversationHistory
from src.services.embedding_service import EmbeddingService

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")
API_KEY = os.getenv("API_KEY")
CHAT_MODEL = os.getenv("CHAT_MODEL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")


def print_separator():
    print("-" * 65)


def main():
    print("=" * 65)
    print("            PolicyPilot E-commerce Chatbot Demo")
    print("=" * 65)
    print("Environment loaded successfully.")
    print(f"API Base URL: {'configured' if API_BASE_URL else 'not configured'}")
    print(f"API Key: {'configured' if API_KEY else 'not configured'}")
    print(f"Chat Model: {CHAT_MODEL or 'not configured'}")
    print(f"Embedding Model: {EMBEDDING_MODEL or 'not configured'}")
    print_separator()

    # Load return policy and seller agreement documents
    doc_service = DocumentService("data")
    policies = doc_service.load_documents()

    if not policies:
        print(
            "[Error] No policy documents found in the data/ directory. "
            "Please ensure data/ecommerce_policies.txt is present."
        )
        return

    print("Policy documents successfully loaded.")

    retrieval_service = RetrievalService()
    response_service = ResponseService()

    # Configure demonstration variables
    input_price = 0.0015  # pricing per 1,000 input tokens
    output_price = 0.0020  # pricing per 1,000 output tokens
    max_limit = 1000

    queries = [
        "What is the return period?",
        "Can I return a damaged product?",
        "What are the refund conditions?",
        "What are the seller's responsibilities?",
        "Can I claim a refund for my personal gym membership?",
    ]

    print("\n=== RUNNING CHATBOT ASSIGNMENT DEMO ===")

    for idx, query in enumerate(queries, 1):
        print(f"\nInteraction #{idx}")
        print_separator()
        print(f"User Question:\n\"{query}\"")

        # 1. Retrieve policy context
        context = retrieval_service.search(query, policies)
        print(
            f"\nContext (Retrieved):\n{context if context else '[No relevant policy text found]'}"
        )

        # 2. Generate grounded answer
        res = response_service.generate(
            query, context, max_context_limit=max_limit
        )

        # 3. Estimate cost
        costs = estimate_cost(
            res["input_tokens"],
            res["output_tokens"],
            input_price_per_1k=input_price,
            output_price_per_1k=output_price,
        )

        print(f"\nAnswer:\n{res['answer']}")

        print("\nToken Information:")
        print(f"  Input Tokens: {res['input_tokens']}")
        print(f"  Output Tokens: {res['output_tokens']}")
        print(f"  Total Tokens: {res['total_tokens']}")

        print("\nEstimated Cost:")
        print(
            f"  Input Cost:  ${costs['input_cost']:.6f} (estimated at ${input_price}/1k tokens)"
        )
        print(
            f"  Output Cost: ${costs['output_cost']:.6f} (estimated at ${output_price}/1k tokens)"
        )
        print(f"  Total Cost:  ${costs['total_cost']:.6f} (estimated)")

        print("\nContext Limit:")
        print(f"  Used: {res['input_tokens']} tokens")
        print(f"  Maximum: {max_limit} tokens")
        print_separator()

    # 4. Demonstrate Context Window Truncation
    print("\n=== DEMONSTRATING CONTEXT WINDOW TRUNCATION ===")
    print_separator()
    small_limit = 140
    test_query = "What is the return period?"
    print(f"Query: \"{test_query}\"")
    print(f"Simulating a very strict Context Limit of: {small_limit} tokens...")

    res_trunc = response_service.generate(
        test_query, policies, max_context_limit=small_limit
    )

    print(f"\nContext Truncated: {res_trunc['context_truncated']}")
    print(
        f"Context Used Size: {len(res_trunc['context_used'].split())} words "
        f"(Original policy size: {len(policies.split())} words)"
    )
    print(f"Answer: {res_trunc['answer']}")
    print_separator()

    # 5. Demonstrate Message History Management
    print("\n=== DEMONSTRATING MESSAGE HISTORY TRIMMING ===")
    print_separator()
    history = ConversationHistory()
    system_prompt = "You are a helpful assistant."

    history.add_message("user", "Hello! I am a seller.")
    history.add_message(
        "assistant", "Hi there! How can I help you with your store today?"
    )
    history.add_message("user", "I need help with packaging guidelines.")
    history.add_message(
        "assistant", "Sure, all items must be in original secure packaging."
    )

    print("Original History:")
    for msg in history.get_messages():
        print(f"  [{msg['role'].upper()}]: {msg['content']}")

    history_limit = 45
    new_query = "What is the shipping cost?"
    trimmed_prompt = history.trim_history(
        max_tokens=history_limit,
        system_prompt=system_prompt,
        token_counter=get_token_count,
        new_query=new_query,
    )

    print(
        f"\nTrimmed Prompt Messages (Limit: {history_limit} tokens, preserving system prompt & new query):"
    )
    for msg in trimmed_prompt:
        print(f"  [{msg['role'].upper()}]: {msg['content']}")
    print()

    # 6. Demonstrate Embedding Generation and Cosine Similarity
    print("=== DEMONSTRATING EMBEDDINGS AND VECTOR REPRESENTATIONS ===")
    print_separator()
    embed_service = EmbeddingService()

    # Define test queries
    query_base = "What is the return period?"
    query_similar = "How long is the return window?"
    query_unrelated = "The seller must respond within 24 hours."

    print(f"Base Text:      \"{query_base}\"")
    print(f"Similar Text:   \"{query_similar}\"")
    print(f"Unrelated Text: \"{query_unrelated}\"")
    print()

    # Generate embeddings
    emb_base = embed_service.generate_embedding(query_base)
    emb_similar = embed_service.generate_embedding(query_similar)
    emb_unrelated = embed_service.generate_embedding(query_unrelated)

    # Print dimensions and vector preview
    print(f"Embedding Model: {embed_service.model}")
    print(f"Vector Dimensions: {len(emb_base)}")
    print(f"Vector Preview (first 5 elements): {emb_base[:5]}")
    print()

    # Calculate similarities
    sim_similar = embed_service.cosine_similarity(emb_base, emb_similar)
    sim_unrelated = embed_service.cosine_similarity(emb_base, emb_unrelated)

    print(f"Cosine Similarity (Base <-> Similar):   {sim_similar:.6f}")
    print(f"Cosine Similarity (Base <-> Unrelated): {sim_unrelated:.6f}")
    print()
    
    if sim_similar > sim_unrelated:
        print("Success: Similar texts have a higher similarity score than unrelated texts!")
    else:
        print("Failure: Similarity scores do not align with semantic similarity.")
    print_separator()

    print()
    print("PolicyPilot foundation is running successfully.")
    print("=" * 65)


if __name__ == "__main__":
    main()
