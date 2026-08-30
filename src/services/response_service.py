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
    "5. Prefer exact policy information over general assumptions.\n"
    "Format Constraint: Reply strictly with ONLY a valid JSON object. Do not include markdown code block ticks or conversational text outside the JSON. The JSON structure MUST be exactly:\n"
    '{\n'
    '  "answer": "<string>",\n'
    '  "source": "<string>"\n'
    '}\n'
    "The 'source' field MUST be the specific policy title or header extracted from the context (e.g., 'RETURN PERIOD POLICY', 'DAMAGED PRODUCT POLICY', 'REFUND CONDITIONS POLICY', or 'SELLER RESPONSIBILITIES POLICY') that was used to answer the question, or 'None' if no answer could be determined from the guidelines."
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

    def parse_and_validate_json(self, text: str) -> Dict[str, str]:
        """Safely parse and validate the JSON response.

        Returns a dictionary if valid and contains 'answer' and 'source' keys.
        Otherwise raises ValueError or json.JSONDecodeError.
        """
        import json
        cleaned = text.strip()

        # Clean markdown formatting if present
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if len(lines) >= 2:
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                cleaned = "\n".join(lines).strip()

        # Extract JSON substring if there is surrounding conversational text
        if "{" in cleaned and "}" in cleaned:
            start_idx = cleaned.find("{")
            end_idx = cleaned.rfind("}")
            cleaned = cleaned[start_idx : end_idx + 1]

        data = json.loads(cleaned)
        if not isinstance(data, dict):
            raise ValueError("Response is not a JSON object")

        if "answer" not in data or "source" not in data:
            raise ValueError("Missing required fields: 'answer' and/or 'source'")

        return {
            "answer": str(data["answer"]),
            "source": str(data["source"]),
        }

    def simulate_response(self, query: str, context: str) -> str:
        """Simulate LLM responses grounded strictly in the policies (local offline fallback)."""
        import json
        query_lower = query.lower()
        context_lower = context.lower() if context else ""
        fallback_msg = "I am unable to answer this question as it is not specified in the official policy guidelines."

        if not context_lower:
            return json.dumps({"answer": fallback_msg, "source": "None"})

        if "return period" in query_lower or "how long" in query_lower:
            if "return period" in context_lower and "30 days" in context_lower:
                return json.dumps({
                    "answer": "The return period for standard catalog items is 30 days from the delivery date.",
                    "source": "RETURN PERIOD POLICY"
                })
            return json.dumps({"answer": fallback_msg, "source": "None"})

        if "damaged" in query_lower:
            if "damaged" in context_lower and "48 hours" in context_lower:
                return json.dumps({
                    "answer": "You can return a damaged product if you report the damage and initiate the return within 48 hours of delivery.",
                    "source": "DAMAGED PRODUCT POLICY"
                })
            return json.dumps({"answer": fallback_msg, "source": "None"})

        if "refund conditions" in query_lower or "conditions" in query_lower:
            if (
                "refund conditions" in context_lower
                and "original packaging" in context_lower
            ):
                return json.dumps({
                    "answer": "Refund conditions require products to be in original packaging, unused, and with tags intact. Refunds are processed in 5-7 business days.",
                    "source": "REFUND CONDITIONS POLICY"
                })
            return json.dumps({"answer": fallback_msg, "source": "None"})

        if "seller" in query_lower or "responsibilities" in query_lower:
            if "seller" in context_lower and "2 business days" in context_lower:
                return json.dumps({
                    "answer": "Seller responsibilities include dispatching orders within 2 business days, guaranteeing product authenticity, and responding to inquiries within 24 hours.",
                    "source": "SELLER RESPONSIBILITIES POLICY"
                })
            return json.dumps({"answer": fallback_msg, "source": "None"})

        return json.dumps({"answer": fallback_msg, "source": "None"})

    def generate(
        self, query: str, context: str, max_context_limit: int = 1000
    ) -> Dict[str, Any]:
        """Generate a grounded policy response, performing context size limit checks.

        Returns a dictionary with the answer and detailed token usage/costs.
        """
        import json
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

        raw_response = ""
        simulated = True

        # Run completion using API or offline simulation
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model=self.model, messages=messages, temperature=0.0
                )
                raw_response = response.choices[0].message.content
                simulated = False
            except Exception:
                # If API call fails, fallback to local simulation
                raw_response = self.simulate_response(query, final_context)
        else:
            raw_response = self.simulate_response(query, final_context)

        # Parse and validate response
        parsed_response = None
        try:
            parsed_response = self.parse_and_validate_json(raw_response)
        except Exception:
            # First attempt failed. Retry if using the API client and not simulated.
            if self.client and not simulated:
                try:
                    retry_messages = list(messages)
                    retry_messages.append({"role": "assistant", "content": raw_response})
                    retry_messages.append({
                        "role": "user",
                        "content": (
                            "Error parsing JSON: invalid format or missing required fields. "
                            "Please reply strictly with ONLY a valid JSON object matching the schema: "
                            "{\"answer\": \"<string>\", \"source\": \"<string>\"}. "
                            "Do not include markdown code block ticks or conversational text outside the JSON."
                        )
                    })
                    # Count tokens for the retry instructions
                    retry_input_tokens = input_tokens + get_token_count(raw_response) + get_token_count(retry_messages[-1]["content"]) + 20

                    response = self.client.chat.completions.create(
                        model=self.model, messages=retry_messages, temperature=0.0
                    )
                    raw_response = response.choices[0].message.content
                    parsed_response = self.parse_and_validate_json(raw_response)
                    input_tokens = retry_input_tokens
                except Exception:
                    # Retry failed, fallback to default structure
                    parsed_response = {
                        "answer": "I am unable to answer this question as it is not specified in the official policy guidelines.",
                        "source": "None"
                    }
            else:
                # Simulation failed or no client, fallback to default structure
                parsed_response = {
                    "answer": "I am unable to answer this question as it is not specified in the official policy guidelines.",
                    "source": "None"
                }

        answer_str = json.dumps(parsed_response, indent=2)
        output_tokens = get_token_count(answer_str)

        return {
            "answer": answer_str,
            "context_used": final_context,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "context_truncated": context_truncated,
            "simulated": simulated,
        }