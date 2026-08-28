"""Prompt construction and management service for PolicyPilot RAG Assistant.

Uses centralized prompt templates from prompt_templates.py for consistency.
This ensures that prompt changes apply across all features (chat, CLI, comparison, etc.)
without editing multiple copies.

Provides:
- Vague prompt for comparison/testing
- Strict grounded prompt for PolicyPilot
- Strict JSON prompt for structured testing
- Protection against hallucination and <think> output
"""

import re
from typing import Any, Dict, List

from src.services.prompt_templates import TemplateRenderer, FALLBACK_RESPONSE


# ============================================================================
# PROMPT CONSTRUCTION API (using TemplateRenderer)
# ============================================================================

def get_vague_prompt(user_query: str) -> List[Dict[str, str]]:
    """Build a vague/unconstrained prompt for comparison.

    Uses the 'system_vague' and 'user_simple' templates from the
    centralized template registry.
    """
    return TemplateRenderer.render_messages(
        system_template="system_vague",
        user_template="user_simple",
        question=user_query,
    )


def get_constrained_prompt(
    user_query: str,
    context: str = "",
) -> List[Dict[str, str]]:
    """Build a strict, grounded PolicyPilot prompt.

    Uses the 'system_constrained' and 'user_with_context' templates
    from the centralized template registry.
    """
    return TemplateRenderer.render_messages(
        system_template="system_constrained",
        user_template="user_with_context",
        context=context,
        question=user_query,
        fallback_response=FALLBACK_RESPONSE,
    )


def get_json_constrained_prompt(
    user_query: str,
    context: str = "",
) -> List[Dict[str, str]]:
    """Build a strict JSON PolicyPilot prompt.

    Uses the 'system_json_constrained' and 'user_with_context' templates
    from the centralized template registry.
    """
    return TemplateRenderer.render_messages(
        system_template="system_json_constrained",
        user_template="user_with_context",
        context=context,
        question=user_query,
        fallback_response=FALLBACK_RESPONSE,
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