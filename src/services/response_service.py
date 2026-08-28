"""Language-model response generation and prompt engineering services for PolicyPilot."""

import os
from typing import Dict, Any, List
from openai import OpenAI
from src.services.token_service import get_token_count

SYSTEM_PROMPT_TEMPLATE = (
    "You are PolicyPilot, an internal e-commerce support chatbot for customers and sellers. "
    "Your sole task is to answer user questions accurately using the provided policy context below. "
    "Rules:\n"
    "1. Answer ONLY using the provided policy/context.\n"
    "2. Avoid inventing information or making assumptions.\n"
    "3. If the answer is not specified in the provided context or if you are unsure, reply strictly with: "
    "'I am unable to answer this question as it is not specified in the official policy guidelines.'\n"
    "4. Keep your response concise (maximum 2 sentences).\n"
    "5. Prefer exact policy information over general assumptions."
)


class ResponseService:
    """Generate an answer using retrieved context and prompt engineering."""

    def __init__(self, system_prompt: str = SYSTEM_PROMPT_TEMPLATE):
        self.system_prompt = system_prompt
        # Load API keys if present
        self.api_base_url = os.getenv("API_BASE_URL")
        self.api_key = os.getenv("API_KEY")
        self.model = os.getenv("CHAT_MODEL", "gpt-3.5-turbo")

        self.client = None
        if self.api_base_url and self.api_key:
            try:
                self.client = OpenAI(
                    base_url=self.api_base_url, api_key=self.api_key
                )
            except Exception:
                self.client = None

    def construct_prompt(self, query: str, context: str) -> List[Dict[str, str]]:
        """Construct the prompt messages using system, user, and context roles."""
        user_content = f"Context:\n{context}\n\nQuestion: {query}"
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_content},
        ]

    def simulate_response(self, query: str, context: str) -> str:
        """Simulate LLM responses grounded strictly in the policies (local offline fallback)."""
        query_lower = query.lower()
        context_lower = context.lower() if context else ""
        fallback = "I am unable to answer this question as it is not specified in the official policy guidelines."

        if not context_lower:
            return fallback

        if "return period" in query_lower or "how long" in query_lower:
            if "return period" in context_lower and "30 days" in context_lower:
                return "The return period for standard catalog items is 30 days from the delivery date."
            return fallback

        if "damaged" in query_lower:
            if "damaged" in context_lower and "48 hours" in context_lower:
                return "You can return a damaged product if you report the damage and initiate the return within 48 hours of delivery."
            return fallback

        if "refund conditions" in query_lower or "conditions" in query_lower:
            if (
                "refund conditions" in context_lower
                and "original packaging" in context_lower
            ):
                return "Refund conditions require products to be in original packaging, unused, and with tags intact. Refunds are processed in 5-7 business days."
            return fallback

        if "seller" in query_lower or "responsibilities" in query_lower:
            if "seller" in context_lower and "2 business days" in context_lower:
                return "Seller responsibilities include dispatching orders within 2 business days, guaranteeing product authenticity, and responding to inquiries within 24 hours."
            return fallback

        return fallback

    def generate(
        self, query: str, context: str, max_context_limit: int = 1000
    ) -> Dict[str, Any]:
        """Generate a grounded policy response, performing context size limit checks.

        Returns a dictionary with the answer and detailed token usage/costs.
        """
        system_tokens = get_token_count(self.system_prompt)
        query_tokens = get_token_count(query)
        # Allocate minor token overhead for conversational template structure
        fixed_tokens = system_tokens + query_tokens + 20

        context_tokens = get_token_count(context)
        context_truncated = False
        final_context = context

        # Check context limits and truncate context if exceeded
        if fixed_tokens + context_tokens > max_context_limit:
            context_truncated = True
            words = context.split()
            while len(words) > 0:
                final_context = " ".join(words)
                current_total = fixed_tokens + get_token_count(final_context)
                if current_total <= max_context_limit:
                    break
                words.pop()
            if not words:
                final_context = ""

        # Build prompt messages
        messages = self.construct_prompt(query, final_context)
        input_tokens = fixed_tokens + get_token_count(final_context)

        answer = ""
        simulated = True

        # Run completion using API or offline simulation
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model=self.model, messages=messages, temperature=0.0
                )
                answer = response.choices[0].message.content
                simulated = False
            except Exception:
                # If API call fails, fallback to local simulation
                answer = self.simulate_response(query, final_context)
        else:
            answer = self.simulate_response(query, final_context)

        output_tokens = get_token_count(answer)

        return {
            "answer": answer,
            "context_used": final_context,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "context_truncated": context_truncated,
            "simulated": simulated,
        }