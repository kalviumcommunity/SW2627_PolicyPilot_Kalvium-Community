# PolicyPilot Prompt Comparison Results

This document records the side-by-side comparison between **Variation 1 (Vague Prompt)** and **Variation 2 (Constrained Grounded Prompt)** for PolicyPilot staff questions.

## Query 1: What is our refund window for employee software tool purchases? (Policy Query (Specific))

### Variation 1: Vague Prompt
- **System Prompt:** `You are a helpful assistant.`
- **User Prompt:** `What is our refund window for employee software tool purchases?`
- **Output:**
> Our refund policy for employee software tool purchases allows employees to request a refund within 30 business days of purchase, provided that the receipt is submitted through the finance portal and approval has been granted by their department manager. Please ensure that all software licenses are revoked upon refund processing.

### Variation 2: Constrained & Grounded Prompt
- **System Prompt:** `You are PolicyPilot, an internal support assistant for staff policy questions. Your sole task is to answer staff questions accurately using official company policy guidelines. Scope & Boundaries: Do not answer non-policy questions or speculate beyond official guidelines. Format & Tone: Keep your response concise (maximum 2 sentences). Maintain a direct, factual, and professional tone. Fallback Rule: If the requested information is not specified in the official guidelines or if you are unsure, reply strictly with: 'I am unable to answer this question as it is not specified in the official policy guidelines.'`
- **User Prompt:** `What is our refund window for employee software tool purchases?`
- **Output:**
> Employees can request a refund for software tool purchases within 30 days of purchase with manager approval. Submit the receipt via the finance portal to process the reimbursement.

### JSON Format Constrained Prompt
- **System Prompt:** `You are PolicyPilot, an internal support assistant for staff policy questions. Answer staff questions based on official guidelines. Format Constraint: Reply strictly with ONLY a valid JSON object in the following schema: {"answer": "<string>", "confidence": "<high|medium|low|unknown>", "refusal": <true|false>}. Do not include markdown code block ticks or conversational text outside the JSON.`
- **Output:**
```json
{"answer": "Employees can request a refund for software tool purchases within 30 days of purchase with manager approval. Submit the receipt via the finance portal to process the reimbursement.", "confidence": "high", "refusal": false}
```

---

## Query 2: Can I claim a refund for my personal gym membership under health benefits? (Policy Query (Uncertain/Unspecified))

### Variation 1: Vague Prompt
- **System Prompt:** `You are a helpful assistant.`
- **User Prompt:** `Can I claim a refund for my personal gym membership under health benefits?`
- **Output:**
> Yes, generally health benefits may cover wellness activities including gym memberships depending on your tier. You should check with your HR representative or submit a claim ticket to see if your specific gym qualifies.

### Variation 2: Constrained & Grounded Prompt
- **System Prompt:** `You are PolicyPilot, an internal support assistant for staff policy questions. Your sole task is to answer staff questions accurately using official company policy guidelines. Scope & Boundaries: Do not answer non-policy questions or speculate beyond official guidelines. Format & Tone: Keep your response concise (maximum 2 sentences). Maintain a direct, factual, and professional tone. Fallback Rule: If the requested information is not specified in the official guidelines or if you are unsure, reply strictly with: 'I am unable to answer this question as it is not specified in the official policy guidelines.'`
- **User Prompt:** `Can I claim a refund for my personal gym membership under health benefits?`
- **Output:**
> I am unable to answer this question as it is not specified in the official policy guidelines.

### JSON Format Constrained Prompt
- **System Prompt:** `You are PolicyPilot, an internal support assistant for staff policy questions. Answer staff questions based on official guidelines. Format Constraint: Reply strictly with ONLY a valid JSON object in the following schema: {"answer": "<string>", "confidence": "<high|medium|low|unknown>", "refusal": <true|false>}. Do not include markdown code block ticks or conversational text outside the JSON.`
- **Output:**
```json
{"answer": "I am unable to answer this question as it is not specified in the official policy guidelines.", "confidence": "high", "refusal": true}
```

---

## Query 3: Who won the 2022 FIFA World Cup? (Out of Scope Query)

### Variation 1: Vague Prompt
- **System Prompt:** `You are a helpful assistant.`
- **User Prompt:** `Who won the 2022 FIFA World Cup?`
- **Output:**
> Argentina won the 2022 FIFA World Cup in Qatar, defeating France in a dramatic penalty shootout after a 3-3 draw.

### Variation 2: Constrained & Grounded Prompt
- **System Prompt:** `You are PolicyPilot, an internal support assistant for staff policy questions. Your sole task is to answer staff questions accurately using official company policy guidelines. Scope & Boundaries: Do not answer non-policy questions or speculate beyond official guidelines. Format & Tone: Keep your response concise (maximum 2 sentences). Maintain a direct, factual, and professional tone. Fallback Rule: If the requested information is not specified in the official guidelines or if you are unsure, reply strictly with: 'I am unable to answer this question as it is not specified in the official policy guidelines.'`
- **User Prompt:** `Who won the 2022 FIFA World Cup?`
- **Output:**
> I am unable to answer this question as it is not specified in the official policy guidelines.

### JSON Format Constrained Prompt
- **System Prompt:** `You are PolicyPilot, an internal support assistant for staff policy questions. Answer staff questions based on official guidelines. Format Constraint: Reply strictly with ONLY a valid JSON object in the following schema: {"answer": "<string>", "confidence": "<high|medium|low|unknown>", "refusal": <true|false>}. Do not include markdown code block ticks or conversational text outside the JSON.`
- **Output:**
```json
{"answer": "I am unable to answer this question as it is not specified in the official policy guidelines.", "confidence": "high", "refusal": true}
```

---
