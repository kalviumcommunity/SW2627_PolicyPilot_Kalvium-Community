# PolicyPilot Corpus Ingestion Summary & Completeness Audit

- **Run Timestamp (UTC):** `2026-08-31T17:58:39.903676+00:00`
- **Corpus Source Directory:** `C:\Users\Sushmitha Malleboina\Desktop\privacypolicy\SW2627_PolicyPilot_Kalvium-Community\data`
- **Chunk Configuration:** Target Size = `400` tokens | Overlap = `60` tokens
- **Text Normalization:** `Enabled (NFKC, line-wraps, whitespace, boilerplate removal)`

## 1. Executive Ingestion Matrix

| Metric | Count / Value | Status |
| :--- | :---: | :---: |
| **Total Source Documents Discovered** | **5** | `Audited` |
| **Successfully Ingested Documents** | **4** | `Ready` |
| **Failed / Skipped Documents** | **1** | `Isolated` |
| **Total Chunks Created** | **4** | `Indexed` |
| **Total Ingested Tokens** | **182** | `Counted` |
| **Total Ingested Characters** | **789** | `Processed` |
| **Completeness Validation Check** | **PASSED** | `PASS` |

## 2. Completeness Validation Audit

> **Reconciliation Equation:**
> $$\text{Total Discovered (5)} = \text{Ingested (4)} + \text{Failures (1)}$$

- **Validation Status:** `PASSED`
- **Reconciled:** `True`
- **Discrepancy:** `0` documents
- **Audit Proof:** Completeness Verified: Total discovered (5) matches ingested (4) + failed (1). Zero documents silently dropped.

## 3. Per-Document Ingestion Breakdown

| Source Document | Format | Size (Bytes) | Raw Chars | Clean Chars | Chunks | Tokens | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `corrupt_file.pdf` | `pdf` | 40 | 0 | 0 | 0 | 0 | `FAILED` |
| `remote_policy.txt` | `txt` | 213 | 208 | 207 | 1 | 46 | `OK` |
| `sample_policy.pdf` | `pdf` | 1,589 | 191 | 190 | 1 | 40 | `OK` |
| `stipend_faq.html` | `html` | 291 | 186 | 164 | 1 | 41 | `OK` |
| `work_hours.md` | `md` | 234 | 229 | 228 | 1 | 55 | `OK` |

## 4. Isolated Failures & Skipped Files

The following files failed parsing during intake and were safely isolated without interrupting the pipeline:

| Source Document | Format | Size | Exception Type | Failure Reason |
| :--- | :---: | :---: | :--- | :--- |
| `corrupt_file.pdf` | `pdf` | 40 B | `PdfStreamError` | `Stream has ended unexpectedly` |
