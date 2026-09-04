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
from src.services.similarity_service import SimilarityService
from src.services.batch_embedding_service import BatchEmbeddingService
from src.services.metadata_search_service import MetadataSearchService


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

    # 6. Demonstrate Embedding Generation and Vector Representations
    print("=== DEMONSTRATING EMBEDDINGS AND VECTOR REPRESENTATIONS ===")
    print_separator()
    embed_service = EmbeddingService()
    sim_service = SimilarityService(embedding_service=embed_service)

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

    # Calculate similarities using SimilarityService
    sim_similar = sim_service.cosine_similarity(emb_base, emb_similar)
    sim_unrelated = sim_service.cosine_similarity(emb_base, emb_unrelated)


    print(f"Cosine Similarity (Base <-> Similar):   {sim_similar:.6f}")
    print(f"Cosine Similarity (Base <-> Unrelated): {sim_unrelated:.6f}")
    print()
    
    if sim_similar > sim_unrelated:
        print("Success: Similar texts have a higher similarity score than unrelated texts!")
    else:
        print("Failure: Similarity scores do not align with semantic similarity.")
    print_separator()

    # 7. Demonstrate Similarity Ranking and Chunk Retrieval
    print("\n=== DEMONSTRATING SIMILARITY RANKING & RETRIEVAL ===")
    print_separator()

    sample_chunks = [
        {
            "chunk_index": 0,
            "source": "ACCOUNT_SECURITY_POLICY",
            "content": (
                "To reset your password, click 'Forgot Password' on the login page, "
                "enter your registered email address, and follow the password reset link "
                "sent to your inbox."
            ),
        },
        {
            "chunk_index": 1,
            "source": "LEARNER_PORTAL_GUIDELINES",
            "content": (
                "Learners can access online course materials, lecture recordings, "
                "and track assignment submission deadlines directly from the student dashboard."
            ),
        },
        {
            "chunk_index": 2,
            "source": "RETURN_AND_REFUND_POLICY",
            "content": (
                "Customers can request a refund for eligible catalog items within 30 days "
                "of delivery. All items must be unused and in original packaging."
            ),
        },
    ]

    sample_query = "How can a learner reset their password?"
    print(f"Sample Query: \"{sample_query}\"")
    print(f"Total Candidate Chunks: {len(sample_chunks)}\n")

    ranked_chunks = retrieval_service.retrieve_ranked_chunks(
        sample_query, sample_chunks
    )

    print("Ranked Results (Descending Similarity):")
    for rank, chunk in enumerate(ranked_chunks, start=1):
        print(f"  Rank #{rank}:")
        print(f"    Similarity Score : {chunk['similarity_score']:.6f}")
        print(f"    Source Policy    : {chunk['source']}")
        print(f"    Chunk Index      : {chunk['chunk_index']}")
        print(f"    Content Snippet  : \"{chunk['content'][:80]}...\"")
        print()

    most_relevant = ranked_chunks[0]
    least_relevant = ranked_chunks[-1]

    print("Similarity Highlights:")
    print(
        f"  [MOST RELEVANT]  Score: {most_relevant['similarity_score']:.6f} | "
        f"Source: {most_relevant['source']} (Chunk #{most_relevant['chunk_index']})"
    )
    print(f"                   Snippet: \"{most_relevant['content']}\"")
    print(
        f"  [LEAST RELEVANT] Score: {least_relevant['similarity_score']:.6f} | "
        f"Source: {least_relevant['source']} (Chunk #{least_relevant['chunk_index']})"
    )
    print(f"                   Snippet: \"{least_relevant['content']}\"")
    print_separator()

    # 8. Demonstrate Batch Embedding & Rate/Cost Management
    print("\n=== DEMONSTRATING BATCH EMBEDDING & RATE/COST MANAGEMENT ===")
    print_separator()
    batch_service = BatchEmbeddingService(batch_size=2)

    batch_chunks = [
        {
            "chunk_index": 0,
            "source": "SHIPPING_POLICY",
            "content": "Standard delivery takes 3 to 5 business days for standard orders.",
        },
        {
            "chunk_index": 1,
            "source": "SHIPPING_POLICY",
            "content": "Expedited shipping guarantees delivery within 24 to 48 hours.",
        },
        {
            "chunk_index": 2,
            "source": "PAYMENT_POLICY",
            "content": "We accept major credit cards, debit cards, and digital wallet payments.",
        },
        {
            "chunk_index": 3,
            "source": "CANCELLATION_POLICY",
            "content": "Orders can be canceled within 2 hours of placement before dispatch.",
        },
    ]

    print(f"Initial Chunks Count: {len(batch_chunks)}")
    print("Processing initial batch embedding run...")
    metrics1 = batch_service.process_chunks(batch_chunks)

    print("\nInitial Run Metrics:")
    print(f"  Total Chunks    : {metrics1['total_chunks']}")
    print(f"  Skipped Chunks  : {metrics1['skipped_chunks']}")
    print(f"  Embedded Chunks : {metrics1['embedded_chunks']}")
    print(f"  Failed Chunks   : {metrics1['failed_chunks']}")
    print(f"  Input Tokens    : {metrics1['input_tokens']}")
    print(f"  Estimated Cost  : ${metrics1['estimated_cost']:.6f}")

    print("\nDemonstrating Resumability (re-running on same chunk list)...")
    metrics2 = batch_service.process_chunks(batch_chunks)

    print("\nResumed Run Metrics:")
    print(f"  Total Chunks    : {metrics2['total_chunks']}")
    print(
        f"  Skipped Chunks  : {metrics2['skipped_chunks']} (all previously embedded chunks skipped)"
    )
    print(f"  Embedded Chunks : {metrics2['embedded_chunks']}")
    print(f"  Failed Chunks   : {metrics2['failed_chunks']}")
    print(f"  Input Tokens    : {metrics2['input_tokens']}")
    print(f"  Estimated Cost  : ${metrics2['estimated_cost']:.6f}")
    print_separator()

    # 9. Demonstrate Metadata Filtering & Hybrid Search
    print("\n=== DEMONSTRATING METADATA FILTERING & HYBRID SEARCH ===")
    print_separator()
    metadata_service = MetadataSearchService()

    meta_chunks = [
        {
            "chunk_index": 0,
            "source": "ACCOUNT_SECURITY_POLICY",
            "section": "Account access",
            "content": "To reset your password, click 'Forgot Password' on the login page, enter your registered email address, and follow the password reset link sent to your inbox.",
        },
        {
            "chunk_index": 1,
            "source": "LEARNER_PORTAL_GUIDELINES",
            "section": "Student dashboard",
            "content": "Learners can access online course materials, lecture recordings, and track assignment submission deadlines directly from the student dashboard.",
        },
        {
            "chunk_index": 2,
            "source": "RETURN_AND_REFUND_POLICY",
            "section": "Refund conditions",
            "content": "Customers can request a refund for eligible catalog items within 30 days of delivery. All items must be in original packaging.",
        },
    ]

    target_query = "What are the password reset steps?"
    print(f"Query: \"{target_query}\"\n")

    # A. Unfiltered Retrieval
    print("--- 1. Unfiltered Retrieval (all candidate chunks) ---")
    unfiltered_results = metadata_service.search(target_query, meta_chunks, metadata_filter=None)
    for idx, item in enumerate(unfiltered_results, 1):
        print(f"  Result #{idx}:")
        print(f"    Similarity Score : {item.get('similarity_score', 0.0):.6f}")
        print(f"    Source           : {item.get('source')}")
        print(f"    Section          : {item.get('section')}")
        print(f"    Chunk Content    : \"{item.get('content')[:75]}...\"")
        print()

    # B. Filtered Retrieval
    filter_dict = {"section": "Account access"}
    print(f"--- 2. Filtered Retrieval (filter: {filter_dict}) ---")
    filtered_results = metadata_service.search(target_query, meta_chunks, metadata_filter=filter_dict)
    for idx, item in enumerate(filtered_results, 1):
        print(f"  Result #{idx}:")
        print(f"    Similarity Score : {item.get('similarity_score', 0.0):.6f}")
        print(f"    Source           : {item.get('source')}")
        print(f"    Section          : {item.get('section')}")
        print(f"    Chunk Content    : \"{item.get('content')[:75]}...\"")
        print()

    # C. Hybrid Search (Vector Similarity + Keyword Score)
    print("--- 3. Hybrid Search (Vector Weight: 0.8 | Keyword Weight: 0.2) ---")
    hybrid_results = metadata_service.search(
        target_query,
        meta_chunks,
        metadata_filter=None,
        enable_hybrid=True,
        vector_weight=0.8,
        keyword_weight=0.2,
    )
    for idx, item in enumerate(hybrid_results, 1):
        print(f"  Result #{idx}:")
        print(f"    Hybrid Score     : {item.get('hybrid_score', 0.0):.6f}")
        print(f"    Vector Score     : {item.get('similarity_score', 0.0):.6f}")
        print(f"    Keyword Score    : {item.get('keyword_score', 0.0):.6f}")
        print(f"    Source           : {item.get('source')}")
        print(f"    Section          : {item.get('section')}")
        print(f"    Chunk Content    : \"{item.get('content')[:75]}...\"")
        print()
    print_separator()

    print()
    print("PolicyPilot foundation is running successfully.")
    print("=" * 65)


if __name__ == "__main__":
    main()

