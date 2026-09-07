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

---

## 6. Video Walkthrough Script Guide (3–5 Minutes)

### 1. What Context Injection Means in RAG (0:00 – 0:45)
- *"Welcome to the PolicyPilot demonstration on Prompt Augmentation and Context Injection. In a RAG application, retrieval simply fetches raw text chunks from vector storage. Context injection is the process of structuring those chunks, attaching unique source markers, managing token budgets, and wrapping them in a system instruction so the language model can generate an accurate, grounded answer."*

### 2. How to Keep Context Within the Token Budget (0:45 – 1:30)
- *"Show `assemble_context()` in `src/services/prompt_service.py`. We use `tiktoken` with the `cl100k_base` encoding to calculate the exact token count of each formatted chunk plus delimiters. If adding another chunk exceeds `MAX_CONTEXT_TOKENS` (e.g. 5,000 tokens), the loop terminates gracefully, prioritizing highest-ranked chunks first."*

### 3. Assembled Prompt Walkthrough (1:30 – 2:30)
- *"Run `python src/run_prompt_augmentation_demo.py`. Walk through the assembled prompt on screen, pointing out:"*
  - **Source markers:** `[1] account-guide.md#0`
  - **Separators:** `---` between distinct chunks
  - **Grounding instruction:** *"Answer the question using only the provided context. If the answer is not in the context, say: 'I don't have enough information in the provided context.' When possible, cite sources using markers like [1] or [2]."*

### 4. Why the Model Is Told to Answer ONLY from Context (2:30 – 3:30)
- *"Without the 'only from context' constraint, LLMs will rely on broad, unverified pre-training data rather than specific company policy guidelines. It also prevents the model from speculating or hallucinating when the knowledge base has no answer."*

### 5. Follow-Up Question: What to Do When Retrieved Chunks Exceed Token Limit? (3:30 – 4:45)
- Answer clearly with 5 production strategies:
  1. **Rank-Prioritized Truncation:** Keep the top-$k$ highest-scoring chunks and drop lower-ranked candidates (implemented in PolicyPilot).
  2. **Re-Ranking Before Assembly:** Run a cross-encoder / LLM re-ranking step to discard irrelevant chunks so only the top 3-5 high-precision chunks are injected.
  3. **Contextual Chunk Compression / Trimming:** Strip boilerplate headers, whitespace, and irrelevant sentences from chunks before injection.
  4. **Map-Reduce / Refine Summarization:** Use a multi-stage LLM call to summarize individual chunks before assembling the final prompt.
  5. **Dynamic Top-$k$ Adjustment:** Lower $k$ dynamically based on average chunk length.
