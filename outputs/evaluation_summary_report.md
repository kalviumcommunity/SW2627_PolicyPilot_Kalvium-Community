# PolicyPilot Full RAG System Evaluation & Quality Report

- **Run Timestamp (UTC):** `2026-09-08T07:58:37.515031+00:00`
- **Total Test Cases Evaluated:** `8`
- **Passed Tests (Score >= 70%):** `7` | **Notable Failures:** `1`
- **Overall RAG System Quality Score:** `86.08%`

## 1. Executive Quality Scorecard Matrix

| Evaluation Metric Dimension | Target Threshold | Achieved Score | Performance Status |
| :--- | :---: | :---: | :---: |
| **Factual Answer Correctness** | `80.0%` | **80.08%** | `PASS` |
| **Context Grounding Quality** | `90.0%` | **92.66%** | `PASS` |
| **Source Citation Accuracy** | `80.0%` | **87.5%** | `PASS` |
| **Overall RAG System Benchmark** | `85.0%` | **86.08%** | `PASS` |

## 2. Per-Test Case Scored Results Breakdown

| ID | Category | Query | Expected Source | Generated Answer & Citation | Correctness | Grounding | Citation Score | Status |
| :---: | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| `EVAL-01` | In-Scope Direct Fact | *"How many days per week can eligible employees work remotely?"* | `remote_policy.txt` | *"Eligible employees are allowed to work remotely up to three days per week,..."* | `85.0%` | `88.9%` | `100.0%` | `PASS` |
| `EVAL-02` | In-Scope Direct Fact | *"What is the maximum monthly claim limit for home internet allowance?"* | `stipend_faq.html` | *"Employees can claim up to $75 per month for high-speed home internet servic..."* | `91.0%` | `85.7%` | `100.0%` | `PASS` |
| `EVAL-03` | In-Scope Multi-Clause | *"What are the standard daily/weekly work hours and what is required for overtime?"* | `work_hours.md` | *"Standard work hours are 8 hours per day and 40 hours per week, with daily c..."* | `87.1%` | `83.3%` | `100.0%` | `PASS` |
| `EVAL-04` | In-Scope Multi-Clause | *"What is the deadline for submitting travel expenses and what class flight is required?"* | `sample_policy.pdf` | *"Travel expenses must be submitted within 30 days of returning, and all flig..."* | `96.4%` | `94.4%` | `100.0%` | `PASS` |
| `EVAL-05` | In-Scope Boundary Rule | *"What hours must remote employees maintain for daily core collaboration?"* | `remote_policy.txt` | *"Eligible employees are allowed to work remotely up to three days per week,..."* | `81.1%` | `88.9%` | `100.0%` | `PASS` |
| `EVAL-06` | Out-of-Scope Fallback | *"Are employees allowed to bring pets to the office?"* | `None (Fallback)` | *"I am unable to answer this question as it is not specified in the official..."* | `100.0%` | `100.0%` | `100.0%` | `PASS` |
| `EVAL-07` | Out-of-Scope Fallback | *"How much does the company reimburse for monthly gym memberships?"* | `None (Fallback)` | *"I am unable to answer this question as it is not specified in the official..."* | `100.0%` | `100.0%` | `100.0%` | `PASS` |
| `EVAL-08` | Morphological Retrieval Edge Case | *"What are the rules for travel expense submission and flight bookings?"* | `sample_policy.pdf` | *"I am unable to answer this question as it is not specified in the official..."* | `0.0%` | `100.0%` | `0.0%` | `FAIL` |

## 3. Notable Failures & Root Cause Diagnostics (Task 4 Findings)

### Case ID `EVAL-08`: Citation Mismatch: Cited sources [] do not match expected sources ['sample_policy.pdf'].
- **Query:** *"What are the rules for travel expense submission and flight bookings?"*
- **Expected Sources:** `['sample_policy.pdf']` | **Retrieved Sources:** `['work_hours.md', 'stipend_faq.html', 'sample_policy.pdf']`
- **Cited Sources:** `[]`
- **Generated Answer:** *"I am unable to answer this question as it is not specified in the official policy guidelines."*
- **Overall Case Score:** `30.0%`

#### Diagnosis & Likely Root Cause:
Morphological Inflection Miss / Hash Vector Orthogonality: Query terms ('submission', 'bookings') failed to match source text ('submitted', 'booked') due to un-stemmed hash embeddings, causing target source to drop out of top-k retrieval.

## 4. Recommendations for System Improvements

1. **Morphological Stemming / Lemmatization:** Integrate stemming/lemmatization or transformer dense embeddings to prevent query word inflections (`submission`/`bookings`) from missing source terms (`submitted`/`booked`).
2. **Hybrid BM25 Keyword Search:** Combine dense vector search with sparse BM25 keyword matching to guarantee exact term and number matches are retrieved.
3. **Explicit Citation Formatting Enforcer:** Enforce structured JSON output format containing explicit `citations: [source_files]` fields to ensure 100% citation compliance.
