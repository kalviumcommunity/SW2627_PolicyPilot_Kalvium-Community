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
