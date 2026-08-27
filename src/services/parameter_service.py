"""Model parameters service for PolicyPilot RAG Assistant.

Manages completion hyper-parameters (temperature, max_tokens, top_p, stop sequences)
and runs comparative parameter experiments for grounded factual task tuning.
"""

from typing import Any, Dict, List, Optional
from src.services.prompt_service import get_constrained_prompt


def get_grounded_config() -> Dict[str, Any]:
    """Return recommended model decoding parameters for factual/grounded RAG tasks.

    Returns:
        Dict of parameter names and values optimized for determinism and factual reliability.
    """
    return {
        "temperature": 0.0,
        "max_tokens": 150,
        "top_p": 0.1,
        "stop": None,
    }


def prepare_completion_payload(
    messages: List[Dict[str, str]],
    model: str,
    temperature: float = 0.0,
    max_tokens: Optional[int] = 150,
    top_p: Optional[float] = None,
    stop: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Construct standard request parameters dictionary for OpenAI Chat Completions API."""
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }

    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if top_p is not None:
        payload["top_p"] = top_p
    if stop is not None:
        payload["stop"] = stop

    return payload


def clean_answer(answer: str) -> str:
    """Remove CoT reasoning tags <think>...</think> if present in model output."""
    if not answer:
        return ""
    if "<think>" in answer:
        if "</think>" in answer:
            answer = answer.split("</think>", 1)[1]
        else:
            answer = answer.replace("<think>", "")
    return answer.replace("```text", "").replace("```", "").strip()


def execute_completion_with_params(
    client: Any,
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.0,
    max_tokens: Optional[int] = 150,
    top_p: Optional[float] = None,
    stop: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Execute LLM chat completion request with specific decoding parameters."""
    payload = prepare_completion_payload(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        stop=stop,
    )

    response = client.chat.completions.create(**payload)
    choice = response.choices[0]

    raw_content = choice.message.content or ""
    cleaned_content = clean_answer(raw_content)

    usage_dict = {}
    if hasattr(response, "usage") and response.usage:
        usage_dict = {
            "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
            "completion_tokens": getattr(response.usage, "completion_tokens", 0),
            "total_tokens": getattr(response.usage, "total_tokens", 0),
        }

    return {
        "content": cleaned_content if cleaned_content else raw_content,
        "raw_content": raw_content,
        "finish_reason": getattr(choice, "finish_reason", "stop"),
        "usage": usage_dict,
        "params": {
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "stop": stop,
        },
    }
