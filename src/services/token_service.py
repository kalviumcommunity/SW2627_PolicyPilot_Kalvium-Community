"""Token counting and cost estimation services for PolicyPilot."""

import tiktoken
from typing import Dict

DEFAULT_ENCODING = "cl100k_base"


def get_token_count(text: str, model_or_encoding: str = DEFAULT_ENCODING) -> int:
    """Count tokens in a string using tiktoken.

    If tiktoken is not available or fails, falls back to a word-split estimation.
    """
    if not text:
        return 0
    try:
        if model_or_encoding.startswith("gpt-") or model_or_encoding in [
            "text-embedding-ada-002"
        ]:
            try:
                encoding = tiktoken.encoding_for_model(model_or_encoding)
            except KeyError:
                encoding = tiktoken.get_encoding(DEFAULT_ENCODING)
        else:
            try:
                encoding = tiktoken.get_encoding(model_or_encoding)
            except ValueError:
                encoding = tiktoken.get_encoding(DEFAULT_ENCODING)
        return len(encoding.encode(text))
    except Exception:
        # Fallback split-based token count estimation (approx. 1.3 words per token)
        return int(len(text.split()) * 1.3) + 1


def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    input_price_per_1k: float = 0.0015,
    output_price_per_1k: float = 0.0020,
) -> Dict[str, float]:
    """Calculate approximately:

    input_cost = input_tokens /  * in1000put_price_per_1k
    output_cost = output_tokens / 1000 * output_price_per_1k
    total_cost = input_cost + output_cost
    """
    input_cost = (input_tokens / 1000.0) * input_price_per_1k
    output_cost = (output_tokens / 1000.0) * output_price_per_1k
    total_cost = input_cost + output_cost

    return {
        "input_cost": round(input_cost, 6),
        "output_cost": round(output_cost, 6),
        "total_cost": round(total_cost, 6),
    }
