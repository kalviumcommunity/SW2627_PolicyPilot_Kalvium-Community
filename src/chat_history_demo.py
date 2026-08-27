"""Demonstration script for CSA 3.15 Context Windows and Message History Management.

Simulates a multi-turn conversation and demonstrates how the history is managed
using trimming and summarization to fit within a tight token budget.
"""

import os
import sys
import io
from dotenv import load_dotenv
from openai import OpenAI

# Force stdout/stderr to use UTF-8 on Windows to prevent UnicodeEncodeError
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Ensure src/ is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.history_service import (
    count_tokens,
    total_tokens,
    trim,
    summarize_history,
)

# Load configuration
load_dotenv()
BASE_URL = os.getenv("API_BASE_URL")
API_KEY = os.getenv("API_KEY")
MODEL = os.getenv("CHAT_MODEL")

if not BASE_URL or not API_KEY or not MODEL:
    print("Error: Missing API configurations in .env file.")
    sys.exit(1)

# Initialize OpenAI-compatible client
client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

# Log file path
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)
log_file_path = os.path.join(OUTPUT_DIR, "sample_run.log")

# Questions to simulate in the multi-turn chat
CONVERSATION_TURNS = [
    "What is the policy for working from home?",
    "Are there any equipment allowances for home office setup?",
    "How do I request reimbursement for my internet bills?",
    "What is the maximum reimbursement amount allowed per month?",
    "Can I work from home from another country?",
    "How many consecutive days can I work remotely?",
    "What is the policy for business travel and remote work?",
    "Who is the primary contact for HR remote policy questions?",
]

SYSTEM_PROMPT = (
    "You are PolicyPilot, an internal assistant for company policy questions. "
    "Provide clear, professional answers. Keep answers brief (max 2 sentences) to save tokens."
)


def log_and_print(text, file_obj):
    """Print to console and write to log file."""
    print(text)
    file_obj.write(text + "\n")
    file_obj.flush()


def run_trim_demo(log_file):
    log_and_print("=" * 60, log_file)
    log_and_print("SIMULATION 1: CONTEXT TRIMMING (Budget: 350 Tokens)", log_file)
    log_and_print("=" * 60, log_file)

    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    budget = 350

    log_and_print(f"System Prompt: {SYSTEM_PROMPT}", log_file)
    log_and_print(f"Initial tokens: {total_tokens(history)}", log_file)
    log_and_print("", log_file)

    for i, user_msg in enumerate(CONVERSATION_TURNS, 1):
        log_and_print(f"--- Turn {i} ---", log_file)
        log_and_print(f"User Question: '{user_msg}'", log_file)

        # Append user message
        history.append({"role": "user", "content": user_msg})

        tokens_before_trim = total_tokens(history)
        log_and_print(f"Tokens before trim check: {tokens_before_trim}", log_file)

        # Apply trimming strategy
        trim(history, budget=budget)

        tokens_after_trim = total_tokens(history)
        log_and_print(f"Tokens after trim check: {tokens_after_trim}", log_file)
        log_and_print(f"Number of active turns in history: {len(history)}", log_file)

        # Print current message list roles to verify oldest is popped but system stays
        roles = [m["role"] for m in history]
        log_and_print(f"Active message roles: {roles}", log_file)

        # Call model
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=history,
            )
            answer = response.choices[0].message.content.strip()
            log_and_print(f"Assistant: {answer}", log_file)
            history.append({"role": "assistant", "content": answer})
        except Exception as e:
            log_and_print(f"API Error: {e}", log_file)
            break

        log_and_print(f"Token count after turn: {total_tokens(history)}", log_file)
        log_and_print("", log_file)


def run_summarize_demo(log_file):
    log_and_print("=" * 60, log_file)
    log_and_print("SIMULATION 2: CONTEXT SUMMARIZATION (Budget: 1000 Tokens)", log_file)
    log_and_print("=" * 60, log_file)

    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    budget = 1000

    log_and_print(f"System Prompt: {SYSTEM_PROMPT}", log_file)
    log_and_print(f"Initial tokens: {total_tokens(history)}", log_file)
    log_and_print("", log_file)

    for i, user_msg in enumerate(CONVERSATION_TURNS, 1):
        log_and_print(f"--- Turn {i} ---", log_file)
        log_and_print(f"User Question: '{user_msg}'", log_file)

        # Append user message
        history.append({"role": "user", "content": user_msg})

        tokens_before_sum = total_tokens(history)
        log_and_print(f"Tokens before summarize check: {tokens_before_sum}", log_file)

        # Apply summarization strategy (keep last 2 turns active)
        summarize_history(history, client, MODEL, budget=budget, keep_turns=2)

        tokens_after_sum = total_tokens(history)
        log_and_print(f"Tokens after summarize check: {tokens_after_sum}", log_file)
        log_and_print(f"Number of active turns in history: {len(history)}", log_file)

        # Print current message list roles to verify summary turn insertion
        roles = [m["role"] for m in history]
        log_and_print(f"Active message roles: {roles}", log_file)

        # Call model
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=history,
            )
            answer = response.choices[0].message.content.strip()
            log_and_print(f"Assistant: {answer}", log_file)
            history.append({"role": "assistant", "content": answer})
        except Exception as e:
            log_and_print(f"API Error: {e}", log_file)
            break

        log_and_print(f"Token count after turn: {total_tokens(history)}", log_file)
        log_and_print("", log_file)


def main():
    print(f"Writing run results to: {log_file_path}\n")

    with open(log_file_path, "w", encoding="utf-8") as log_file:
        log_and_print("PolicyPilot CSA 3.15 Context Management Demo", log_file)
        log_and_print(f"Model used: {MODEL}", log_file)
        log_and_print(f"API Base URL: {BASE_URL}", log_file)
        log_and_print("", log_file)

        run_trim_demo(log_file)
        log_and_print("\n" + "=" * 60 + "\n", log_file)
        run_summarize_demo(log_file)

    print(f"\nSimulation complete! Run logs saved to {log_file_path}")


if __name__ == "__main__":
    main()
