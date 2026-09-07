# Prompt Augmentation & Context Injection Report (Concept 3.36)

This report documents the implementation and verification of PolicyPilot's context injection and prompt augmentation pipeline.

---

## 1. Overview & Key Capabilities

- **Chunk Labeling & Source Markers:** Formats each retrieved chunk with `[index] source#chunk_index` to enable citation tracking.
- **Token Budget Assembly:** Respects model context window limits by packing highest-ranked chunks first and stopping when the budget is reached.
- **Grounded Instruction:** Constrains generation to only the provided context, requiring refusal when information is absent.

---

## 2. Chunk Formatting & Source Markers

```text
[1] account-guide.md#0
How can a learner reset their password? Learners can reset their password by navigating to the login portal, clicking 'Forgot Password', entering their registered email, and following the secure reset link. Multi-factor authentication (MFA) recovery can be initiated through support.

---

[2] campus-guide.md#0
Campus Facilities and Dining: When does the cafeteria menu change? The campus cafeteria rotates its full menu every Monday morning at 7:00 AM. Operating hours: Breakfast 7:30-10:00 AM, Lunch 12:00-2:30 PM, Dinner 6:00-8:30 PM.
```

---

## 3. Token Budget Enforcement

| Budget Configuration | Token Cap | Tokens Used | Chunks Included | Behavior |
| --- | --- | --- | --- | --- |
| **Standard Context Budget** | 5,000 tokens | `251` tokens | `4` / `4` | All relevant retrieved chunks included |
| **Constrained Context Budget** | 100 tokens | `61` tokens | `1` / `4` | Gracefully stopped at budget limit without crashing |

---

## 4. Assembled Grounded Prompt Example

```text
You are a grounded assistant. Answer the question using only the provided context. If the answer is not in the context, say: "I don't have enough information in the provided context."
When possible, cite sources using the markers like [1] or [2].

Context:
[1] account-guide.md#0
How can a learner reset their password? Learners can reset their password by navigating to the login portal, clicking 'Forgot Password', entering their registered email, and following the secure reset link. Multi-factor authentication (MFA) recovery can be initiated through support.

---

[2] campus-guide.md#0
Campus Facilities and Dining: When does the cafeteria menu change? The campus cafeteria rotates its full menu every Monday morning at 7:00 AM. Operating hours: Breakfast 7:30-10:00 AM, Lunch 12:00-2:30 PM, Dinner 6:00-8:30 PM.

---

[3] submission-rubric.md#0
Academic Project Submission Rubric: What evidence is required for project submission? Required evidence includes a public GitHub repository link, clean source code, passing automated unit tests, granular commit history, and a 3-5 minute demo video.

---

[4] remote_policy.txt#0
Company Remote Work Policy (Effective January 1, 2026): Eligible employees may work remotely up to three days per week while maintaining standard core collaboration hours from 10 AM to 4 PM.

Question:
How can a learner reset their password?
```

---

## 5. Architectural Control Points

1. **Why Label Chunks with Markers?** Enables verifiable citation auditing and prevents hallucinations.
2. **Why Stay Within Token Budget?** Prevents context window truncation errors and leaves space for the model's generated answer.
3. **Why Enforce 'Only from Provided Context'?** Prevents general pre-training bias from overriding internal policy guidelines.
