"""Prompt construction and management service for PolicyPilot RAG Assistant.

Provides:
- Vague prompt for comparison/testing
- Strict grounded prompt for PolicyPilot
- Strict JSON prompt for structured testing
- Protection against hallucination and <think> output
"""

import re
from typing import Any, Dict, List


FALLBACK_RESPONSE = (
    "I am unable to answer this question as it is not specified in the official policy guidelines."
)


# ---------------------------------------------------------------------------
# STRICT POLICY PROMPT
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_CONSTRAINED = f"""
You are PolicyPilot, an internal company policy assistant.

Your ONLY job is to answer questions using the official policy information
provided in the retrieved context.

STRICT RULES:

1. Use ONLY the information contained in the retrieved policy context.
2. If the retrieved policy context contains enough information to answer the
   question, answer the question directly and concisely.
3. If the retrieved policy context does NOT contain enough information to
   answer the question, reply EXACTLY with:
   "{FALLBACK_RESPONSE}"
4. If the question is unrelated to company policy, reply EXACTLY with the
   same fallback response.
5. NEVER use general knowledge, outside information, assumptions, common
   corporate practices, or guesses.
6. NEVER invent or infer missing policy details.
7. NEVER provide an answer just because something is generally true in
   other companies.
8. Do not recommend HR, Google, websites, handbooks, or other sources when
   the required information is missing.
9. Do not mention the retrieved context in the final answer.
10. Do not reveal your reasoning or internal thought process.
11. NEVER output <think>, </think>, analysis, reasoning, self-correction,
    or planning text.
12. Keep valid answers concise, factual, and professional.
13. Return ONLY the final answer. Do not add headings, labels, explanations,
    or extra commentary.

The retrieved policy context will be provided with each user question.
"""


# ---------------------------------------------------------------------------
# VAGUE PROMPT
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_VAGUE = "You are a helpful assistant."


# ---------------------------------------------------------------------------
# STRICT JSON PROMPT
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_JSON_FORMAT = f"""
You are PolicyPilot, an internal company policy assistant.

Your ONLY job is to answer questions using the official policy information
provided in the retrieved context.

STRICT RULES:

1. Use ONLY the retrieved policy context.
2. If the context contains enough information to answer the question,
   provide the answer using ONLY that information.
3. If the context does not contain enough information, use exactly:
   "{FALLBACK_RESPONSE}"
4. If the question is unrelated to company policy, use exactly the same
   fallback response.
5. NEVER use general knowledge or outside information.
6. NEVER guess or infer missing policy information.
7. NEVER invent company policies.
8. Do not reveal reasoning or internal thought processes.
9. NEVER output <think> or </think>.
10. Return ONLY valid JSON.
11. Do not use markdown code fences.

Required JSON schema:

{{
    "answer": "<string>",
    "confidence": "<high|medium|low|unknown>",
    "refusal": <true|false>
}}

For a supported question:
- "answer" = concise answer based only on the retrieved context.
- "confidence" = "high" when the context directly supports the answer.
- "refusal" = false.

For an unsupported or unrelated question:
- "answer" = "{FALLBACK_RESPONSE}"
- "confidence" = "unknown"
- "refusal" = true.
"""


# ---------------------------------------------------------------------------
# MESSAGE BUILDER
# ---------------------------------------------------------------------------

def build_messages(
    system_content: str,
    user_content: str,
) -> List[Dict[str, str]]:
    """Construct system and user messages."""

    return [
        {
            "role": "system",
            "content": system_content.strip(),
        },
        {
            "role": "user",
            "content": user_content.strip(),
        },
    ]


# ---------------------------------------------------------------------------
# PROMPT VARIATIONS
# ---------------------------------------------------------------------------

def get_vague_prompt(user_query: str) -> List[Dict[str, str]]:
    """Build a vague/unconstrained prompt for comparison."""

    return build_messages(
        system_content=SYSTEM_PROMPT_VAGUE,
        user_content=user_query,
    )


def get_constrained_prompt(
    user_query: str,
    context: str = "",
) -> List[Dict[str, str]]:
    """Build a strict, grounded PolicyPilot prompt."""

    user_content = f"""
Retrieved policy context:
{context}

User question:
{user_query}
"""

    return build_messages(
        system_content=SYSTEM_PROMPT_CONSTRAINED,
        user_content=user_content,
    )


def get_json_constrained_prompt(
    user_query: str,
    context: str = "",
) -> List[Dict[str, str]]:
    """Build a strict JSON PolicyPilot prompt."""

    user_content = f"""
Retrieved policy context:
{context}

User question:
{user_query}
"""

    return build_messages(
        system_content=SYSTEM_PROMPT_JSON_FORMAT,
        user_content=user_content,
    )


# ---------------------------------------------------------------------------
# PROMPT COMPARISON
# ---------------------------------------------------------------------------

def compare_prompt_structures(user_query: str) -> Dict[str, Any]:
    """Return structural comparison of vague vs constrained prompts."""

    vague_messages = get_vague_prompt(user_query)
    constrained_messages = get_constrained_prompt(user_query)

    return {
        "user_query": user_query,

        "variation_1_vague": {
            "system_prompt": vague_messages[0]["content"],
            "user_prompt": vague_messages[1]["content"],
            "characteristics": [
                "Vague system role",
                "No defined policy scope",
                "No grounding requirement",
                "No hallucination protection",
                "No refusal fallback",
            ],
        },

        "variation_2_constrained": {
            "system_prompt": constrained_messages[0]["content"],
            "user_prompt": constrained_messages[1]["content"],
            "characteristics": [
                "Clear PolicyPilot persona",
                "Strict policy-only scope",
                "Uses retrieved context",
                "No general knowledge",
                "No guessing",
                "No hallucination",
                "Strict fallback response",
                "No reasoning output",
                "Maximum concise response",
            ],
        },
    }


# ---------------------------------------------------------------------------
# RESPONSE CLEANING
# ---------------------------------------------------------------------------

def clean_response(response: str) -> str:
    """Remove accidental reasoning/thinking tags from model output."""

    if not response:
        return ""

    # Remove <think>...</think>
    response = re.sub(
        r"<think>.*?</think>",
        "",
        response,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # Remove stray thinking tags
    response = re.sub(
        r"</?think>",
        "",
        response,
        flags=re.IGNORECASE,
    )

    return response.strip()


# ---------------------------------------------------------------------------
# API EXECUTION
# ---------------------------------------------------------------------------

def execute_prompt(
    client: Any,
    model: str,
    messages: List[Dict[str, str]],
) -> str:
    """Execute a chat completion request and return clean final answer."""

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
    )

    answer = response.choices[0].message.content or ""

    return clean_response(answer)