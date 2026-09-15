"""
PolicyPilot Standalone API Server
==================================
A self-contained HTTP server that loads policy documents from data/
and returns grounded, citation-backed answers. No MongoDB, no broken imports.

Run with:
    python policy_api.py
    
Endpoints:
    GET  /health
    POST /query          { "question": "..." }
    POST /query/stream   { "question": "..." }  (SSE)
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, List, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
logger = logging.getLogger("policy_api")

PROJECT_ROOT = Path(__file__).resolve().parent
USERS_FILE = PROJECT_ROOT / "data" / "users.json"

# ── Optional: load OPENAI / Groq key from .env ──────────────────────────────
def _load_env():
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

_load_env()

# ─────────────────────────────────────────────────────────────────────────────
# 1. POLICY DOCUMENT LOADER
# ─────────────────────────────────────────────────────────────────────────────

SUPPORTED = {".txt", ".md", ".html", ".htm"}


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text)


def _load_file(path: Path) -> str:
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
        if path.suffix.lower() in (".html", ".htm"):
            raw = _strip_html(raw)
        return raw
    except Exception as e:
        logger.warning("Could not read %s: %s", path.name, e)
        return ""


def load_policy_chunks() -> List[Dict[str, Any]]:
    """Load all policy files from data/ into paragraph-level chunks."""
    data_dir = PROJECT_ROOT / "data"
    chunks: List[Dict[str, Any]] = []
    idx = 0

    if data_dir.exists():
        for fp in sorted(data_dir.glob("*.*")):
            if fp.suffix.lower() not in SUPPORTED:
                continue
            text = _load_file(fp)
            if not text.strip():
                continue
            # Split into paragraphs
            paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
            for para in paragraphs:
                # Determine section header
                first_line = para.splitlines()[0].strip()
                if re.match(r"^#{1,4}\s+", first_line):
                    section = re.sub(r"^#{1,4}\s+", "", first_line).strip()
                elif re.match(r"^(SECTION|POLICY|[A-Z ]{6,})", first_line):
                    section = first_line
                else:
                    section = "General Policy"
                chunks.append({
                    "id": f"{fp.stem}:{idx}",
                    "source": fp.name,
                    "chunk_index": idx,
                    "section": section,
                    "text": para,
                })
                idx += 1
            logger.info("Loaded %s → %d paragraphs", fp.name, len(paragraphs))

    if not chunks:
        # Built-in fallback if no data files
        logger.warning("No data files found — using built-in fallback policies")
        chunks = [
            {"id": "fallback:0", "source": "RETURN_POLICY", "chunk_index": 0,
             "section": "Return Window",
             "text": "Customers can return eligible items within 30 days of delivery. Items must be unused and in original packaging."},
            {"id": "fallback:1", "source": "RETURN_POLICY", "chunk_index": 1,
             "section": "Damaged Products",
             "text": "Damaged or defective products must be reported within 48 hours of delivery. A free pick-up and replacement or full refund will be arranged."},
            {"id": "fallback:2", "source": "SHIPPING_POLICY", "chunk_index": 2,
             "section": "Standard Delivery",
             "text": "Standard delivery takes 4-7 business days. Free shipping on orders above Rs 499."},
            {"id": "fallback:3", "source": "SELLER_POLICY", "chunk_index": 3,
             "section": "Dispatch SLA",
             "text": "Sellers must dispatch ordered items within 2 business days of order confirmation."},
            {"id": "fallback:4", "source": "CANCELLATION_POLICY", "chunk_index": 4,
             "section": "Cancellation Window",
             "text": "Orders can be cancelled within 1 hour of placement at no charge."},
            {"id": "fallback:5", "source": "PAYMENT_POLICY", "chunk_index": 5,
             "section": "Accepted Payments",
             "text": "Accepted payments: Credit/Debit Cards, UPI, Net Banking, EMI, COD (up to Rs 50,000), ShopVerse Wallet."},
        ]

    logger.info("Total chunks: %d", len(chunks))
    return chunks


# ── Singleton chunk store ─────────────────────────────────────────────────────
_CHUNKS: List[Dict[str, Any]] = []


def get_chunks() -> List[Dict[str, Any]]:
    global _CHUNKS
    if not _CHUNKS:
        _CHUNKS = load_policy_chunks()
    return _CHUNKS


def load_users() -> List[Dict[str, Any]]:
    """Load the configured user records without inventing marketplace data."""
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


def make_token(user: Dict[str, Any]) -> str:
    payload = json.dumps({"sub": user.get("email"), "role": user.get("role")}, separators=(",", ":"))
    import base64
    encoded = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
    return f"policy.{encoded}.local"


# ─────────────────────────────────────────────────────────────────────────────
# 2. RETRIEVAL — simple TF-style keyword scoring
# ─────────────────────────────────────────────────────────────────────────────

_STOP = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "i", "my", "me", "we", "our",
    "you", "your", "it", "its", "this", "that", "these", "those", "what",
    "how", "when", "where", "why", "who", "which", "for", "of", "in", "on",
    "at", "by", "with", "about", "from", "to", "and", "or", "but", "not",
    "no", "so", "if", "then", "than", "as", "up", "out", "get", "go",
}


def _tokenize(text: str) -> List[str]:
    tokens = re.findall(r"[a-z]+", text.lower())
    return [t for t in tokens if t not in _STOP and len(t) > 2]


def retrieve(question: str, top_k: int = 5) -> List[Dict[str, Any]]:
    q_tokens = set(_tokenize(question))
    all_chunks = get_chunks()

    # Filter out heading-only chunks (very short, mostly a title line)
    content_chunks = [c for c in all_chunks if len(c["text"].split()) > 8]
    if not content_chunks:
        content_chunks = all_chunks

    if not q_tokens:
        return content_chunks[:top_k]

    scored: List[Tuple[float, Dict]] = []
    for chunk in content_chunks:
        chunk_tokens = _tokenize(chunk["text"] + " " + chunk["section"])
        if not chunk_tokens:
            continue
        overlap = q_tokens & set(chunk_tokens)
        # TF-overlap score
        score = len(overlap) / (len(q_tokens) + 0.001)
        # Boost exact phrase matches in text
        if question.lower() in chunk["text"].lower():
            score += 0.8
        # Boost section name matches
        sec_tokens = set(_tokenize(chunk["section"]))
        sec_overlap = q_tokens & sec_tokens
        score += len(sec_overlap) * 0.3
        scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = [c for s, c in scored[:top_k] if s > 0]
    if not results:
        results = content_chunks[:top_k]
    return results


# ─────────────────────────────────────────────────────────────────────────────
# 3. ANSWER GENERATION
# ─────────────────────────────────────────────────────────────────────────────

def _try_llm_answer(question: str, context: str) -> str | None:
    """Try to generate an answer using OpenAI API if key is available."""
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    try:
        import urllib.request
        import urllib.error

        is_groq = bool(os.getenv("GROQ_API_KEY")) and not os.getenv("OPENAI_API_KEY")
        url = "https://api.groq.com/openai/v1/chat/completions" if is_groq else "https://api.openai.com/v1/chat/completions"
        model = os.getenv("CHAT_MODEL", "mixtral-8x7b-32768" if is_groq else "gpt-3.5-turbo")

        system_prompt = (
            "You are PolicyPilot, ShopVerse's AI assistant. "
            "Answer the customer's question ONLY using the provided policy context. "
            "Be specific, cite exact policy details (timeframes, amounts, conditions). "
            "If the answer is not in the context, say so clearly. "
            "Keep the answer concise and helpful (2-4 sentences)."
        )

        payload = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Policy Context:\n{context}\n\nCustomer Question: {question}"},
            ],
            "max_tokens": 400,
            "temperature": 0.2,
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.warning("LLM call failed: %s", e)
        return None


def build_grounded_answer(question: str, chunks: List[Dict[str, Any]]) -> Tuple[str, List[Dict]]:
    """Build a grounded answer from retrieved policy chunks."""
    if not chunks:
        return ("I could not find relevant policy information for your question. "
                "Please contact ShopVerse support at support@shopverse.in.", [])

    # Build context string
    context_parts = []
    for i, c in enumerate(chunks, 1):
        context_parts.append(f"[{i}] {c['section']} ({c['source']}):\n{c['text']}")
    context = "\n\n".join(context_parts)

    # Try LLM first
    llm_answer = _try_llm_answer(question, context)
    if llm_answer:
        answer = llm_answer
    else:
        # Fallback: rule-based extraction
        answer = _rule_based_answer(question, chunks)

    # Build source list
    sources = [
        {
            "marker": str(i + 1),
            "source": c["source"],
            "section": c["section"],
            "chunk_index": c["chunk_index"],
            "text": c["text"][:200] + ("..." if len(c["text"]) > 200 else ""),
        }
        for i, c in enumerate(chunks[:3])
    ]

    return answer, sources


def _rule_based_answer(question: str, chunks: List[Dict]) -> str:
    """Generate a direct, grounded answer from the top retrieved policy chunks."""
    q_lower = question.lower()
    q_tokens = set(_tokenize(question))

    # Intent detection
    intent_keywords = [
        (("return", "refund", "money back", "send back", "exchange"), "return"),
        (("deliver", "shipping", "ship", "days", "arrive", "track", "dispatch"), "ship"),
        (("cancel", "cancellation"), "cancel"),
        (("seller", "vendor", "commission", "penalty"), "seller"),
        (("payment", "pay", "cod", "upi", "emi", "card", "wallet", "bank"), "payment"),
        (("support", "contact", "help", "complaint", "grievance", "escalat"), "support"),
        (("damage", "defect", "broken", "faulty"), "damage"),
        (("privacy", "data", "personal"), "privacy"),
        (("prohibit", "banned", "not allowed", "illegal"), "prohibited"),
    ]
    intent = None
    for keywords, tag in intent_keywords:
        if any(kw in q_lower for kw in keywords):
            intent = tag
            break

    # Re-score chunks for primary selection
    def score_chunk(c: Dict) -> float:
        combined = (c["text"] + " " + c["section"]).lower()
        s = float(sum(1 for t in q_tokens if t in combined))
        if intent and intent in combined:
            s += 4
        return s

    ranked_chunks = sorted(chunks, key=score_chunk, reverse=True)
    primary = ranked_chunks[0]

    # Clean markdown from text
    clean_text = re.sub(r"^#{1,4}\s+.*$", "", primary["text"], flags=re.MULTILINE).strip()
    clean_text = re.sub(r"\*+", "", clean_text).strip()

    # Extract best sentences
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean_text) if len(s.strip()) > 15]
    sent_scored = sorted(
        sentences,
        key=lambda s: sum(1 for t in q_tokens if t in s.lower()),
        reverse=True,
    )
    best_sentences = sent_scored[:3]
    # Restore original order for readability
    ordered = [s for s in sentences if s in best_sentences][:3]
    excerpt = " ".join(ordered) if ordered else clean_text[:400]

    source_ref = f"[{primary['section']} — {primary['source']}]"
    answer = f"{excerpt}\n\n{source_ref}"

    return answer



# ─────────────────────────────────────────────────────────────────────────────
# 4. SIMPLE QUERY CACHE
# ─────────────────────────────────────────────────────────────────────────────

_CACHE: Dict[str, Any] = {}
_CACHE_TTL = 300  # 5 minutes


def cache_get(key: str) -> Any | None:
    entry = _CACHE.get(key)
    if entry and (time.time() - entry["ts"]) < _CACHE_TTL:
        return entry["val"]
    return None


def cache_set(key: str, val: Any):
    _CACHE[key] = {"val": val, "ts": time.time()}


# ─────────────────────────────────────────────────────────────────────────────
# 5. HTTP SERVER
# ─────────────────────────────────────────────────────────────────────────────

class PolicyHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # noqa: A002
        logger.info("%s %s", self.address_string(), fmt % args)

    # ── CORS ─────────────────────────────────────────────────────────────────
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    # ── GET /health ───────────────────────────────────────────────────────────
    def do_GET(self):
        if self.path.rstrip("/") in ("", "/health"):
            chunks = get_chunks()
            body = json.dumps({
                "status": "ok",
                "service": "PolicyPilot RAG API",
                "policy_chunks": len(chunks),
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self._cors()
            self.end_headers()
            self.wfile.write(body)
        elif self.path.rstrip("/") == "/admin/summary":
            users = load_users()
            self._json({
                "users": [{k: v for k, v in user.items() if k != "password"} for user in users],
                "policy_sources": len(get_chunks()),
                "orders": [],
                "sellers": [],
            })
        else:
            self._error(404, "Not found")

    # ── POST /query  /query/stream ────────────────────────────────────────────
    def do_POST(self):
        if self.path not in ("/query", "/query/stream", "/auth/login", "/auth/signup"):
            self._error(404, "Endpoint not found")
            return

        length = int(self.headers.get("Content-Length", 0))
        if not length:
            self._error(400, "Request body required")
            return

        try:
            body = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            self._error(400, "Invalid JSON")
            return

        if self.path in ("/auth/login", "/auth/signup"):
            users = load_users()
            email = str(body.get("email") or "").strip().lower()
            password = str(body.get("password") or "")
            if self.path == "/auth/signup":
                name = str(body.get("name") or "").strip()
                if not name or not email or not password:
                    self._error(400, "Name, email, and password are required.")
                    return
                if any(user.get("email", "").lower() == email for user in users):
                    self._error(409, "An account with this email already exists.")
                    return
                users.append({"id": max([user.get("id", 0) for user in users] or [0]) + 1, "email": email, "password": password, "role": "user", "name": name})
                USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")
                user = users[-1]
            else:
                user = next((candidate for candidate in users if candidate.get("email", "").lower() == email and candidate.get("password") == password), None)
                if user is None:
                    self._error(401, "Invalid email or password.")
                    return
            self._json({"access_token": make_token(user), "role": user.get("role", "user"), "user": {k: v for k, v in user.items() if k != "password"}})
            return

        question = (body.get("question") or "").strip() if isinstance(body, dict) else ""
        if not question:
            self._error(400, "Question is required and cannot be empty.")
            return

        # Cache check (non-stream only)
        if self.path == "/query":
            cached = cache_get(question)
            if cached:
                cached["usage"]["cache_hit"] = True
                self._json(cached)
                return

        # Retrieve + generate
        t0 = time.perf_counter()
        chunks = retrieve(question, top_k=5)
        answer, sources = build_grounded_answer(question, chunks)
        latency = round((time.perf_counter() - t0) * 1000, 2)

        if self.path == "/query/stream":
            self._stream(answer, sources, latency)
        else:
            result = {
                "answer": answer,
                "sources": sources,
                "usage": {
                    "cache_hit": False,
                    "retrieved_chunks": len(chunks),
                    "latency_ms": latency,
                },
            }
            cache_set(question, result)
            self._json(result)

    # ── Streaming (SSE) ───────────────────────────────────────────────────────
    def _stream(self, answer: str, sources: list, latency: float):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self._cors()
        self.end_headers()

        def _send(obj: dict):
            line = f"data: {json.dumps(obj)}\n\n".encode("utf-8")
            try:
                self.wfile.write(line)
                self.wfile.flush()
            except Exception:
                pass

        # Stream answer word-by-word
        words = answer.split(" ")
        for i, word in enumerate(words):
            token = word + (" " if i < len(words) - 1 else "")
            _send({"type": "token", "text": token})
            time.sleep(0.03)  # simulate streaming

        # Send citations
        _send({"type": "citations", "sources": sources})
        _send({"type": "done"})

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _json(self, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _error(self, code: int, msg: str):
        body = json.dumps({"error": msg}).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)


# ─────────────────────────────────────────────────────────────────────────────
# 6. ENTRYPOINT
# ─────────────────────────────────────────────────────────────────────────────

def run_server(host: str = "0.0.0.0", port: int = 8000):
    # Pre-load chunks at startup
    chunks = get_chunks()
    logger.info("PolicyPilot API ready — %d policy chunks loaded", len(chunks))

    server = HTTPServer((host, port), PolicyHandler)
    logger.info("Listening at http://localhost:%d", port)
    logger.info("Endpoints:  GET /health  |  POST /query  |  POST /query/stream")

    openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY")
    if openai_key:
        logger.info("LLM mode: ACTIVE (key found)")
    else:
        logger.info("LLM mode: OFFLINE (no OPENAI_API_KEY/GROQ_API_KEY) — using rule-based answers")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down.")
        server.server_close()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    run_server(port=port)
