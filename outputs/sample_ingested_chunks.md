# PolicyPilot Ingested Chunks & Metadata Inspection

This report provides sample chunk inspections across every successfully ingested document in the full corpus. Inspect cleaned text quality, chunk boundary preservation, source identifiers, token counts, and complete metadata dictionaries.

- **Ingestion Run UTC:** `2026-08-31T17:58:39.903676+00:00`
- **Total Successfully Ingested Documents:** 4
- **Total Chunks Produced:** 4

---

## Document: `remote_policy.txt` (TXT)
- **Total Chunks in Document:** 1
- **Displaying First 1 Sample Chunk(s):**

### Chunk Index `0` of `1`
- **Source Identifier:** `remote_policy.txt`
- **Token Count:** `46` tokens (Range: `[0 : 46]`)
- **Character Length:** `207` chars | **Word Count:** `34` words
- **Document Format:** `txt`
- **Ingested Timestamp:** `2026-08-31T17:58:39.903676+00:00`

#### Chunk Text Content:
```text
Company Remote Work Policy Effective: January 1, 2026

Eligible employees are allowed to work remotely up to three days per week. Employees must maintain standard core collaboration hours from 10 AM to 4 PM.
```

#### Chunk Metadata Tag Dictionary:
```json
{
  "source": "remote_policy.txt",
  "chunk_index": 0,
  "total_chunks": 1,
  "token_count": 46,
  "start_token": 0,
  "end_token": 46,
  "char_length": 207,
  "word_count": 34,
  "doc_type": "txt",
  "ingested_at": "2026-08-31T17:58:39.903676+00:00"
}
```

---

## Document: `sample_policy.pdf` (PDF)
- **Total Chunks in Document:** 1
- **Displaying First 1 Sample Chunk(s):**

### Chunk Index `0` of `1`
- **Source Identifier:** `sample_policy.pdf`
- **Token Count:** `40` tokens (Range: `[0 : 40]`)
- **Character Length:** `190` chars | **Word Count:** `30` words
- **Document Format:** `pdf`
- **Ingested Timestamp:** `2026-08-31T17:58:39.903676+00:00`

#### Chunk Text Content:
```text
PolicyPilot Official Travel Reimbursement Guidelines
1. Travel expenses must be submitted within 30 days of returning.
2. All flights must be booked in economy class unless approved by a VP.
```

#### Chunk Metadata Tag Dictionary:
```json
{
  "source": "sample_policy.pdf",
  "chunk_index": 0,
  "total_chunks": 1,
  "token_count": 40,
  "start_token": 0,
  "end_token": 40,
  "char_length": 190,
  "word_count": 30,
  "doc_type": "pdf",
  "ingested_at": "2026-08-31T17:58:39.903676+00:00"
}
```

---

## Document: `stipend_faq.html` (HTML)
- **Total Chunks in Document:** 1
- **Displaying First 1 Sample Chunk(s):**

### Chunk Index `0` of `1`
- **Source Identifier:** `stipend_faq.html`
- **Token Count:** `41` tokens (Range: `[0 : 41]`)
- **Character Length:** `164` chars | **Word Count:** `29` words
- **Document Format:** `html`
- **Ingested Timestamp:** `2026-08-31T17:58:39.903676+00:00`

#### Chunk Text Content:
```text
Stipend FAQ Stipend & Reimbursement FAQ Q: What can I claim under the internet allowance? A: You can claim up to $75 per month for high-speed home internet service.
```

#### Chunk Metadata Tag Dictionary:
```json
{
  "source": "stipend_faq.html",
  "chunk_index": 0,
  "total_chunks": 1,
  "token_count": 41,
  "start_token": 0,
  "end_token": 41,
  "char_length": 164,
  "word_count": 29,
  "doc_type": "html",
  "ingested_at": "2026-08-31T17:58:39.903676+00:00"
}
```

---

## Document: `work_hours.md` (MD)
- **Total Chunks in Document:** 1
- **Displaying First 1 Sample Chunk(s):**

### Chunk Index `0` of `1`
- **Source Identifier:** `work_hours.md`
- **Token Count:** `55` tokens (Range: `[0 : 55]`)
- **Character Length:** `228` chars | **Word Count:** `41` words
- **Document Format:** `md`
- **Ingested Timestamp:** `2026-08-31T17:58:39.903676+00:00`

#### Chunk Text Content:
```text
# Work Hours and Overtime Guideline

All remote workers must log their daily check-in and check-out times in the HR system.
- Standard hours: 8 hours per day, 40 hours per week.
- Overtime must be pre-approved by your team lead.
```

#### Chunk Metadata Tag Dictionary:
```json
{
  "source": "work_hours.md",
  "chunk_index": 0,
  "total_chunks": 1,
  "token_count": 55,
  "start_token": 0,
  "end_token": 55,
  "char_length": 228,
  "word_count": 41,
  "doc_type": "md",
  "ingested_at": "2026-08-31T17:58:39.903676+00:00"
}
```

---
