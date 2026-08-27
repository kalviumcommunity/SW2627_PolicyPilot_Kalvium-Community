"""Language-model response generation service enforcing strict policy-only answering."""

import logging
import os
import re
from typing import Dict, Any, Optional

from dotenv import load_dotenv

from src.services.retrieval_service import (
    RetrievalService,
    DEFAULT_RELEVANCE_THRESHOLD,
)

load_dotenv()

FALLBACK_RESPONSE = (
    "I am unable to answer this question as it is not specified "
    "in the official policy guidelines."
)


POLICYPILOT_SYSTEM_PROMPT = """
You are PolicyPilot, an internal company policy assistant.

Your ONLY job is to answer questions using the official company policy
information provided in the retrieved context.

STRICT RULES:

1. Answer ONLY when the retrieved context contains the exact information
   needed to answer the user's question.

2. Use ONLY the retrieved context.
   Do NOT use general knowledge, assumptions, common practices, or outside
   information.

3. A context that is merely related to the question is NOT sufficient.
   The actual answer must be present in the context.

4. If the answer is NOT explicitly available in the retrieved context,
   respond with EXACTLY:
   I am unable to answer this question as it is not specified in the official policy guidelines.

5. If the question is unrelated to company policy, respond with EXACTLY:
   I am unable to answer this question as it is not specified in the official policy guidelines.

6. Never guess, infer, invent, or complete missing policy information.

7. Keep valid answers concise, direct, factual, and professional.

8. Return ONLY the final answer.

9. NEVER output:
   - <think>
   - </think>
   - Thinking Process
   - reasoning
   - analysis
   - self-correction
   - drafts
   - explanations of your instructions

10. Do not tell the user to check HR, Google, websites, handbooks,
    or other sources when the answer is unavailable.

Retrieved official policy context:
{context}

User question:
{question}
"""


def clean_model_output(text: str) -> str:
    """Remove all reasoning, analysis, and <think> blocks from model output.
    
    Returns ONLY the final answer without any reasoning or explanations.
    This function is VERY aggressive about removing anything that's not the direct answer.
    """
    if not text:
        return ""

    text = text.strip()

    # STEP 1: Remove <think>...</think> blocks entirely
    if "<think>" in text.lower():
        think_match = re.search(
            r"<think>.*?</think>",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if think_match:
            text = text[:think_match.start()] + text[think_match.end():]

    # STEP 2: Remove any remaining <think> or </think> tags
    text = re.sub(r"<think>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"</think>", "", text, flags=re.IGNORECASE)

    # STEP 3: Remove markdown code fences
    text = text.replace("```text", "")
    text = text.replace("```", "")

    # STEP 4: Split into lines for analysis
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if not lines:
        return ""

    # STEP 5: Very aggressive filtering - remove any line with analysis/reasoning markers
    bad_patterns = [
        # Reasoning process indicators
        r"^\d+\.\s+",  # "1. ...", "2. ..." (numbered lists for reasoning)
        r"^\*\s+",  # "* ..." (bullet points)
        r"^\-\s+",  # "- ..." (dash lists)
        r"^#{1,6}\s",  # "# ...", "## ..." (headings)
        # Content analysis markers
        r".*Analyze.*",
        r".*Analysis.*",
        r".*Reasoning.*",
        r".*Thinking.*",
        r".*Context.*",
        r".*Evaluate.*",
        r".*Check.*constraint",
        r".*Verify.*",
        r".*Section\s+\d+.*",  # "Section 1: ..." (policy document markers)
        r".*Draft.*",
        r".*Rule\s+\d+.*",  # "Rule 1: ..." (policy rule markers)
        r".*constraint.*",
        r".*All constraints.*",
        r".*formulated.*response",
        r".*direct.*answer.*",
        r".*Final.*",
        r".*Output.*",
    ]

    filtered_lines = []
    for line in lines:
        # Check if line matches any bad pattern
        is_bad = False
        for pattern in bad_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                is_bad = True
                break
        
        # Also reject if it contains policy quote marks like "All" or "employees"
        # at the beginning (suggests it's context/document quote)
        if not is_bad and not line.startswith('*') and not line.startswith('-'):
            filtered_lines.append(line)

    if not filtered_lines:
        return ""

    # STEP 6: Join remaining lines
    answer = " ".join(filtered_lines)

    # STEP 7: Clean up extra whitespace and markdown remnants
    answer = re.sub(r"\s+", " ", answer).strip()
    answer = re.sub(r"\*\*", "", answer)  # Remove ** markdown
    answer = re.sub(r"__", "", answer)    # Remove __ markdown
    answer = re.sub(r"~", "", answer)     # Remove ~ 
    
    # STEP 8: Remove surrounding quotes
    answer = answer.strip().strip('"').strip("'").strip()

    return answer


class ResponseService:
    """Generate grounded answers using official policy context."""

    def __init__(self, data_dir: Optional[str] = None):
        self.retrieval_service = RetrievalService(data_dir=data_dir)

        self.base_url = os.getenv("API_BASE_URL")
        self.api_key = os.getenv("API_KEY")
        self.model = os.getenv(
            "CHAT_MODEL",
            "llama-3.1-8b-instant",
        )

        self._client = None

    def _get_client(self):
        """Create the OpenAI-compatible client."""

        if self._client is None and self.base_url and self.api_key:
            try:
                from openai import OpenAI

                self._client = OpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key,
                )

            except Exception as err:
                logging.error(
                    "Could not initialize API client: %s",
                    err,
                )

        return self._client

    def generate(
        self,
        query: str,
        threshold: float = DEFAULT_RELEVANCE_THRESHOLD,
    ) -> Dict[str, Any]:
        """Generate an answer using only retrieved policy information."""

        query = query.strip()

        # Empty question
        if not query:
            return {
                "query": query,
                "answer": FALLBACK_RESPONSE,
                "is_grounded": False,
                "llm_called": False,
                "reason": "Empty query.",
                "max_score": 0.0,
                "retrieved_chunks_count": 0,
            }

        # ---------------------------------------------------------
        # STEP 1: Retrieve policy context
        # ---------------------------------------------------------

        retrieval_res = self.retrieval_service.search(
            query,
            threshold=threshold,
        )

        # ---------------------------------------------------------
        # STEP 2: Reject questions with no relevant policy context
        # ---------------------------------------------------------

        if not retrieval_res["is_sufficient"]:

            logging.info(
                "Query rejected: '%s' | max_score=%.4f < threshold=%.4f",
                query,
                retrieval_res["max_score"],
                threshold,
            )

            return {
                "query": query,
                "answer": FALLBACK_RESPONSE,
                "is_grounded": False,
                "llm_called": False,
                "reason": "No sufficient official policy context found.",
                "max_score": retrieval_res["max_score"],
                "retrieved_chunks_count": len(
                    retrieval_res["relevant_chunks"]
                ),
            }

        # ---------------------------------------------------------
        # STEP 3: Build retrieved context
        # ---------------------------------------------------------

        context_text = "\n\n".join(
            chunk["content"]
            for chunk in retrieval_res["relevant_chunks"]
        )

        # ---------------------------------------------------------
        # STEP 4: Build strict system prompt
        # ---------------------------------------------------------

        system_message_content = POLICYPILOT_SYSTEM_PROMPT.format(
            context=context_text,
            question=query,
        )

        client = self._get_client()

        # ---------------------------------------------------------
        # STEP 5: If API unavailable, fallback
        # ---------------------------------------------------------

        if not client:

            return {
                "query": query,
                "answer": FALLBACK_RESPONSE,
                "is_grounded": False,
                "llm_called": False,
                "reason": "LLM client unavailable.",
                "max_score": retrieval_res["max_score"],
                "retrieved_chunks_count": len(
                    retrieval_res["relevant_chunks"]
                ),
            }

        # ---------------------------------------------------------
        # STEP 6: Call LLM
        # ---------------------------------------------------------

        try:

            logging.info(
                "Query passed relevance check: '%s' | score=%.4f",
                query,
                retrieval_res["max_score"],
            )

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_message_content,
                    },
                    {
                        "role": "user",
                        "content": query,
                    },
                ],
                temperature=0.0,
                max_tokens=150,
            )

            raw_answer = (
                response.choices[0].message.content or ""
            )

            answer = clean_model_output(raw_answer)

            # -----------------------------------------------------
            # STEP 7: Reject reasoning/refusal output
            # -----------------------------------------------------

            lowered = answer.lower()

            refusal_phrases = [
                "unable to answer",
                "not specified",
                "does not specify",
                "does not state",
                "does not mention",
                "not provided",
                "no information",
                "cannot answer",
                "can't answer",
                "not available",
            ]

            reasoning_phrases = [
                "<think>",
                "</think>",
                "thinking process:",
                "analysis:",
                "reasoning:",
                "self-correction:",
                "final check:",
                "all constraints met",
            ]

            if not answer:
                answer = FALLBACK_RESPONSE

            elif any(
                phrase in lowered
                for phrase in refusal_phrases
            ):
                answer = FALLBACK_RESPONSE

            elif any(
                phrase in lowered
                for phrase in reasoning_phrases
            ):
                answer = FALLBACK_RESPONSE

            # -----------------------------------------------------
            # STEP 8: Final response
            # -----------------------------------------------------

            return {
                "query": query,
                "answer": answer,
                "is_grounded": True,
                "llm_called": True,
                "max_score": retrieval_res["max_score"],
                "retrieved_chunks_count": len(
                    retrieval_res["relevant_chunks"]
                ),
            }

        except Exception as err:

            logging.error(
                "LLM API execution error: %s",
                err,
            )

            return {
                "query": query,
                "answer": FALLBACK_RESPONSE,
                "is_grounded": False,
                "llm_called": False,
                "reason": "LLM execution failed.",
                "max_score": retrieval_res["max_score"],
                "retrieved_chunks_count": len(
                    retrieval_res["relevant_chunks"]
                ),
            }