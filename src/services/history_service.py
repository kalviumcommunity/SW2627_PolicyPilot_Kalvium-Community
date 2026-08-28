"""Conversation history management service for PolicyPilot."""

from typing import List, Dict, Callable


class ConversationHistory:
    """Manages chat message history and prunes old turns to fit within context limits."""

    def __init__(self):
        self.messages: List[Dict[str, str]] = []

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the history."""
        self.messages.append({"role": role, "content": content})

    def get_messages(self) -> List[Dict[str, str]]:
        """Get the current list of messages."""
        return self.messages

    def clear(self) -> None:
        """Clear message history."""
        self.messages = []

    def trim_history(
        self,
        max_tokens: int,
        system_prompt: str,
        token_counter: Callable[[str], int],
        new_query: str = "",
    ) -> List[Dict[str, str]]:
        """Limit message history based on token count.

        Preserves the system prompt and the new query, trimming the oldest
        user-assistant message pairs if the total token count exceeds the limit.
        """
        system_tokens = token_counter(system_prompt)
        query_tokens = token_counter(new_query)
        base_tokens = system_tokens + query_tokens

        # If system + new query alone exceeds the limit, return just system prompt
        if base_tokens >= max_tokens:
            return [{"role": "system", "content": system_prompt}]

        # Filter out system messages from history to avoid duplicates
        history_turns = [m for m in self.messages if m["role"] != "system"]

        # Keep removing oldest messages in pairs until token count fits within limits
        while len(history_turns) > 0:
            history_content = " ".join([m["content"] for m in history_turns])
            history_tokens = token_counter(history_content)

            if base_tokens + history_tokens <= max_tokens:
                break

            # Remove oldest turn (user + assistant pair)
            if len(history_turns) >= 2:
                history_turns = history_turns[2:]
            else:
                history_turns = []

        final_messages = [{"role": "system", "content": system_prompt}]
        final_messages.extend(history_turns)
        return final_messages
