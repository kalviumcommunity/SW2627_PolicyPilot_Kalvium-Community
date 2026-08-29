# Text Cleaning Pipeline Before/After Report

This report demonstrates the effect of the Text Extraction & Cleaning Pipeline on the documents in our corpus.

## Summary Statistics

| Document Source | Raw Chars | Cleaned Chars | Change (Chars) | Reduction (%) |
| --- | --- | --- | --- | --- |
| remote_policy.txt | 208 | 207 | -1 | 0.5% |
| sample_policy.pdf | 191 | 190 | -1 | 0.5% |
| stipend_faq.html | 186 | 164 | -22 | 11.8% |
| work_hours.md | 229 | 228 | -1 | 0.4% |

## Detailed Before / After Comparisons

### Document: `remote_policy.txt`

#### BEFORE (Raw Extracted Text Preview):
```text
Company Remote Work Policy
Effective: January 1, 2026

Eligible employees are allowed to work remotely up to three days per week.
Employees must maintain standard core collaboration hours from 10 AM to 4 PM.

```

#### AFTER (Cleaned & Normalised Text Preview):
```text
Company Remote Work Policy Effective: January 1, 2026

Eligible employees are allowed to work remotely up to three days per week. Employees must maintain standard core collaboration hours from 10 AM to 4 PM.
```

---

### Document: `sample_policy.pdf`

#### BEFORE (Raw Extracted Text Preview):
```text
PolicyPilot Official Travel Reimbursement Guidelines
1. Travel expenses must be submitted within 30 days of returning.
2. All flights must be booked in economy class unless approved by a VP.

```

#### AFTER (Cleaned & Normalised Text Preview):
```text
PolicyPilot Official Travel Reimbursement Guidelines
1. Travel expenses must be submitted within 30 days of returning.
2. All flights must be booked in economy class unless approved by a VP.
```

---

### Document: `stipend_faq.html`

#### BEFORE (Raw Extracted Text Preview):
```text

 
 
 Stipend FAQ 
 
 
 Stipend & Reimbursement FAQ 
 Q: What can I claim under the internet allowance? 
 A: You can claim up to $75 per month for high-speed home internet service. 
 
 

```

#### AFTER (Cleaned & Normalised Text Preview):
```text
Stipend FAQ Stipend & Reimbursement FAQ Q: What can I claim under the internet allowance? A: You can claim up to $75 per month for high-speed home internet service.
```

---

### Document: `work_hours.md`

#### BEFORE (Raw Extracted Text Preview):
```text
# Work Hours and Overtime Guideline

All remote workers must log their daily check-in and check-out times in the HR system.
- Standard hours: 8 hours per day, 40 hours per week.
- Overtime must be pre-approved by your team lead.

```

#### AFTER (Cleaned & Normalised Text Preview):
```text
# Work Hours and Overtime Guideline

All remote workers must log their daily check-in and check-out times in the HR system.
- Standard hours: 8 hours per day, 40 hours per week.
- Overtime must be pre-approved by your team lead.
```

---
