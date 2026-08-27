"""PolicyPilot Test Suite Runner with Dynamic PASS/FAIL Enforcement Verification."""

import sys
from pathlib import Path
from typing import Dict, List, Any

# Ensure stdout uses UTF-8 encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.response_service import ResponseService, FALLBACK_RESPONSE


TEST_CASES = [
    {
        "id": 1,
        "category": "Valid policy question with information available",
        "query": "What is our annual leave allowance for full-time employees?",
        "expected_type": "supported",
        "expected_reason": "Answer grounded in official policy.",
    },
    {
        "id": 2,
        "category": "Valid policy question with information available",
        "query": "What is the daily meal expense cap for business travel?",
        "expected_type": "supported",
        "expected_reason": "Answer grounded in official policy.",
    },
    {
        "id": 3,
        "category": "Unrelated general knowledge question",
        "query": "Who won the FIFA 2024 World Cup?",
        "expected_type": "unsupported",
        "expected_reason": "Question correctly rejected as outside policy scope.",
    },
    {
        "id": 4,
        "category": "General programming question",
        "query": "What is Python?",
        "expected_type": "unsupported",
        "expected_reason": "Question correctly rejected as outside policy scope.",
    },
    {
        "id": 5,
        "category": "Casual conversation",
        "query": "Tell me a joke.",
        "expected_type": "unsupported",
        "expected_reason": "Question correctly rejected as outside policy scope.",
    },
    {
        "id": 6,
        "category": "Out of domain question",
        "query": "What is the weather today?",
        "expected_type": "unsupported",
        "expected_reason": "Question correctly rejected as outside policy scope.",
    },
    {
        "id": 7,
        "category": "Policy question with missing information",
        "query": "What is our refund window for employee software tool purchases?",
        "expected_type": "unsupported",
        "expected_reason": "Information not found in official policy.",
    },
    {
        "id": 8,
        "category": "Follow-up question with insufficient context",
        "query": "Can I carry those annual leave days into next year?",
        "expected_type": "unsupported",
        "expected_reason": "Information not found in official policy.",
    },
]


class PolicyPilotTestRunner:
    """Test suite runner evaluating actual PolicyPilot RAG pipeline behavior."""

    def __init__(self, data_dir=None):
        self.response_service = ResponseService(data_dir=data_dir)

    def evaluate_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single test case against actual PolicyPilot pipeline and evaluate PASS/FAIL dynamically.

        DYNAMIC PASS/FAIL EVALUATION LOGIC:
        1. For UNSUPPORTED questions (general knowledge, casual, out of domain, missing policy):
           - PolicyPilot MUST return EXACTLY the fallback sentence:
             "I am unable to answer this question as it is not specified in the official policy guidelines."
           - The LLM MUST NOT be called to generate a general knowledge answer (llm_called must be False, or answer must be exact fallback).
           - If LLM generated a general knowledge answer instead of fallback -> FAIL.
           - If exact fallback returned -> PASS.

        2. For SUPPORTED questions (valid policy question in documents):
           - PolicyPilot MUST return a non-fallback, grounded answer.
           - If answer is non-empty and not fallback -> PASS.
           - If fallback returned for valid policy query -> FAIL.
        """
        query = test_case["query"]
        expected_type = test_case["expected_type"]
        expected_reason = test_case["expected_reason"]

        # Execute actual RAG pipeline
        result = self.response_service.generate(query)
        actual_answer = result["answer"]
        llm_called = result.get("llm_called", False)

        passed = False
        fail_reason = ""
        status_text = ""

        if expected_type == "unsupported":
            # Check 1: Output must be EXACT fallback sentence
            is_exact_fallback = (actual_answer == FALLBACK_RESPONSE)

            # Check 2: If LLM was called and returned general knowledge text (not fallback) -> FAIL
            if not is_exact_fallback:
                passed = False
                fail_reason = f"LLM generated general answer instead of exact fallback. Output: '{actual_answer[:60]}...'"
            else:
                passed = True
                status_text = f"PASS - {expected_reason}"

        elif expected_type == "supported":
            # Must be a grounded answer (not fallback)
            is_grounded = (actual_answer != FALLBACK_RESPONSE) and (len(actual_answer) > 0)
            if is_grounded:
                passed = True
                status_text = f"PASS - {expected_reason}"
            else:
                passed = False
                fail_reason = "PolicyPilot returned fallback for a valid, supported policy question."

        return {
            "test_case": test_case,
            "actual_answer": actual_answer,
            "llm_called": llm_called,
            "passed": passed,
            "status_text": status_text if passed else f"FAIL - {fail_reason}",
        }

    def run_all_tests(self) -> Dict[str, Any]:
        """Execute all test cases and display formatted test cards and final summary."""
        results = []
        total_tests = len(TEST_CASES)
        passed_count = 0
        failed_count = 0

        for tc in TEST_CASES:
            res = self.evaluate_test_case(tc)
            results.append(res)

            print("========================================")
            print("       PolicyPilot Test")
            print("========================================")
            print(f"Category: {tc['category']}")
            print(f"\nQuestion:\n{tc['query']}\n")
            print(f"PolicyPilot:\n{res['actual_answer']}\n")
            print(f"Status:\n{res['status_text']}")
            print("========================================\n")

            if res["passed"]:
                passed_count += 1
            else:
                failed_count += 1

        all_passed = (failed_count == 0)

        print("========================================")
        print("             TEST SUMMARY")
        print("========================================")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_count}")
        print(f"Failed: {failed_count}")
        print(f"Policy-only enforcement: {'PASS' if all_passed else 'FAIL'}")
        print("========================================\n")

        return {
            "total": total_tests,
            "passed": passed_count,
            "failed": failed_count,
            "enforcement_pass": all_passed,
            "details": results,
        }


if __name__ == "__main__":
    runner = PolicyPilotTestRunner()
    runner.run_all_tests()
