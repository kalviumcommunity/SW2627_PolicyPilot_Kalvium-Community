# Token-Aware Chunk Sizing & Overlap Report

This report documents the design, implementation, settings justification, and boundary-context preservation results of PolicyPilot's token-aware chunker.

## Task 1 & 2: Chunker Setup

- **Tokenizer:** `tiktoken` (utilizing the `cl100k_base` encoding family)
- **Standard Production Settings:**
  - **Chunk Size:** `400` tokens
  - **Chunk Overlap:** `60` tokens (15% overlap)

### Corpus Chunking Results (Demo Settings: Size=35, Overlap=10)

The corpus files were successfully loaded, cleaned, and chunked with token-aware limits:

| Source File | Chunk Index | Token Count | Start Token | End Token | Chunk Preview |
| --- | --- | --- | --- | --- | --- |
| `remote_policy.txt` | 0 | 35 | 0 | 35 | Company Remote Work Policy Effective: January 1, 2026  Eligi... |
| `remote_policy.txt` | 1 | 21 | 25 | 46 | three days per week. Employees must maintain standard core... |
| `sample_policy.pdf` | 0 | 35 | 0 | 35 | PolicyPilot Official Travel Reimbursement Guidelines 1. Trav... |
| `sample_policy.pdf` | 1 | 15 | 25 | 40 | . All flights must be booked in economy class unless approve... |
| `stipend_faq.html` | 0 | 35 | 0 | 35 | Stipend FAQ Stipend & Reimbursement FAQ Q: What can I claim... |
| `stipend_faq.html` | 1 | 16 | 25 | 41 | You can claim up to $75 per month for high-speed home inter... |
| `work_hours.md` | 0 | 35 | 0 | 35 | # Work Hours and Overtime Guideline  All remote workers must... |
| `work_hours.md` | 1 | 30 | 25 | 55 | system. - Standard hours: 8 hours per day, 40 hours per wee... |

## Task 3: Boundary Context Preservation Demonstration

To show the effect of overlap, we chunked a sample text containing a critical boundary policy statement.

**Sample Text:**
> PolicyPilot Guidelines for Workplace Safety and Environment. 1. Fire Hazards: All hallways must remain completely clear of any obstructions, including delivery boxes. 2. Standard Working Hours: The core team operates under the Flexible Hours Program (FHP), which mandates core hours of 10 AM to 3 PM for synchronous collaboration. 3. Travel Reimbursements: Employees traveling on official business can claim a meal allowance of up to fifty dollars per day.

We compared splitting with **Size=25, Overlap=0** vs **Size=25, Overlap=8**.

### Without Overlap (Overlap = 0)

| Chunk | Token Count | Range | Text Content |
| --- | --- | --- | --- |
| Chunk 0 | 25 | 0:25 | `PolicyPilot Guidelines for Workplace Safety and Environment. 1. Fire Hazards: All hallways must remain completely clear of` |
| Chunk 1 | 25 | 25:50 | `any obstructions, including delivery boxes. 2. Standard Working Hours: The core team operates under the Flexible Hours Program (` |
| Chunk 2 | 25 | 50:75 | `FHP), which mandates core hours of 10 AM to 3 PM for synchronous collaboration. 3. Travel Reim` |
| Chunk 3 | 21 | 75:96 | `bursements: Employees traveling on official business can claim a meal allowance of up to fifty dollars per day.` |

### With Overlap (Overlap = 8)

| Chunk | Token Count | Range | Text Content |
| --- | --- | --- | --- |
| Chunk 0 | 25 | 0:25 | `PolicyPilot Guidelines for Workplace Safety and Environment. 1. Fire Hazards: All hallways must remain completely clear of` |
| Chunk 1 | 25 | 17:42 | `All hallways must remain completely clear of any obstructions, including delivery boxes. 2. Standard Working Hours: The core` |
| Chunk 2 | 25 | 34:59 | `2. Standard Working Hours: The core team operates under the Flexible Hours Program (FHP), which mandates core hours of` |
| Chunk 3 | 25 | 51:76 | `HP), which mandates core hours of 10 AM to 3 PM for synchronous collaboration. 3. Travel Reimburse` |
| Chunk 4 | 25 | 68:93 | `. 3. Travel Reimbursements: Employees traveling on official business can claim a meal allowance of up to fifty dollars` |
| Chunk 5 | 11 | 85:96 | `a meal allowance of up to fifty dollars per day.` |

### Preservation Analysis

- Target Phrase: `Flexible Hours Program (FHP)`
- **Intact without overlap?** No (phrase is split across chunk boundaries)
- **Intact with overlap?** Yes (Found in **Chunk 2**)

**Visual Explanation:**
Without overlap, Chunk 1 ends at token index 50 (`... Flexible Hours Program (`) and Chunk 2 starts at 50 (`FHP), which mandates ...`). The phrase is sliced in half.
With overlap, Chunk 2 steps back by 8 tokens and starts at index 42 (`team operates under...`), pulling the text `Flexible Hours Program (` back into the chunk. This preserves the phrase `Flexible Hours Program (FHP)` intact in Chunk 2, enabling accurate semantic indexing and retrieval.

## Task 4: Chunker Settings Justification

For our target model (e.g., Gemini 3.5 Flash / Gemini Pro), we justify a chunk size of **400 tokens** and an overlap of **60 tokens** (15%) based on the following engineering trade-offs:

1. **Context Window Compatibility:**
   - Gemini 1.5/3.5 models support up to 1-2 million tokens, easily fitting massive retrieval prompts.
   - However, using smaller, high-relevance chunks (e.g., top-k=5 of 400-token chunks = 2,000 tokens) keeps the prompt focused, reduces irrelevant noise ('needle in a haystack' distraction), and reduces API latency.
2. **Embedding Model Constraints:**
   - Most vector database embedding models (like OpenAI `text-embedding-3-small` or Google `text-embedding-004`) have a max input constraint of 512 or 8192 tokens.
   - A chunk size of 400 tokens fits safely within these limits without truncation, ensuring complete representation of every chunk in the vector database.
3. **Cost vs Context Preservation:**
   - A 15% overlap (60 tokens) represents an optimal trade-off: it increases storage and token indexing cost by only 15%, but completely covers standard English sentence lengths (typically 15-30 tokens). This ensures that sentences falling on chunk boundaries are fully preserved in at least one chunk.
4. **Interaction with Top-k and Context Window:**
   - A smaller chunk size (e.g., 200 tokens) allows a higher `top-k` (retrieving more distinct sections of text), but risks lacking sufficient local context within each chunk.
   - A larger chunk size (e.g., 1000 tokens) provides deep context but reduces the variety of sources we can retrieve within a given context budget.
   - **400 tokens** strikes a perfect balance: it is large enough to contain a complete sub-section or multi-step guideline, while leaving the prompt light enough to retrieve 5 to 10 chunks simultaneously.