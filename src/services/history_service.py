"""Context windows and conversation history management services for PolicyPilot RAG Assistant.

Includes token counting, trimming old turns, and summarization strategies.
"""

import logging
from typing import Dict, List, Any
from tokenizers import Tokenizer

# Configure logging
logger = logging.getLogger(__name__)

# Global tokenizer instance loaded from HuggingFace Hub
_tokenizer = None
try:
    _tokenizer = Tokenizer.from_pretrained("gpt2")
except Exception as e:
    logger.warning("Failed to load Hugging Face BPE tokenizer, using fallback approximation: %s", e)


def count_tokens(text: str) -> int:
    """Compute the number of tokens in a string.
    
    Uses BPE tokenizer (gpt2) if available, otherwise falls back to a 
    word/character length approximation.
    """
    if not text:
        return 0
        
    if _tokenizer:
        try:
            return len(_tokenizer.encode(text).ids)
        except Exception as e:
            logger.debug("Tokenization failed, using word-based approximation: %s", e)
            
    # Fallback approximation: 
    # Words in English are on average 1.3 tokens. Characters are about 4 per token.
    words = text.split()
    return max(1, int(len(words) * 1.3) + 1)


def total_tokens(messages: List[Dict[str, str]]) -> int:
    """Compute the total token count of a message list.
    
    Sums the token count of each message's content.
    """
    return sum(count_tokens(m.get("content", "")) for m in messages)


def trim(messages: List[Dict[str, str]], budget: int = 6000) -> None:
    """Trim oldest messages when the history exceeds the token budget.
    
    Always preserves the system message (assumed to be at index 0).
    Removes the oldest non-system turn (at index 1) until the total token 
    count is under the budget.
    """
    initial_tokens = total_tokens(messages)
    if initial_tokens <= budget:
        return
        
    logger.info("Current tokens (%d) exceed budget (%d). Trimming oldest turns...", initial_tokens, budget)
    
    # System message is at index 0. The oldest non-system message is at index 1.
    # Keep at least the system message and one user/assistant response (len > 2)
    while total_tokens(messages) > budget and len(messages) > 2:
        removed = messages.pop(1)
        logger.info("Dropped old message: [%s] '%.40s...'", removed.get("role"), removed.get("content", ""))
        
    final_tokens = total_tokens(messages)
    logger.info("Trimming complete. Final token count: %d", final_tokens)


def summarize_history(
    messages: List[Dict[str, str]], 
    client: Any, 
    model: str, 
    budget: int = 6000, 
    keep_turns: int = 2
) -> List[Dict[str, str]]:
    """Summarize older messages when the history exceeds the token budget.
    
    Always preserves the system message at index 0.
    Summarizes all turns except the last `keep_turns` (active context), 
    and replaces them with a single system summary message.
    
    Falls back to trimming if summarization fails or there are too few messages.
    """
    initial_tokens = total_tokens(messages)
    if initial_tokens <= budget:
        return messages
        
    logger.info("Current tokens (%d) exceed budget (%d). Summarizing oldest turns...", initial_tokens, budget)
    
    # We need: 1 system prompt, at least 1 message to summarize, and keep_turns * 2 active messages
    keep_count = keep_turns * 2
    if len(messages) <= keep_count + 2:
        logger.warning("Too few messages to summarize. Falling back to trimming.")
        trim(messages, budget)
        return messages
        
    system_msg = messages[0]
    to_summarize = messages[1:-keep_count]
    active_msgs = messages[-keep_count:]
    
    # Format conversation history for the summarizer model
    conversation_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in to_summarize
    )
    
    summary_prompt = (
        "Summarize the following conversation history concisely in a single paragraph. "
        "Preserve key facts, user requests, and assistant answers:\n\n"
        f"{conversation_text}"
    )
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes conversation histories concisely."},
                {"role": "user", "content": summary_prompt}
            ],
            max_tokens=150,
            temperature=0.3
        )
        summary_text = response.choices[0].message.content.strip()
        logger.info("Generated conversation summary: '%s'", summary_text)
    except Exception as e:
        logger.error("Failed to generate summary, falling back to trimming: %s", e)
        trim(messages, budget)
        return messages
        
    # Replace summarized messages with a single system summary turn
    summary_message = {
        "role": "system",
        "content": f"Summary of previous conversation: {summary_text}"
    }
    
    # Reconstruct messages list in-place
    new_messages = [system_msg, summary_message] + active_msgs
    
    # If the history is still over the budget, we trim active messages (excluding system and summary)
    while total_tokens(new_messages) > budget and len(new_messages) > 3:
        # Index 0 is system, index 1 is summary. Pop the oldest active message at index 2.
        new_messages.pop(2)
        
    messages.clear()
    messages.extend(new_messages)
    
    logger.info("Summarization complete. Final token count: %d", total_tokens(messages))
    return messages
