# PolicyPilot Prompt Construction & System/User Roles Guide

## 1. Overview & Objectives

In a Retrieval-Augmented Generation (RAG) assistant, system prompts serve as the primary control mechanism. Small adjustments in system prompt wording dictate whether an assistant generates concise, grounded, and safe answers or produces wordy, ungrounded, and hallucinated responses.

This document details:
1. The functional separation between **System** and **User** roles.
2. The elements of an effective System Message (Role, Scope, Constraints, Tone, and Refusal Fallback).
3. Comparative analysis between **Variation 1 (Vague)** and **Variation 2 (Constrained & Grounded)** prompts.
4. Explanations of why the chosen constrained system message works reliably.
5. Guidance on constraining output formats (e.g., JSON schema enforcement).

---

## 2. System vs. User Roles: Functional Division

| Role | Purpose | Responsibilities | Example |
|---|---|---|---|
| **System (`role: "system"`)** | Assistant Persona & Rules Engine | Sets global identity, domain boundaries (scope), answer constraints (length/tone), and refusal fallback rules. | `"You are PolicyPilot, an internal support assistant for staff policy questions..."` |
| **User (`role: "user"`)** | Turn Input / Question | Supplies the specific question, context, or task for the current interaction turn. | `"What is our refund window for employee software tool purchases?"` |

### Key Takeaway
- The **System Message** dictates *how* the assistant thinks, responds, and bounds its knowledge.
- The **User Message** specifies *what* exact query needs to be answered in this turn.

---

## 3. System Message Architecture (Role, Scope, Constraints & Fallback)

Our optimal system message is constructed with five explicit components:

```text
[ROLE]
You are PolicyPilot, an internal support assistant for staff policy questions.

[SCOPE & BOUNDARIES]
Your sole task is to answer staff questions accurately using official company policy guidelines. Do not answer non-policy questions or speculate beyond official guidelines.

[CONSTRAINTS & TONE]
Keep your response concise (maximum 2 sentences). Maintain a direct, factual, and professional tone.

[FALLBACK RULE]
If the requested information is not specified in the official guidelines or if you are unsure, reply strictly with: 'I am unable to answer this question as it is not specified in the official policy guidelines.'
```

---

## 4. Prompt Variations Comparison

### Test Matrix

| Query # | Input Query | Query Category | Variation 1 (Vague System Prompt) Output | Variation 2 (Constrained System Prompt) Output | Analysis / Output Difference |
|---|---|---|---|---|---|
| **1** | *"What is our refund window for employee software tool purchases?"* | Specific Policy Query | *"Our refund policy for employee software tool purchases allows employees to request a refund within 30 business days of purchase, provided that the receipt is submitted..."* (Rambling, unconstrained) | *"Employees can request a refund for software tool purchases within 30 days of purchase with manager approval. Submit the receipt via the finance portal to process the reimbursement."* (Concise, 2 sentences) | **Variation 2** strictly enforced the 2-sentence max constraint and maintained a direct, professional tone. |
| **2** | *"Can I claim a refund for my personal gym membership under health benefits?"* | Unspecified Policy Query | *"Yes, generally health benefits may cover wellness activities including gym memberships depending on your tier. You should check with HR..."* (Speculative, dangerous assumption) | *"I am unable to answer this question as it is not specified in the official policy guidelines."* (Clean refusal) | **Variation 1** hallucinates an answer. **Variation 2** triggers the fallback rule, preventing misinformation. |
| **3** | *"Who won the 2022 FIFA World Cup?"* | Out-of-Scope General Knowledge | *"Argentina won the 2022 FIFA World Cup in Qatar, defeating France in a dramatic penalty shootout..."* (Answers out of domain) | *"I am unable to answer this question as it is not specified in the official policy guidelines."* (Scope enforcement) | **Variation 1** ignores role boundary. **Variation 2** correctly refuses non-policy questions. |

---

## 5. Documenting the Chosen Prompt: Why Variation 2 Works

The **Constrained & Grounded System Prompt (Variation 2)** was selected as the optimal prompt for PolicyPilot for four key reasons:

1. **Explicit Role & Persona Boundaries**: Explicitly defining `PolicyPilot` prevents the model from acting as a general-purpose search engine or entertainment assistant.
2. **Scope Control & Refusal Mechanism**: Unspecified policy questions and out-of-scope topics trigger the predefined fallback response instead of generating plausibly-sounding hallucinations.
3. **Predictable Formatting & Length**: Setting a strict limit (`maximum 2 sentences`) prevents long winded, rambling output, making responses easier for employees to digest quickly.
4. **Grounding Readiness**: In a full RAG pipeline, enforcing fallback refusal behavior ensures the model relies exclusively on retrieved context rather than its pre-trained parametric memory.

---

## 6. How to Constrain Output Formats (JSON / Schema)

When software applications consume LLM outputs, unstructured text can break JSON parsers. To strictly constrain the model to a JSON format, provide explicit schema definitions in the system message:

```python
messages = [
    {
        "role": "system",
        "content": (
            "You are PolicyPilot, an internal policy assistant. "
            "Reply strictly with ONLY a valid JSON object matching this schema: "
            '{"answer": "<string>", "confidence": "<high|medium|low>", "refusal": <boolean>}. '
            "Do not include markdown backticks (```json) or conversational text outside the JSON object."
        )
    },
    {
        "role": "user",
        "content": "What is the refund window for software tools?"
    }
]
```

### Response Example:
```json
{
  "answer": "Employees can request a refund for software tools within 30 days of purchase with manager approval.",
  "confidence": "high",
  "refusal": false
}
```
