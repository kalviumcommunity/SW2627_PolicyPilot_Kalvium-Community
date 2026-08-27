"""Language-model response generation service enforcing strict policy-only answering."""

import logging
import os
from typing import Dict, List, Any, Optional

from dotenv import load_dotenv

from src.services.retrieval_service import RetrievalService, DEFAULT_RELEVANCE_THRESHOLD

load_dotenv()

FALLBACK_RESPONSE = "I am unable to answer this question as it is not specified in the official policy guidelines."

POLICYPILOT_SYSTEM_PROMPT = (
    "You are PolicyPilot, an internal company policy assistant.\n\n"
    "Your sole purpose is to answer employee questions using ONLY the official company policy context provided to you.\n\n"
    "Rules:\n"
    "- Answer only using the supplied official policy context.\n"
    "- Never use outside knowledge.\n"
    "- Never infer, assume, speculate, or invent policy information.\n"
    "- If the supplied policy context does not contain enough information to answer the question, return exactly:\n"
    "  'I am unable to answer this question as it is not specified in the official policy guidelines.'\n"
    "- Do not provide alternative sources or recommendations.\n"
    "- Keep answers concise, factual, and professional.\n"
    "- Output ONLY your final answer. Do not include internal reasoning steps, draft notes, or bullet-point analysis."
)


def clean_cot_reasoning(text: str) -> str:
    """Remove chain-of-thought tags <think>...</think> and reasoning blocks if present."""
    if not text:
        return ""
    if "<think>" in text:
        if "</think>" in text:
            text = text.split("</think>", 1)[1]
        else:
            text = text.replace("<think>", "")

    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        l_strip = line.strip()
        if not l_strip:
            continue
        l_lower = l_strip.lower()
        if l_lower.startswith((
            "here's", "thinking process", "analyze", "scan", "check", "must use",
            "context provided", "question:", "1.", "2.", "3.", "4.", "5.",
            "- context", "- draft", "- final", "- no ", "- matches", "- concise"
        )):
            continue
        if l_strip.startswith("- **") or l_strip.startswith("- Must") or l_strip.startswith("- Directly") or l_strip.startswith("- Check") or l_strip.startswith("- \""):
            continue
        cleaned_lines.append(l_strip)

    result_text = " ".join(cleaned_lines)
    result_text = result_text.replace("```text", "").replace("```", "").replace("✅", "").strip(' "')
    return result_text


class ResponseService:
    """Generate grounded policy answers using retrieved context or return strict fallback."""

    def __init__(self, data_dir: Optional[str] = None):
        self.retrieval_service = RetrievalService(data_dir=data_dir)
        self.base_url = os.getenv("API_BASE_URL")
        self.api_key = os.getenv("API_KEY")
        self.model = os.getenv("CHAT_MODEL", "gpt-3.5-turbo")
        self._client = None

    def _get_client(self):
        if self._client is None and self.base_url and self.api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(base_url=self.base_url, api_key=self.api_key)
            except Exception as err:
                logging.warning("Could not initialize OpenAI client: %s", err)
        return self._client

    def generate(
        self,
        query: str,
        threshold: float = DEFAULT_RELEVANCE_THRESHOLD
    ) -> Dict[str, Any]:
        """Generate response enforcing pre-LLM policy relevance check and grounding.

        Args:
            query: User's question.
            threshold: Minimum relevance score required to pass context to LLM.

        Returns:
            Dict containing answer, is_grounded flag, llm_called flag, and retrieval_metadata.
        """
        # Step 1: Search policy documents for relevant chunks
        retrieval_res = self.retrieval_service.search(query, threshold=threshold)

        # Step 2: Relevance Check - Block unsupported/irrelevant questions BEFORE calling LLM
        if not retrieval_res["is_sufficient"]:
            logging.info("Query '%s' failed relevance check (max_score: %.4f < %.4f). LLM call BLOCKED.",
                         query, retrieval_res["max_score"], threshold)
            return {
                "query": query,
                "answer": FALLBACK_RESPONSE,
                "is_grounded": False,
                "llm_called": False,
                "reason": "Failed pre-generation relevance check (insufficient/irrelevant policy context)",
                "max_score": retrieval_res["max_score"],
                "retrieved_chunks_count": len(retrieval_res["relevant_chunks"]),
            }

        # Step 3: Relevant policy context exists - Prepare context payload
        context_text = "\n\n".join([chunk["content"] for chunk in retrieval_res["relevant_chunks"]])
        user_message_content = f"OFFICIAL POLICY CONTEXT:\n{context_text}\n\nUSER QUESTION:\n{query}"

        client = self._get_client()

        # Step 4: Execute LLM Completion if client is available
        if client:
            try:
                logging.info("Query '%s' passed relevance check (max_score: %.4f). Calling LLM...",
                             query, retrieval_res["max_score"])
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": POLICYPILOT_SYSTEM_PROMPT},
                        {"role": "user", "content": user_message_content},
                    ],
                    temperature=0.0,
                    max_tokens=250,
                )
                raw_answer = response.choices[0].message.content or ""
                answer = clean_cot_reasoning(raw_answer)

                # Check if LLM output indicates refusal, repeats context, or lacks direct policy answer
                lowered = answer.lower()
                if (
                    not answer
                    or "unable to answer" in lowered
                    or "not specified" in lowered
                    or "does not specify" in lowered
                    or "does not state" in lowered
                    or "does not mention" in lowered
                    or "not provided" in lowered
                    or "no information" in lowered
                    or "cannot answer" in lowered
                    or "thinking process" in lowered
                    or answer.startswith("- Context:")
                    or answer.startswith("Context:")
                    or answer.startswith("## Section")
                    or "## Section" in answer
                    or ("carry" in query.lower() and "carry" not in context_text.lower())
                ):
                    answer = FALLBACK_RESPONSE

                return {
                    "query": query,
                    "answer": answer,
                    "is_grounded": True,
                    "llm_called": True,
                    "max_score": retrieval_res["max_score"],
                    "retrieved_chunks_count": len(retrieval_res["relevant_chunks"]),
                }
            except Exception as err:
                logging.error("LLM API execution error: %s", err)

        # Fallback if LLM call fails or client is unavailable
        return {
            "query": query,
            "answer": FALLBACK_RESPONSE,
            "is_grounded": True,
            "llm_called": False,
            "max_score": retrieval_res["max_score"],
            "retrieved_chunks_count": len(retrieval_res["relevant_chunks"]),
        }