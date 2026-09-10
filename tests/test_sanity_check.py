"""Unit tests for retrieval and embedding sanity testing service."""

from pathlib import Path
import pytest

from src.sanity_test import SanityTester, export_sanity_reports, TestCase


def test_default_test_cases_structure():
    """Verify default test cases are populated with required fields."""
    cases = SanityTester.get_default_test_cases()
    assert len(cases) >= 5

    tc1 = cases[0]
    assert isinstance(tc1, TestCase)
    assert tc1.id == "TC-01"
    assert tc1.expected_source == "remote_policy.txt"
    assert len(tc1.query) > 0


def test_sanity_tester_run_suite():
    """Verify SanityTester runs benchmark suite and computes ranking metrics."""
    tester = SanityTester()
    project_root = Path(__file__).resolve().parents[1]
    data_dir = project_root / "data"

    summary = tester.run_suite(data_dir=data_dir)

    assert summary.total_tests == 6
    assert summary.passed_count >= 4
    assert summary.failed_count >= 1
    assert 0.0 <= summary.pass_rate_percent <= 100.0
    assert len(summary.results) == 6

    # Verify candidate scores breakdown sorting
    tc1_res = summary.results[0]
    assert tc1_res.passed is True
    assert tc1_res.top_ranked_source == "remote_policy.txt"
    assert len(tc1_res.scores_breakdown) == 4
    # Ensure scores are sorted descending
    scores = [s["score"] for s in tc1_res.scores_breakdown]
    assert scores == sorted(scores, reverse=True)


def test_export_sanity_reports(tmp_path):
    """Verify markdown and JSON sanity reports are saved correctly."""
    tester = SanityTester()
    project_root = Path(__file__).resolve().parents[1]
    data_dir = project_root / "data"

    summary = tester.run_suite(data_dir=data_dir)
    md_file, json_file = export_sanity_reports(summary, output_dir=tmp_path)

    assert md_file.exists()
    assert json_file.exists()
    assert md_file.stat().st_size > 0
    assert json_file.stat().st_size > 0

    content = md_file.read_text(encoding="utf-8")
    assert "# PolicyPilot Retrieval & Embedding Sanity Test Report" in content
    assert "Morphological Inflection Mismatch" in content
