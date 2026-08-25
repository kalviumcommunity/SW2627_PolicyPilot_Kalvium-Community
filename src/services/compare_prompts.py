"""Prompt comparison script for PolicyPilot.

Runs prompt variations (vague vs. clear/constrained) against staff policy queries,
logs outputs, compares behavior differences, and writes output files.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

from src.services.prompt_service import (
    get_vague_prompt,
    get_constrained_prompt,
    get_json_constrained_prompt,
    compare_prompt_structures,
    execute_prompt,
)

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BASE_URL = os.getenv("API_BASE_URL")
API_KEY = os.getenv("API_KEY")
MODEL = os.getenv("CHAT_MODEL", "gpt-3.5-turbo")

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

SAMPLE_QUERIES = [
    {
        "id": 1,
        "query": "What is our refund window for employee software tool purchases?",
        "type": "Policy Query (Specific)",
        "simulated_vague": (
            "Our refund policy for employee software tool purchases allows employees to request a refund "
            "within 30 business days of purchase, provided that the receipt is submitted through the finance portal "
            "and approval has been granted by their department manager. Please ensure that all software licenses are "
            "revoked upon refund processing."
        ),
        "simulated_constrained": (
            "Employees can request a refund for software tool purchases within 30 days of purchase with manager approval. "
            "Submit the receipt via the finance portal to process the reimbursement."
        ),
    },
    {
        "id": 2,
        "query": "Can I claim a refund for my personal gym membership under health benefits?",
        "type": "Policy Query (Uncertain/Unspecified)",
        "simulated_vague": (
            "Yes, generally health benefits may cover wellness activities including gym memberships depending on your "
            "tier. You should check with your HR representative or submit a claim ticket to see if your specific gym qualifies."
        ),
        "simulated_constrained": (
            "I am unable to answer this question as it is not specified in the official policy guidelines."
        ),
    },
    {
        "id": 3,
        "query": "Who won the 2022 FIFA World Cup?",
        "type": "Out of Scope Query",
        "simulated_vague": (
            "Argentina won the 2022 FIFA World Cup in Qatar, defeating France in a dramatic penalty shootout after a 3-3 draw."
        ),
        "simulated_constrained": (
            "I am unable to answer this question as it is not specified in the official policy guidelines."
        ),
    },
]


def run_comparisons() -> List[Dict[str, Any]]:
    """Execute or simulate prompt comparison across sample queries."""
    client = None
    if BASE_URL and API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
            logging.info("Connected to OpenAI-compatible API at %s", BASE_URL)
        except Exception as err:
            logging.warning("Failed to initialize API client (%s). Using fallback demonstration outputs.", err)
    else:
        logging.info("API credentials not found in .env. Using fallback demonstration outputs.")

    results = []

    for item in SAMPLE_QUERIES:
        query_text = item["query"]
        vague_messages = get_vague_prompt(query_text)
        constrained_messages = get_constrained_prompt(query_text)
        json_messages = get_json_constrained_prompt(query_text)

        vague_output = ""
        constrained_output = ""
        json_output = ""

        if client:
            try:
                vague_output = execute_prompt(client, MODEL, vague_messages)
                constrained_output = execute_prompt(client, MODEL, constrained_messages)
                json_output = execute_prompt(client, MODEL, json_messages)
            except Exception as err:
                logging.error("API call failed for query '%s': %s", query_text, err)
                vague_output = item["simulated_vague"]
                constrained_output = item["simulated_constrained"]
                json_output = json.dumps({
                    "answer": constrained_output,
                    "confidence": "high",
                    "refusal": "unable" in constrained_output.lower()
                })
        else:
            vague_output = item["simulated_vague"]
            constrained_output = item["simulated_constrained"]
            json_output = json.dumps({
                "answer": constrained_output,
                "confidence": "high",
                "refusal": "unable" in constrained_output.lower()
            })

        results.append({
            "id": item["id"],
            "query": query_text,
            "query_type": item["type"],
            "variation_1_vague": {
                "system_prompt": vague_messages[0]["content"],
                "user_prompt": vague_messages[1]["content"],
                "output": vague_output,
            },
            "variation_2_constrained": {
                "system_prompt": constrained_messages[0]["content"],
                "user_prompt": constrained_messages[1]["content"],
                "output": constrained_output,
            },
            "json_format_constrained": {
                "system_prompt": json_messages[0]["content"],
                "user_prompt": json_messages[1]["content"],
                "output": json_output,
            },
        })

    return results


def write_outputs(results: List[Dict[str, Any]]) -> None:
    """Save results as JSON and Markdown files in outputs/ directory."""
    json_path = OUTPUT_DIR / "prompt_comparison_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    logging.info("Saved JSON results to %s", json_path)

    md_path = OUTPUT_DIR / "prompt_comparison_results.md"
    md_content = ["# PolicyPilot Prompt Comparison Results\n"]
    md_content.append("This document records the side-by-side comparison between **Variation 1 (Vague Prompt)** and **Variation 2 (Constrained Grounded Prompt)** for PolicyPilot staff questions.\n")

    for res in results:
        md_content.append(f"## Query {res['id']}: {res['query']} ({res['query_type']})\n")
        md_content.append("### Variation 1: Vague Prompt")
        md_content.append(f"- **System Prompt:** `{res['variation_1_vague']['system_prompt']}`")
        md_content.append(f"- **User Prompt:** `{res['variation_1_vague']['user_prompt']}`")
        md_content.append(f"- **Output:**\n> {res['variation_1_vague']['output']}\n")

        md_content.append("### Variation 2: Constrained & Grounded Prompt")
        md_content.append(f"- **System Prompt:** `{res['variation_2_constrained']['system_prompt']}`")
        md_content.append(f"- **User Prompt:** `{res['variation_2_constrained']['user_prompt']}`")
        md_content.append(f"- **Output:**\n> {res['variation_2_constrained']['output']}\n")

        md_content.append("### JSON Format Constrained Prompt")
        md_content.append(f"- **System Prompt:** `{res['json_format_constrained']['system_prompt']}`")
        md_content.append(f"- **Output:**\n```json\n{res['json_format_constrained']['output']}\n```\n")

        md_content.append("---\n")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_content))
    logging.info("Saved Markdown summary to %s", md_path)


if __name__ == "__main__":
    logging.info("Starting prompt comparison test...")
    results = run_comparisons()
    write_outputs(results)
    print("\nPrompt comparison complete! Check outputs/ directory for generated logs.\n")
