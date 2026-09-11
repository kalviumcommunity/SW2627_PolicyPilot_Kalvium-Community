"""Prompt construction and management service for PolicyPilot RAG Assistant.

Demonstrates role separation (system vs user), system message constraints (role,
scope, length, tone, fallback), and prompt variation comparison.
"""

from typing import Any, Dict, List, Optional


SYSTEM_PROMPT_CONSTRAINED = (
    "You are PolicyPilot, an internal support assistant for staff policy questions. "
    "Your sole task is to answer staff questions accurately using official company policy guidelines. "
    "Scope & Boundaries: Do not answer non-policy questions or speculate beyond official guidelines. "
    "Format & Tone: Keep your response concise (maximum 2 sentences). Maintain a direct, factual, and professional tone. "
    "Fallback Rule: If the requested information is not specified in the official guidelines or if you are unsure, "
    "reply strictly with: 'I am unable to answer this question as it is not specified in the official policy guidelines.'"
)

SYSTEM_PROMPT_VAGUE = "You are a helpful assistant."

SYSTEM_PROMPT_JSON_FORMAT = (
    "You are PolicyPilot, an internal support assistant for staff policy questions. "
    "Answer staff questions based on official guidelines. "
    "Format Constraint: Reply strictly with ONLY a valid JSON object in the following schema: "
    '{"answer": "<string>", "confidence": "<high|medium|low|unknown>", "refusal": <true|false>}. '
    "Do not include markdown code block ticks or conversational text outside the JSON."
)


def build_messages(system_content: str, user_content: str) -> List[Dict[str, str]]:
    """Construct a message list with distinct system and user roles.

    Args:
        system_content: Instructions defining assistant identity, scope, constraints, and fallback.
        user_content: The user's query or turn task.

    Returns:
        A list of role-content message dictionaries expected by OpenAI-compatible Chat API.
    """
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def get_vague_prompt(user_query: str) -> List[Dict[str, str]]:
    """Build a vague/unconstrained prompt pair (Variation 1)."""
    return build_messages(
        system_content=SYSTEM_PROMPT_VAGUE,
        user_content=user_query,
    )


def get_constrained_prompt(user_query: str) -> List[Dict[str, str]]:
    """Build a clear, constrained, and grounded system prompt pair (Variation 2)."""
    return build_messages(
        system_content=SYSTEM_PROMPT_CONSTRAINED,
        user_content=user_query,
    )


def get_json_constrained_prompt(user_query: str) -> List[Dict[str, str]]:
    """Build a system prompt enforcing JSON output format."""
    return build_messages(
        system_content=SYSTEM_PROMPT_JSON_FORMAT,
        user_content=user_query,
    )


def compare_prompt_structures(user_query: str) -> Dict[str, Any]:
    """Return a structural comparison dictionary of vague vs constrained prompts."""
    vague_messages = get_vague_prompt(user_query)
    constrained_messages = get_constrained_prompt(user_query)

    return {
        "user_query": user_query,
        "variation_1_vague": {
            "system_prompt": vague_messages[0]["content"],
            "user_prompt": vague_messages[1]["content"],
            "characteristics": [
                "Vague system role ('helpful assistant')",
                "No defined scope or domain boundary",
                "No length or formatting constraints",
                "No refusal fallback mechanism for unknown policies",
            ],
        },
        "variation_2_constrained": {
            "system_prompt": constrained_messages[0]["content"],
            "user_prompt": constrained_messages[1]["content"],
            "characteristics": [
                "Clear persona ('PolicyPilot internal support assistant')",
                "Strict scope boundary (staff policy questions only)",
                "Explicit length constraint (max 2 sentences)",
                "Factual & professional tone directive",
                "Strict refusal fallback statement when information is missing",
            ],
        },
    }


def execute_prompt(client: Any, model: str, messages: List[Dict[str, str]]) -> str:
    """Execute a chat completion request using the provided client and messages."""
    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    return response.choices[0].message.content


# -------------------------------------------------------------
# Prompt Augmentation & Context Injection (Concept 3.36)
# -------------------------------------------------------------

import tiktoken

DEFAULT_MAX_CONTEXT_TOKENS = 5000


def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """Count tokens in a text string using tiktoken encoding."""
    if not text:
        return 0
    try:
        enc = tiktoken.get_encoding(encoding_name)
    except Exception:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text, disallowed_special=()))


def format_chunk(index: int, chunk: Dict[str, Any]) -> str:
    """Format a retrieved chunk with source and chunk index citation markers.

    Example Output:
        [1] account-guide.md#0
        How can a learner reset their password? Click Forgot Password...
    """
    metadata = chunk.get("metadata", {})
    source = metadata.get("source", "unknown_source")
    chunk_index = metadata.get("chunk_index", chunk.get("index", 0))
    marker = f"[{index}] {source}#{chunk_index}"
    text = chunk.get("text", "").strip()
    return f"{marker}\n{text}"


def assemble_context(
    chunks: List[Dict[str, Any]],
    max_context_tokens: int = DEFAULT_MAX_CONTEXT_TOKENS,
    encoding_name: str = "cl100k_base",
) -> tuple:
    """Assemble formatted retrieved chunks into a single context string within token budget.

    Args:
        chunks: List of retrieved chunk dictionaries.
        max_context_tokens: Maximum tokens allowed for the assembled context.
        encoding_name: Tiktoken encoding name (default: cl100k_base).

    Returns:
        tuple: (assembled_context_str, used_tokens_int, selected_chunks_metadata_list)
    """
    selected = []
    selected_meta = []
    used_tokens = 0

    for index, chunk in enumerate(chunks, start=1):
        formatted = format_chunk(index, chunk)
        token_count = count_tokens(formatted, encoding_name=encoding_name)

        # Account for delimiter tokens between chunks
        delimiter_tokens = count_tokens("\n\n---\n\n", encoding_name=encoding_name) if selected else 0

        if used_tokens + delimiter_tokens + token_count > max_context_tokens:
            break

        selected.append(formatted)
        meta = dict(chunk.get("metadata", {}))
        meta["citation_index"] = index
        selected_meta.append(meta)
        used_tokens += (delimiter_tokens + token_count)

    context_str = "\n\n---\n\n".join(selected)
    return context_str, used_tokens, selected_meta


def build_augmented_prompt(
    question: str,
    retrieved_chunks: List[Dict[str, Any]],
    max_context_tokens: int = DEFAULT_MAX_CONTEXT_TOKENS,
    encoding_name: str = "cl100k_base",
) -> Dict[str, Any]:
    """Construct an augmented grounded prompt separating instructions, context, and question.

    Instructs the model to answer strictly from the provided context with source citations,
    and fallback when information is missing.

    Args:
        question: The user query string.
        retrieved_chunks: List of retrieved evidence chunks.
        max_context_tokens: Token budget for injected context.
        encoding_name: Tokenizer encoding name.

    Returns:
        Dictionary containing:
            - prompt: Complete formatted prompt string.
            - messages: Role-separated OpenAI messages list.
            - context: Raw injected context string.
            - context_tokens: Tokens used by context.
            - total_prompt_tokens: Total tokens in prompt.
            - sources_used: List of metadata for chunks included in context.
            - num_chunks_included: Number of chunks within token budget.
            - total_chunks_provided: Total input chunks before budget cutoff.
    """
    context, context_tokens, sources_used = assemble_context(
        chunks=retrieved_chunks,
        max_context_tokens=max_context_tokens,
        encoding_name=encoding_name,
    )

    system_instruction = (
        "You are a grounded assistant. Answer the question using only the provided context. "
        "If the answer is not in the context, say: \"I don't have enough information in the provided context.\"\n"
        "When possible, cite sources using the markers like [1] or [2].\n"
        "Output ONLY the direct answer. Do not include thinking steps or preamble."
    )

    user_content = f"Context:\n{context}\n\nQuestion:\n{question}"

    prompt_str = f"{system_instruction}\n\n{user_content}"
    total_tokens = count_tokens(prompt_str, encoding_name=encoding_name)

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_content},
    ]

    return {
        "prompt": prompt_str,
        "messages": messages,
        "context": context,
        "context_tokens": context_tokens,
        "total_prompt_tokens": total_tokens,
        "sources_used": sources_used,
        "num_chunks_included": len(sources_used),
        "total_chunks_provided": len(retrieved_chunks),
    }


def build_prompt(question: str, retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build augmented prompt matching the standard signature."""
    return build_augmented_prompt(question=question, retrieved_chunks=retrieved_chunks)

