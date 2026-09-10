"""Command-Line Runner for PolicyPilot Full RAG System Evaluation.

Executes the full RAG system (Retrieval -> Response Generation -> Citation -> Refusal Fallback)
across benchmark test set, scores factual correctness, grounding quality, and citation accuracy,
identifies notable failures, prints terminal scorecard, and saves output reports.
"""

import json
import logging
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.evaluation_service import EvaluationService, export_evaluation_reports

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)
TESTSET_FILE = PROJECT_ROOT / "data" / "rag_eval_testset.json"


def main():
    print("=" * 85)
    print("        PolicyPilot Full RAG System Quality Evaluation Suite")
    print("=" * 85)

    print(f"\n[1] Initializing EvaluationService & Loading Test Set...")
    print(f"    - Benchmark Test Set: {TESTSET_FILE}")
    print(f"    - Output Report Directory: {OUTPUTS_DIR}")

    eval_service = EvaluationService()

    print(f"\n[2] Executing Full RAG System Evaluation across Benchmark Questions...")
    summary = eval_service.evaluate_rag_system(test_set_path=TESTSET_FILE)

    print("\n" + "=" * 85)
    print("                     RAG SYSTEM EVALUATION SCORECARD")
    print("=" * 85)
    print(f"{'ID':<7} | {'Category':<22} | {'Correctness':<11} | {'Grounding':<9} | {'Citations':<9} | {'Status'}")
    print("-" * 85)

    for r in summary["results"]:
        status_str = "[PASS]" if r["passed"] else "[!] FAIL"
        corr_pct = f"{r['correctness_score']*100:.1f}%"
        grnd_pct = f"{r['grounding_score']*100:.1f}%"
        cite_pct = f"{r['citation_score']*100:.1f}%"
        print(
            f"{r['id']:<7} | {r['category']:<22} | {corr_pct:<11} | {grnd_pct:<9} | {cite_pct:<9} | {status_str}"
        )

    print("-" * 85)
    print(f"\n  Total Tests Evaluated:        {summary['total_tests_evaluated']}")
    print(f"  Passed Tests (Score >= 70%):  {summary['passed_tests_count']}")
    print(f"  Failed / Notable Cases:       {summary['failed_tests_count']}")
    print(f"  ------------------------------------------------")
    print(f"  Average Factual Correctness:  {summary['average_correctness_percent']}%")
    print(f"  Average Context Grounding:    {summary['average_grounding_percent']}%")
    print(f"  Average Citation Accuracy:    {summary['average_citation_accuracy_percent']}%")
    print(f"  OVERALL RAG QUALITY BENCHMARK:{summary['overall_quality_score_percent']}%")
    print("=" * 85)

    if summary["notable_failures"]:
        print("\n" + "-" * 85)
        print("  NOTABLE FAILURES & ROOT CAUSE DIAGNOSTICS (Task 4 Findings):")
        print("-" * 85)
        for nf in summary["notable_failures"]:
            print(f"  * Case {nf['id']}: \"{nf['query']}\"")
            print(f"    Expected: {nf['expected_sources']} | Retrieved: {nf['retrieved_sources']} | Cited: {nf['cited_sources']}")
            print(f"    Score:    {nf['overall_score']*100:.1f}% | Issue: {nf['failure_reason']}")
            print(f"    Cause:    {nf['likely_cause']}")
        print("-" * 85)

    print(f"\n[3] Exporting Evaluation Reports...")
    md_path, json_path = export_evaluation_reports(summary, output_dir=OUTPUTS_DIR)

    print("\n" + "=" * 85)
    print("                 OUTPUT ARTIFACTS SUCCESSFULLY SAVED")
    print("=" * 85)
    print(f"  [1] JSON Scored Results:      {json_path}")
    print(f"  [2] Markdown Evaluation Audit:{md_path}")
    print("=" * 85 + "\n")


if __name__ == "__main__":
    main()
