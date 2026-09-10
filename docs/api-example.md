# PolicyPilot query API

Start the API from the repository root after configuring `.env`:

```powershell
python -m uvicorn src.api:app --host 127.0.0.1 --port 8000
```

## Sample request

```powershell
Invoke-RestMethod `
  -Uri http://127.0.0.1:8000/query `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"question":"How much is the monthly internet allowance?"}'
```

## Sample response

```json
{
  "status": "success",
  "question": "How much is the monthly internet allowance?",
  "answer": "Employees can claim up to $75 per month for high-speed home internet service under the internet allowance. [Source: stipend_faq.html]",
  "sources": [
    {
      "document": "stipend_faq.html",
      "score": 0.84,
      "chunks": [0]
    }
  ],
  "metadata": {
    "model": "configured-from-CHAT_MODEL",
    "top_k": 3,
    "retrieved_chunks": 1,
    "is_fallback": false,
    "latency_ms": 42.31
  }
}
```

The model name in a real response is read from `CHAT_MODEL`; no credential is returned.

Invalid requests receive `422 Unprocessable Entity` (for example, a missing, blank, or overlong `question`). Unexpected pipeline failures receive `500 Internal Server Error` without exposing provider details.
