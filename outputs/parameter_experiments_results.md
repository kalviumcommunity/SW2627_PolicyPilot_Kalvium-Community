# PolicyPilot Model Parameter Experiments

**Test Question:** `What is our refund policy and window for employee software tool purchases?`

## Task 1: Temperature Experiments (0.0 vs 0.7 vs 1.2)

### Temperature = 0.0 (Deterministic & repeatable)
- **Run 1:**
  > Here's a thinking process:

1.  **Analyze User Input:**
   - Question: "What is our refund policy and window for employee software tool purchases?"
   - Topic: Refund policy and window for employee software tool purchases
   - Role: PolicyPilot (internal support assistant for staff policy questions)
   - Constraints: 
     - Answer accurately using official company policy guidelines
     - Do not answer non-policy questions or speculate
     - Keep response concise (max 2 sentences)
     - Maintain direct, factual, professional tone
     - Fallback rule: If not specified in guidelines or unsure, reply strictly with: 'I am unable to answer this question as it is not specified in the official policy guidelines.'

2.  **Check Constraints & Knowledge:**
   - I don't have access to the actual "official company policy guidelines" in this prompt. The prompt doesn't provide them.
   - According to the fallback rule, if the information is not specified in the official guidelines or if I'm unsure, I must reply strictly with the exact fallback phrase.
   - Since I don't have the policy document, I must use the fallback.

3.  **Formulate Response:**
   - Must be exactly: "I am unable to answer this question as it is not specified in the official policy guidelines."
   - Check constraints: Max 2 sentences? Yes (1 sentence). Direct/factual/prof

- **Run 2:**
  > Here's a thinking process:

1.  **Analyze User Input:**
   - Question: "What is our refund policy and window for employee software tool purchases?"
   - Topic: Refund policy and window for employee software tool purchases
   - Role: PolicyPilot (internal support assistant for staff policy questions)
   - Constraints: 
     - Answer accurately using official company policy guidelines
     - Do not answer non-policy questions or speculate
     - Keep response concise (max 2 sentences)
     - Maintain direct, factual, professional tone
     - Fallback rule: If not specified in guidelines or unsure, reply strictly with: 'I am unable to answer this question as it is not specified in the official policy guidelines.'

2.  **Check Constraints & Knowledge:**
   - I don't have access to the actual "official company policy guidelines" in this prompt. The prompt doesn't provide them.
   - According to the fallback rule, if the information is not specified in the official guidelines or if I'm unsure, I must reply strictly with the exact fallback phrase.
   - Since I don't have the policy document, I must use the fallback.

3.  **Formulate Response:**
   - Must be exactly: "I am unable to answer this question as it is not specified in the official policy guidelines."
   - Check constraints: Max 2 sentences? Yes (1 sentence). Direct/factual/prof

### Temperature = 0.7 (Balanced creativity)
- **Run 1:**
  > Here's a thinking process:

1.  **Analyze User Input:**
   - Question: "What is our refund policy and window for employee software tool purchases?"
   - Context: Staff policy question about refunds for software purchases.
   - Role: PolicyPilot, internal support assistant for staff policy questions.
   - Constraints: 
     - Sole task: Answer accurately using official company policy guidelines.
     - Scope: Do not answer non-policy questions or speculate.
     - Format/Tone: Concise (max 2 sentences), direct, factual, professional.
     - Fallback: If not specified in guidelines or unsure, reply strictly with: 'I am unable to answer this question as it is not specified in the official policy guidelines.'

2.  **Identify Missing Information:**
   - I don't have access to the actual "official company policy guidelines" in this prompt. The user hasn't provided them, and I'm an AI without external database access to specific company policies.
   - According to the fallback rule, if the information is not specified in the official guidelines or I'm unsure, I must reply strictly with the exact fallback phrase.

3.  **Apply Constraints:**
   - Since I don't have the policy details, I must use the fallback response.
   - Check fallback exact wording: 'I am unable to answer this question as it is not specified in the official policy guidelines.'
   -

- **Run 2:**
  > Here's a thinking process:

1.  **Analyze User Input:**
   - Question: "What is our refund policy and window for employee software tool purchases?"
   - Context: Internal staff policy question about refund policy/window for software tool purchases.

2.  **Check Constraints:**
   - Role: PolicyPilot, internal support assistant for staff policy questions.
   - Scope: Only answer using official company policy guidelines. Do not answer non-policy questions or speculate.
   - Format & Tone: Concise (max 2 sentences). Direct, factual, professional.
   - Fallback Rule: If not specified in guidelines or unsure, reply strictly with: "I am unable to answer this question as it is not specified in the official policy guidelines."

3.  **Evaluate Knowledge/Context:**
   - I do not have access to the user's specific "official company policy guidelines." As an AI, I don't have internal company documents unless provided in the prompt. The prompt doesn't include any policy text.
   - Therefore, I must apply the fallback rule.

4.  **Apply Fallback Rule:**
   - Required exact response: "I am unable to answer this question as it is not specified in the official policy guidelines."

5.  **Check Constraints against Fallback:**
   - Matches fallback exactly.
   - Within max 2 sentences (1 sentence).
   - Direct, factual, professional

### Temperature = 1.2 (High randomness & variance)
- **Run 1:**
  > Here's a thinking process:

1.  **Analyze User Input:**
   - Question: "What is our refund policy and window for employee software tool purchases?"
   - Topic: Refund policy and time window for software tool purchases for employees.

2.  **Check Constraints:**
   - Role: PolicyPilot, internal support assistant for staff policy questions.
   - Scope: Answer accurately using official company policy guidelines. Do not answer non-policy questions or speculate.
   - Format/Tone: Concise (max 2 sentences), direct, factual, professional.
   - Fallback Rule: If info not in guidelines or unsure, reply strictly: "I am unable to answer this question as it is not specified in the official policy guidelines."

3.  **Identify Missing Information:**
   - I don't have access to the specific "official company policy guidelines" provided in the prompt or context. The prompt only gives me my role and constraints, but no actual policy document or knowledge base.
   - Since I cannot verify the specific refund policy and window without official guidelines, I must trigger the fallback rule.

4.  **Apply Fallback Rule:**
   - The prompt explicitly says: "If the requested information is not specified in the official guidelines or if you are unsure, reply strictly with: 'I am unable to answer this question as it is not specified in the official policy guidelines.'"
   - I will output

- **Run 2:**
  > Employees can request a refund for software tool purchases within 30 days of purchase with manager approval. Submit the receipt via the finance portal to process the reimbursement.

## Task 2: Max Tokens Length Capping (15 vs 40 vs 150)

### `max_tokens` = 20
- **Finish Reason:** `length`
- **Truncated:** `True`
- **Output:**
  > Employees can request a refund for software tool purchases within 30 days of purchase with manager approval. Submit the receipt via the finance portal to process the reimbursement.

### `max_tokens` = 60
- **Finish Reason:** `stop`
- **Truncated:** `False`
- **Output:**
  > Employees can request a refund for software tool purchases within 30 days of purchase with manager approval. Submit the receipt via the finance portal to process the reimbursement.

### `max_tokens` = 300
- **Finish Reason:** `stop`
- **Truncated:** `False`
- **Output:**
  > Employees can request a refund for software tool purchases within 30 days of purchase with manager approval. Submit the receipt via the finance portal to process the reimbursement.

## Task 3: Stop Sequence Experiments

### No Stop Sequence (`stop=None`)
- **Finish Reason:** `stop`
- **Output:**
  > Employees can request a refund for software tool purchases within 30 days of purchase with manager approval. Submit the receipt via the finance portal to process the reimbursement.

### Stop on Period ('.') (`stop=['.']`)
- **Finish Reason:** `stop`
- **Output:**
  > Employees can request a refund for software tool purchases within 30 days of purchase with manager approval

### Stop on Newline ('\n') (`stop=['\n']`)
- **Finish Reason:** `stop`
- **Output:**
  > Employees can request a refund for software tool purchases within 30 days of purchase with manager approval. Submit the receipt via the finance portal to process the reimbursement.

## Task 3: Top_P (Nucleus Sampling) Experiments

### `top_p` = 0.1 (Narrow top 10% token sampling (focused))
- **Output:**
  > Employees can request a refund for software tool purchases within 30 days of purchase with manager approval. Submit the receipt via the finance portal to process the reimbursement.

### `top_p` = 0.9 (Broad top 90% token sampling (diverse))
- **Output:**
  > Employees may apply for a reimbursement regarding company software tool expenses within thirty days of buying them. Remember to attach your receipt.

## Task 4: Recommended Grounded Task Configuration Blueprint

```python
RECOMMENDED_GROUNDED_CONFIG = {
    'temperature': 0.0,    # Deterministic & repeatable, eliminates randomness
    'max_tokens': 150,     # Prevents unexpected token usage costs
    'top_p': 0.1,           # Narrow nucleus sampling focusing on high-probability tokens
    'stop': None,             # Optional delimiter list for structured output truncation
}
```
