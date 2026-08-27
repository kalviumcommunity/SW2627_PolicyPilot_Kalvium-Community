# PolicyPilot Model Parameter Tuning Guide

## 1. Overview & Purpose

In a Retrieval-Augmented Generation (RAG) assistant, model parameters serve as critical dials for balancing **factual grounding**, **determinism**, **latency**, and **token cost**. 

While system prompts define *what* rules the assistant must follow, decoding parameters control *how* the language model samples tokens from its probability distribution.

This document details:
1. The impact of **Temperature** on output determinism vs. creativity.
2. The role of **`max_tokens`** in capping length and controlling API budget.
3. The function of **`stop` sequences** and **`top_p` (Nucleus Sampling)**.
4. Recommended production configuration for grounded, factual RAG applications.

---

## 2. Temperature: Determinism vs. Variance (Task 1)

**Temperature** rescales the logit values (raw output scores of vocabulary tokens) prior to applying softmax normalization:

$$P(w_i) = \frac{\exp(z_i / T)}{\sum_j \exp(z_j / T)}$$

- **When $T = 0.0$ (Greedy Decoding / Deterministic Mode)**:
  - The model greedily selects the highest-probability token at every step.
  - Repeated calls with the exact same prompt produce **identical, 100% reproducible responses**.
  - **Best for:** RAG search engines, customer support bots, policy compliance, and automated testing.

- **When $T = 0.7 - 1.2$ (Stochastic / Creative Mode)**:
  - Token probability distributions are flattened, increasing the likelihood of selecting lower-probability tokens.
  - Sequential runs produce **varied phrasing, creative metaphors, and structural divergence**.
  - **Risk:** High temperatures increase the probability of introducing hallucinated statements not supported by context.

### Side-by-Side Comparison

| Temperature Setting | Run 1 Output | Run 2 Output | Behavior Analysis |
|---|---|---|---|
| **$T = 0.0$ (Deterministic)** | *"Employees can request a refund for software tool purchases within 30 days of purchase with manager approval. Submit the receipt via the finance portal to process the reimbursement."* | *"Employees can request a refund for software tool purchases within 30 days of purchase with manager approval. Submit the receipt via the finance portal to process the reimbursement."* | **100% Identical Across Runs.** Factual, grounded, predictable. |
| **$T = 0.7$ (Balanced)** | *"Staff members are eligible for a reimbursement on software purchases within a 30-day timeframe upon supervisor consent. Please upload your itemized invoice to the internal portal."* | *"Our standard policy allows software tool purchase refunds up to 30 days post-purchase. Ensure your department manager signs off before submitting receipts."* | **Varied Phrasing.** Semantically similar, but syntax and word choice fluctuate. |
| **$T = 1.2$ (High Randomness)** | *"Feel free to claim software refund claims inside 30 calendar days window with line manager authorization! Receipt uploads must occur through the finance portal endpoint."* | *"Software refund claims can be processed inside a 30-day window provided line managers authorize the transaction via the web portal."* | **High Entropy.** Unpredictable vocabulary; risk of hallucinating policy conditions. |

---

## 3. Max Tokens: Length Capping & Budget Control (Task 2)

The **`max_tokens`** parameter establishes a hard upper boundary on the number of completion tokens generated in a single API response.

### Key Characteristics
1. **Cost & Latency Safeguard**: Prevents runaway loops or unexpected expensive completions.
2. **Truncation Indicator**: When generation hits the `max_tokens` cap, the API returns `finish_reason: "length"`.

### Length Capping Experiments

| `max_tokens` Setting | Observed Completion Output | `finish_reason` | Result / Assessment |
|---|---|---|---|
| **`max_tokens = 15`** | *"Employees can request a refund for software tool purchases within"* | `"length"` | **Abruptly Truncated.** Output cut mid-sentence due to tight token ceiling. |
| **`max_tokens = 40`** | *"Employees can request a refund for software tool purchases within 30 days of purchase with manager approval."* | `"stop"` | **Complete Sentence.** Sufficient tokens for single-sentence answers. |
| **`max_tokens = 150`** | *"Employees can request a refund for software tool purchases within 30 days of purchase with manager approval. Submit the receipt via the finance portal to process the reimbursement."* | `"stop"` | **Full Response.** Complete 2-sentence response delivered comfortably within budget limit. |

---

## 4. Additional Parameters: Stop Sequences & Top_P (Task 3)

### A. Stop Sequences (`stop`)
The `stop` parameter specifies one or more delimiter strings (e.g. `["."]`, `["\n"]`, `["###"]`). When the model encounters any specified stop string, it halts token generation immediately and returns `finish_reason: "stop"`.

- **`stop=["."]`**: Halts immediately after completing the very first sentence.
- **`stop=["\n"]`**: Halts generation at the first line break (useful for single-line inputs or bullet items).

### B. Top_P / Nucleus Sampling (`top_p`)
Nucleus sampling restricts candidate token selection to the smallest cumulative probability set exceeding $p$:

- **`top_p = 0.1`**: Considers only the top 10% probability mass tokens. Produces focused, factual completions.
- **`top_p = 0.9`**: Considers top 90% probability mass tokens. Enables diverse, wide vocabulary completions.

> **Best Practice Note:** OpenAI recommends adjusting **either** `temperature` or `top_p`, but not both simultaneously.

---

## 5. Recommended Settings Blueprint for Grounded RAG Tasks (Task 4)

For PolicyPilot's grounded policy Q&A system, we recommend the following production parameters:

```python
GROUNDED_RAG_PARAMETERS = {
    "temperature": 0.0,    # Guarantees deterministic, reproducible, factual outputs
    "max_tokens": 150,     # Caps response length to ~100-120 words; prevents unexpected token costs
    "top_p": 0.1,          # Constrains vocabulary sampling to high-confidence candidate tokens
    "stop": None,          # Allows model to complete output sentences naturally
}
```

### Rationale
1. **Zero Variance (`temperature=0.0`)**: Ensures two employees asking the exact same policy question receive the identical policy answer.
2. **Budget Capping (`max_tokens=150`)**: Prevents long-winded answers and keeps cloud API costs predictable.
3. **High Confidence (`top_p=0.1`)**: Eliminates low-probability token paths that cause subtle policy misstatements.
