# PolicyPilot Retrieval & Embedding Sanity Test Report

- **Run Timestamp (UTC):** `2026-09-02T11:40:38.996350+00:00`
- **Corpus Documents Evaluated:** `4`
- **Total Relevance Tests:** `6`
- **Passed Tests:** `5` | **Failed / Surprising Cases:** `1`
- **Overall Ranking Pass Rate:** `83.33%`

## 1. Executive Test Matrix

| ID | Category | Query | Expected Source | Top-Ranked Source | Top Score | Status |
| :---: | :--- | :--- | :--- | :--- | :---: | :---: |
| `TC-01` | Remote Work Allowance | *"How many days per week can eligible employees work remotely?"* | `remote_policy.txt` | `remote_policy.txt` | `0.4406` | `PASS` |
| `TC-02` | Internet Stipend Claim | *"What is the monthly claim limit for home internet allowance under the stipend policy?"* | `stipend_faq.html` | `stipend_faq.html` | `0.5186` | `PASS` |
| `TC-03` | Work Hours & Check-in | *"What are the standard weekly work hours and daily check-in requirements?"* | `work_hours.md` | `work_hours.md` | `0.4247` | `PASS` |
| `TC-04` | Travel Expense Rules | *"What are the rules and guidelines for travel expense reimbursement and economy flights?"* | `sample_policy.pdf` | `sample_policy.pdf` | `0.2416` | `PASS` |
| `TC-05` | Borderline / Domain Overlap | *"What hours must remote employees work for daily core collaboration?"* | `remote_policy.txt` | `remote_policy.txt` | `0.4148` | `PASS` |
| `TC-06` | Morphological Miss (Surprising Failure) | *"What are the rules for travel expense submission and flight bookings?"* | `sample_policy.pdf` | `work_hours.md` | `0.1391` | `FAIL / SURPRISING` |

## 2. Detailed Test Case Evaluation

### TC-01: Remote Work Allowance ([PASS])
- **Query:** *"How many days per week can eligible employees work remotely?"*
- **Expected Relevant Source:** `remote_policy.txt` (Score: `0.4406`)
- **Actual Top-Ranked Source:** `remote_policy.txt` (Score: `0.4406`)
- **Description:** Checks if query about remote work days correctly ranks remote_policy.txt as #1.
- **Evaluation Notes:** PASS: 'remote_policy.txt' ranked #1 with similarity score 0.4406 (margin of +0.2630 over 2nd rank 'work_hours.md').

#### Full Candidate Similarity Score Breakdown:

| Rank | Source Document | Cosine Similarity Score | Target Match |
| :---: | :--- | :---: | :---: |
| #1 | `remote_policy.txt` | `0.4406` | `YES (Expected)` |
| #2 | `work_hours.md` | `0.1776` | `No` |
| #3 | `stipend_faq.html` | `0.1553` | `No` |
| #4 | `sample_policy.pdf` | `0.0856` | `No` |

### TC-02: Internet Stipend Claim ([PASS])
- **Query:** *"What is the monthly claim limit for home internet allowance under the stipend policy?"*
- **Expected Relevant Source:** `stipend_faq.html` (Score: `0.5186`)
- **Actual Top-Ranked Source:** `stipend_faq.html` (Score: `0.5186`)
- **Description:** Checks if internet allowance reimbursement question ranks stipend_faq.html as #1.
- **Evaluation Notes:** PASS: 'stipend_faq.html' ranked #1 with similarity score 0.5186 (margin of +0.4512 over 2nd rank 'work_hours.md').

#### Full Candidate Similarity Score Breakdown:

| Rank | Source Document | Cosine Similarity Score | Target Match |
| :---: | :--- | :---: | :---: |
| #1 | `stipend_faq.html` | `0.5186` | `YES (Expected)` |
| #2 | `work_hours.md` | `0.0674` | `No` |
| #3 | `remote_policy.txt` | `0.0329` | `No` |
| #4 | `sample_policy.pdf` | `0.0065` | `No` |

### TC-03: Work Hours & Check-in ([PASS])
- **Query:** *"What are the standard weekly work hours and daily check-in requirements?"*
- **Expected Relevant Source:** `work_hours.md` (Score: `0.4247`)
- **Actual Top-Ranked Source:** `work_hours.md` (Score: `0.4247`)
- **Description:** Checks if work hours and check-in logging question ranks work_hours.md as #1.
- **Evaluation Notes:** PASS: 'work_hours.md' ranked #1 with similarity score 0.4247 (margin of +0.2116 over 2nd rank 'remote_policy.txt').

#### Full Candidate Similarity Score Breakdown:

| Rank | Source Document | Cosine Similarity Score | Target Match |
| :---: | :--- | :---: | :---: |
| #1 | `work_hours.md` | `0.4247` | `YES (Expected)` |
| #2 | `remote_policy.txt` | `0.2131` | `No` |
| #3 | `stipend_faq.html` | `0.1298` | `No` |
| #4 | `sample_policy.pdf` | `-0.0129` | `No` |

### TC-04: Travel Expense Rules ([PASS])
- **Query:** *"What are the rules and guidelines for travel expense reimbursement and economy flights?"*
- **Expected Relevant Source:** `sample_policy.pdf` (Score: `0.2416`)
- **Actual Top-Ranked Source:** `sample_policy.pdf` (Score: `0.2416`)
- **Description:** Checks if travel expense submission rules rank sample_policy.pdf as #1.
- **Evaluation Notes:** PASS: 'sample_policy.pdf' ranked #1 with similarity score 0.2416 (margin of +0.0680 over 2nd rank 'work_hours.md').

#### Full Candidate Similarity Score Breakdown:

| Rank | Source Document | Cosine Similarity Score | Target Match |
| :---: | :--- | :---: | :---: |
| #1 | `sample_policy.pdf` | `0.2416` | `YES (Expected)` |
| #2 | `work_hours.md` | `0.1736` | `No` |
| #3 | `stipend_faq.html` | `0.1560` | `No` |
| #4 | `remote_policy.txt` | `0.0261` | `No` |

### TC-05: Borderline / Domain Overlap ([PASS])
- **Query:** *"What hours must remote employees work for daily core collaboration?"*
- **Expected Relevant Source:** `remote_policy.txt` (Score: `0.4148`)
- **Actual Top-Ranked Source:** `remote_policy.txt` (Score: `0.4148`)
- **Description:** Tests differentiation between core collaboration hours (remote_policy.txt) and general work hours (work_hours.md).
- **Evaluation Notes:** PASS: 'remote_policy.txt' ranked #1 with similarity score 0.4148 (margin of +0.0610 over 2nd rank 'work_hours.md').

#### Full Candidate Similarity Score Breakdown:

| Rank | Source Document | Cosine Similarity Score | Target Match |
| :---: | :--- | :---: | :---: |
| #1 | `remote_policy.txt` | `0.4148` | `YES (Expected)` |
| #2 | `work_hours.md` | `0.3538` | `No` |
| #3 | `stipend_faq.html` | `0.1304` | `No` |
| #4 | `sample_policy.pdf` | `0.1150` | `No` |

### TC-06: Morphological Miss (Surprising Failure) ([FAIL / SURPRISING])
- **Query:** *"What are the rules for travel expense submission and flight bookings?"*
- **Expected Relevant Source:** `sample_policy.pdf` (Score: `0.0810`)
- **Actual Top-Ranked Source:** `work_hours.md` (Score: `0.1391`)
- **Description:** Surprising failure case where inflected query words ('submission', 'bookings') fail to match source words ('submitted', 'booked') due to lack of stemming/lemmatization in hash embeddings.
- **Evaluation Notes:** FAIL/SURPRISING: Expected 'sample_policy.pdf' (ranked #3 with score 0.0810), but 'work_hours.md' ranked #1 with score 0.1391.

#### Full Candidate Similarity Score Breakdown:

| Rank | Source Document | Cosine Similarity Score | Target Match |
| :---: | :--- | :---: | :---: |
| #1 | `work_hours.md` | `0.1391` | `No` |
| #2 | `stipend_faq.html` | `0.1245` | `No` |
| #3 | `sample_policy.pdf` | `0.0810` | `YES (Expected)` |
| #4 | `remote_policy.txt` | `0.0565` | `No` |

## 3. Analysis of Failing & Surprising Cases (Task 3 Findings)

### Case ID `TC-06`: Morphological Inflection Mismatch
- **Query:** *"What are the rules for travel expense submission and flight bookings?"*
- **Expected Source:** `sample_policy.pdf` (Ranked #3 with score `0.0810`)
- **Top-Ranked Source:** `work_hours.md` (Score `0.1391`)

#### What This Revealed About the Pipeline & Corpus:
1. **Lack of Morphological Stemming / Lemmatization:**
   - The query uses noun/verb inflections: `submission` and `bookings`.
   - The target source document `sample_policy.pdf` contains past tense / verb forms: `submitted` and `booked`.
   - Because the embedding generator hashes raw word strings without lemmatization or stemming (`bookings` vs `booked`), the hash-based vectors treat these terms as orthogonal random noise, preventing keyword-semantic overlap.

2. **Vocabulary Overlap Baseline Noise:**
   - Generic query terms like `rules` and `expense` have subtle overlap across multiple corpus files (`work_hours.md` has guidelines/rules, `stipend_faq.html` has reimbursement/claims).
   - When the core domain keywords (`submission`/`bookings`) miss their target (`submitted`/`booked`), the target document's score drops to `0.0810`, allowing background noise from `work_hours.md` (`0.1391`) to incorrectly rank above it.

## 4. Summary & Recommendations for RAG Retrieval Pipeline

1. **Implement Text Stemming / Lemmatization:** Preprocess queries and corpus text with NLTK/spaCy lemmatizers or stemmers before token hashing to resolve inflection mismatches (`booked` <-> `booking`).
2. **Hybrid Retrieval (BM25 + Dense Embeddings):** Combine sparse keyword retrieval (BM25) with vector similarity ranking to ensure exact/partial word matches boost target document relevance.
3. **Dense Semantic Embeddings:** Transition from word-hash embeddings to neural transformer models (e.g. OpenAI `text-embedding-3-small` or `SentenceTransformers`) which natively represent semantic similarity across inflections and synonyms.
