"""Command-Line Runner for PolicyPilot Retrieval & Embedding Sanity Testing.

Executes known query-chunk relevance benchmarks, evaluates similarity ranking,
identifies failing/surprising cases, prints terminal summary matrix, and saves
structured Markdown & JSON sanity reports to outputs/.
"""

import logging
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.sanity_test import SanityTester, export_sanity_reports

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def main():
    print("=" * 80)
    print("        PolicyPilot Retrieval & Embedding Pipeline Sanity Test")
    print("=" * 80)

    data_dir = PROJECT_ROOT / "data"
    outputs_dir = PROJECT_ROOT / "outputs"

    print(f"\n[1] Initializing SanityTester...")
    print(f"    - Corpus Directory: {data_dir}")
    print(f"    - Report Output Directory: {outputs_dir}")

    tester = SanityTester()

    print(f"\n[2] Executing Known Relevance Test Cases against Corpus...")
    summary = tester.run_suite(data_dir=data_dir)

    print("\n" + "=" * 80)
    print("                     SANITY TEST RESULTS MATRIX")
    print("=" * 80)
    print(f"{'ID':<6} | {'Category':<22} | {'Expected Source':<18} | {'Top Source':<18} | {'Score':<7} | {'Status'}")
    print("-" * 80)

    for r in summary.results:
        status_str = "[PASS]" if r.passed else "[!] FAIL"
        print(
            f"{r.id:<6} | {r.category:<22} | {r.expected_source:<18} | {r.top_ranked_source:<18} | {r.top_score:<7.4f} | {status_str}"
        )
    print("-" * 80)

    print(f"\n  Total Tests Evaluated: {summary.total_tests}")
    print(f"  Passed Tests:          {summary.passed_count}")
    print(f"  Failed / Surprising:   {summary.failed_count}")
    print(f"  Ranking Pass Rate:     {summary.pass_rate_percent:.2f}%")
    print("=" * 80)

    if summary.failing_cases_analysis:
        print("\n" + "-" * 80)
        print("  SURPRISING / FAILING CASE FINDINGS (Task 3 Isolation):")
        print("-" * 80)
        for fa in summary.failing_cases_analysis:
            print(f"  * Case {fa['test_id']}: \"{fa['query']}\"")
            print(f"    Expected: '{fa['expected_source']}' (Score: {fa['expected_score']:.4f}, Rank: #{fa['rank_of_expected']})")
            print(f"    Actual:   '{fa['actual_top_source']}' (Score: {fa['top_score']:.4f}, Rank: #1)")
            print(f"    Insight:  {fa['analysis']}")
        print("-" * 80)

    print(f"\n[3] Exporting Sanity Reports...")
    md_path, json_path = export_sanity_reports(summary, output_dir=outputs_dir)

    print("\n" + "=" * 80)
    print("                 OUTPUT ARTIFACTS SUCCESSFULLY SAVED")
    print("=" * 80)
    print(f"  [1] Markdown Sanity Report: {md_path}")
    print(f"  [2] JSON Sanity Report:     {json_path}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
