# PolicyPilot UI sample interaction

This sample interaction documents the expected browser experience for the Next.js RAG interface.

## Grounded question

**Question:** What is the dispatch SLA for sellers?

**Loading state:** After selecting **Send**, the button changes to `Generating...`, the input is disabled, and the assistant bubble shows an animated typing indicator while `POST http://localhost:8000/query` is in flight.

**Answer:**

> Sellers are required to dispatch ordered items within 2 business days.

**Retrieved sources:**

| Source | Chunk IDs | Relevance |
| --- | --- | --- |
| `policy.pdf` | `2` | `91.0%` |

The source panel is expandable and shows the document name, chunk IDs, relevance score, and any excerpt or link returned by the API. The answer is rendered separately from the source evidence so users can inspect the grounding.

## Error state

If the API is unavailable or returns an error, the assistant bubble shows a visible warning such as:

> Unable to connect to PolicyPilot RAG API server. Please check your backend connection.

The **Retry** button resubmits the original question without losing the user’s conversation history.
