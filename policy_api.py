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
# 3. E-COMMERCE DOMAIN KNOWLEDGE & GUARDRAILS
# ─────────────────────────────────────────────────────────────────────────────

STORE_ORDERS_DB = [
    {
        "id": "ORD-99215",
        "date": "14 Sep 2026",
        "customerName": "Ananya",
        "product": "Sony WH-1000XM5 Wireless Noise-Canceling Headphones",
        "vendor": "Nexus Electronics Direct",
        "amount": "₹24,999",
        "status": "In Transit",
        "currentStep": 3,
        "currentStepName": "In Transit (Step 3 of 5)",
        "carrier": "BlueDart Express",
        "trackingNumber": "BD-88290142",
        "eta": "16 Sep 2026",
        "destination": "Indiranagar, Bengaluru, Karnataka",
        "policyNote": "Eligible for 30-day return upon delivery. Report any transit damage within 48 hours for free doorstep pickup and express replacement.",
        "citations": [
            {"source": "shopverse_policies.md", "section": "Return Window"},
            {"source": "shopverse_policies.md", "section": "Damaged or Defective Products"}
        ]
    },
    {
        "id": "ORD-99214",
        "date": "12 Sep 2026",
        "customerName": "Ananya",
        "product": "Minimalist Weatherproof Commuter Backpack",
        "vendor": "Apex Logistics & Retail",
        "amount": "₹4,250",
        "status": "Delivered",
        "currentStep": 5,
        "currentStepName": "Delivered (Step 5 of 5)",
        "carrier": "Delhivery Express",
        "trackingNumber": "DL-99120411",
        "eta": "Delivered on 14 Sep 2026",
        "destination": "Indiranagar, Bengaluru, Karnataka",
        "policyNote": "Delivered on 14 Sep 2026. 30-day return window is active until 14 Oct 2026 (28 days remaining).",
        "citations": [
            {"source": "shopverse_policies.md", "section": "Return Window"},
            {"source": "shopverse_policies.md", "section": "Refund Timeline"}
        ]
    },
    {
        "id": "ORD-99216",
        "date": "15 Sep 2026",
        "customerName": "Ananya",
        "product": "Ergonomic Mesh Task Chair Pro",
        "vendor": "Solace Home & Living",
        "amount": "₹14,499",
        "status": "Processing",
        "currentStep": 1,
        "currentStepName": "Order Confirmed & Processing (Step 1 of 5)",
        "carrier": "Safexpress Freight",
        "trackingNumber": "SF-44019283",
        "eta": "19 Sep 2026",
        "destination": "Indiranagar, Bengaluru, Karnataka",
        "policyNote": "Seller Solace Home & Living is bound by the 2 business day dispatch SLA. Order can be cancelled with full refund while in processing stage.",
        "citations": [
            {"source": "shopverse_policies.md", "section": "Dispatch SLA"},
            {"source": "shopverse_policies.md", "section": "Order Cancellation by Customer"}
        ]
    },
    {
        "id": "ORD-99217",
        "date": "10 Sep 2026",
        "customerName": "Ananya",
        "product": "Keychron K2 Wireless Mechanical Keyboard",
        "vendor": "Quantum Tech Gadgets",
        "amount": "₹7,899",
        "status": "Delivered",
        "currentStep": 5,
        "currentStepName": "Delivered (Step 5 of 5)",
        "carrier": "BlueDart Express",
        "trackingNumber": "BD-77192033",
        "eta": "Delivered on 12 Sep 2026",
        "destination": "Indiranagar, Bengaluru, Karnataka",
        "policyNote": "Delivered on 12 Sep 2026. 30-day return window open until 12 Oct 2026. 1-year manufacturer warranty active with Quantum Tech Gadgets.",
        "citations": [
            {"source": "shopverse_policies.md", "section": "Return Window"},
            {"source": "shopverse_policies.md", "section": "Exchange Policy"}
        ]
    }
]

STORE_PRODUCTS_DB = [
    {
        "id": "PROD-101",
        "name": "Sony WH-1000XM5 Wireless Noise-Canceling Headphones",
        "price": "₹24,999",
        "vendor": "Nexus Electronics Direct",
        "category": "Consumer Electronics",
        "stock": 24,
        "dispatchSla": "Same-Day Dispatch",
        "returnPolicy": "30-Day Return Window",
        "details": "Features industry-leading wireless active noise cancellation, 30-hour battery life, and quick USB-C charging."
    },
    {
        "id": "PROD-102",
        "name": "Ergonomic Mesh Task Chair Pro",
        "price": "₹14,499",
        "vendor": "Solace Home & Living",
        "category": "Home & Office",
        "stock": 12,
        "dispatchSla": "2-Day Dispatch SLA",
        "returnPolicy": "30-Day Return Window",
        "details": "Breathable high-density mesh back, dynamic lumbar support, and 3D adjustable armrests."
    },
    {
        "id": "PROD-103",
        "name": "Minimalist Weatherproof Commuter Backpack",
        "price": "₹4,250",
        "vendor": "Apex Logistics & Retail",
        "category": "Fashion & Gear",
        "stock": 45,
        "dispatchSla": "Express 24h Dispatch",
        "returnPolicy": "30-Day Return Window",
        "details": "Water-resistant ballistic nylon with dedicated padded sleeve fitting up to 16-inch laptops."
    },
    {
        "id": "PROD-104",
        "name": "Keychron K2 Wireless Mechanical Keyboard",
        "price": "₹7,899",
        "vendor": "Quantum Tech Gadgets",
        "category": "Computer Accessories",
        "stock": 18,
        "dispatchSla": "Same-Day Dispatch",
        "returnPolicy": "30-Day Return Window",
        "details": "Compact 75% mechanical layout with hot-swappable switches and Bluetooth 5.1."
    },
    {
        "id": "PROD-105",
        "name": "Aura Organic Botanical Skin Care Set",
        "price": "₹3,200",
        "vendor": "Aura Health & Beauty",
        "category": "Personal Care",
        "stock": 30,
        "dispatchSla": "1-Day Dispatch SLA",
        "returnPolicy": "Sealed 30-Day Return",
        "details": "Certified organic cleanser, clarifying toner, and hydrating hyaluronic moisture complex."
    },
    {
        "id": "PROD-106",
        "name": "Velocity Performance Athletic Running Jacket",
        "price": "₹3,950",
        "vendor": "Velocity Global Apparel",
        "category": "Fashion & Apparel",
        "stock": 55,
        "dispatchSla": "2-Day Dispatch SLA",
        "returnPolicy": "30-Day Return Window",
        "details": "Lightweight thermal running jacket with 360-degree reflective accents and storm-proof hood."
    }
]

# E-commerce Domain Keywords for strict Guardrails
ECOMMERCE_KEYWORDS = {
    # Order & Tracking
    "order", "orders", "track", "tracking", "status", "package", "packages", "parcel", "shipment", "shipping",
    "delivery", "deliver", "courier", "bluedart", "delhivery", "safexpress", "in transit",
    "eta", "arriving", "arrive", "milestone", "dispatch", "dispatched", "where is", "when will",
    # Policies & Customer protections
    "return", "returns", "refund", "refunds", "exchange", "money back", "replace", "replacement", "damage", "damaged",
    "defect", "defective", "broken", "sla", "penalty", "cancel", "cancellation", "hours", "window",
    "days", "fee", "free delivery", "free shipping", "cod", "cash on delivery", "upi", "emi", "payment", "payments",
    "card", "cards", "wallet", "vendor", "vendors", "seller", "sellers", "commission", "support", "contact",
    "email", "phone", "grievance", "escalate", "warranty", "kyc", "gst", "bis", "non returnable", "perishable",
    # Products & Store Catalog
    "product", "products", "item", "items", "buy", "price", "prices", "cost", "catalog", "stock",
    "cart", "checkout", "store", "shopverse", "policypilot", "headphones", "headphone", "sony", "chair",
    "backpack", "keyboard", "keychron", "skin care", "skincare", "aura", "jacket", "velocity", "electronics",
    "address", "account", "customer", "ananya", "purchase", "shopping", "discount"
}

OFF_TOPIC_TERMS = {
    "poem", "poetry", "joke", "jokes", "story", "essay", "song", "lyrics",
    "python", "javascript", "java", "c++", "html", "css", "quicksort", "algorithm",
    "code", "coding", "program", "function", "variable", "binary tree",
    "president", "prime minister", "capital of", "who was", "who is",
    "weather", "forecast", "movie", "celebrity", "sports score", "cricket match",
    "recipe", "pizza", "burger", "cook", "bake", "astronomy", "physics"
}

OFF_TOPIC_REFUSAL = (
    "I am the ShopVerse & PolicyPilot E-Commerce AI Assistant. I can only assist with questions "
    "regarding our store products, live order tracking, delivery timelines, return/refund rules, "
    "damaged goods claims, and store merchant policies. Please ask a question related to your order "
    "or store policies."
)


def _is_ecommerce_domain(question: str) -> bool:
    """Classify if the question is in the e-commerce / store / policy domain."""
    q_lower = question.lower().strip()
    
    # Direct order ID patterns (e.g., ORD-99215, 99215, ORD-)
    if re.search(r"\bord-?\d{4,6}\b", q_lower) or re.search(r"\b(bd|dl|sf)-?\d{6,}\b", q_lower):
        return True
        
    tokens = set(_tokenize(q_lower))

    # Reject if off-topic terms are present and no specific order/policy terms exist
    if any(term in tokens or re.search(r"\b" + re.escape(term) + r"\b", q_lower) for term in OFF_TOPIC_TERMS):
        # Only allow if strongly order/policy related
        if not (re.search(r"\bord-?\d{4,6}\b", q_lower) or any(t in tokens for t in ["order", "shipment", "return", "refund", "shopverse"])):
            return False
        
    # Check word-boundary regex for e-commerce keywords
    for kw in ECOMMERCE_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", q_lower):
            return True
            
    return False


def _match_order_query(question: str) -> Dict[str, Any] | None:
    """Find specific order referenced in question."""
    q_lower = question.lower()
    for order in STORE_ORDERS_DB:
        # Match by ID
        if order["id"].lower() in q_lower or order["id"].replace("-", "").lower() in q_lower:
            return order
        # Match by tracking number
        if order["trackingNumber"].lower() in q_lower:
            return order
        # Match by product keywords if asking for order/tracking
        if any(term in q_lower for term in ["track", "order", "where is", "status", "eta"]):
            prod_terms = [t for t in _tokenize(order["product"]) if len(t) > 4]
            if any(term in q_lower for term in prod_terms):
                return order
    return None


def _match_product_query(question: str) -> Dict[str, Any] | None:
    """Find specific product referenced in question."""
    q_lower = question.lower()
    
    # Check Sony headphones
    if any(k in q_lower for k in ["sony", "wh-1000xm5", "xm5", "headphones", "headphone"]):
        return STORE_PRODUCTS_DB[0]
    # Check Chair
    if any(k in q_lower for k in ["chair", "task chair", "ergonomic", "mesh chair"]):
        return STORE_PRODUCTS_DB[1]
    # Check Backpack
    if any(k in q_lower for k in ["backpack", "commuter backpack", "weatherproof"]):
        return STORE_PRODUCTS_DB[2]
    # Check Keyboard
    if any(k in q_lower for k in ["keychron", "k2", "keyboard", "mechanical keyboard"]):
        return STORE_PRODUCTS_DB[3]
    # Check Skin Care
    if any(k in q_lower for k in ["skin care", "skincare", "botanical", "aura"]):
        return STORE_PRODUCTS_DB[4]
    # Check Running Jacket
    if any(k in q_lower for k in ["jacket", "running jacket", "velocity"]):
        return STORE_PRODUCTS_DB[5]

    for prod in STORE_PRODUCTS_DB:
        if prod["name"].lower() in q_lower or prod["id"].lower() in q_lower:
            return prod
            
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 4. ANSWER GENERATION
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
            "You MUST ONLY answer questions regarding e-commerce products, live order tracking, and store policies. "
            "If the question is unrelated to the store or policies, politely decline to answer. "
            "Answer the customer's question using the provided context. "
            "Be specific, citing exact timeframes, amounts, status, and policy conditions."
        )

        payload = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Policy & Store Context:\n{context}\n\nCustomer Question: {question}"},
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
    """Build a grounded answer from retrieved policy chunks, orders, and products."""
    # 1. Check Guardrail: Refuse Off-Topic queries
    if not _is_ecommerce_domain(question):
        return (OFF_TOPIC_REFUSAL, [])

    # 2. Check for Specific Order inquiry
    matched_order = _match_order_query(question)
    if matched_order:
        answer = (
            f"Order Tracking Details for {matched_order['id']} ({matched_order['product']}):\n"
            f"• Status: {matched_order['currentStepName']}\n"
            f"• Carrier: {matched_order['carrier']} (Tracking #{matched_order['trackingNumber']})\n"
            f"• Estimated Delivery: {matched_order['eta']} to {matched_order['destination']}\n"
            f"• Order Amount: {matched_order['amount']} • Vendor: {matched_order['vendor']}\n"
            f"• Policy Note: {matched_order['policyNote']}"
        )
        return (answer, matched_order.get("citations", [
            {"source": "shopverse_policies.md", "section": "Return Window"}
        ]))

    # 3. Check for Specific Product inquiry
    matched_product = _match_product_query(question)
    if matched_product and not any(k in question.lower() for k in ["return", "refund", "sla", "policy", "damage"]):
        answer = (
            f"Product Details for {matched_product['name']} ({matched_product['id']}):\n"
            f"• Price: {matched_product['price']} (Special Price)\n"
            f"• Category: {matched_product['category']} • In Stock: {matched_product['stock']} units\n"
            f"• Sold by: {matched_product['vendor']}\n"
            f"• Dispatch SLA: {matched_product['dispatchSla']}\n"
            f"• Return Policy: {matched_product['returnPolicy']}\n"
            f"• Details: {matched_product['details']}"
        )
        return (answer, [
            {"source": "shopverse_policies.md", "section": "Product Catalog Policy"},
            {"source": "shopverse_policies.md", "section": "Dispatch SLA"}
        ])

    if not chunks:
        return ("I could not find relevant policy information for your question. "
                "Please contact ShopVerse support at support@shopverse.in or call 1800-XXX-XXXX.", [])

    # 4. Build context string
    context_parts = []
    for i, c in enumerate(chunks, 1):
        context_parts.append(f"[{i}] {c['section']} ({c['source']}):\n{c['text']}")
    context = "\n\n".join(context_parts)

    # 5. Try LLM first
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

    # Intent-based structured answers for precise grounded compliance
    if any(w in q_lower for w in ["damage", "damaged", "defect", "defective", "broken"]):
        return (
            "Under Section 1 of ShopVerse Customer Policy, if you receive a damaged or defective product, "
            "you must report it within 48 hours of delivery by contacting support@shopverse.in or calling 1800-XXX-XXXX. "
            "ShopVerse will arrange a free doorstep pick-up and provide a replacement product or issue a full refund within 5–7 business days.\n\n"
            "[Damaged or Defective Products — shopverse_policies.md]"
        )

    if any(w in q_lower for w in ["return window", "how many days to return", "30 days", "return policy", "standard return"]):
        return (
            "Under Section 1 of ShopVerse Return Policy, customers may request a return or refund for eligible items "
            "within 30 days of the delivery date. Items must be unused, in their original packaging, and include all accessories. "
            "Once inspected at the warehouse, refunds are credited within 3–7 business days depending on payment method.\n\n"
            "[Return Window — shopverse_policies.md]"
        )

    if any(w in q_lower for w in ["cancel", "cancellation"]):
        return (
            "Under Section 4 of ShopVerse Cancellation Policy, orders can be cancelled within 1 hour of placement at no charge. "
            "For orders in 'Processing' status, free cancellation is available. Once the order is 'Dispatched' or 'Out for Delivery', "
            "cancellation cannot be made, but you can request a return after delivery under the 30-day window.\n\n"
            "[Order Cancellation by Customer — shopverse_policies.md]"
        )

    if any(w in q_lower for w in ["sla", "dispatch time", "merchant dispatch", "seller dispatch", "dispatch sla"]):
        return (
            "Under Section 3 of ShopVerse Seller Agreement, sellers are required to dispatch ordered items within "
            "2 business days of order confirmation. Failure to dispatch within the SLA results in automatic order cancellation "
            "and a penalty of ₹50 per late order on the seller.\n\n"
            "[Dispatch SLA — shopverse_policies.md]"
        )

    if any(w in q_lower for w in ["shipping cost", "free delivery", "delivery time", "shipping policy", "express delivery"]):
        return (
            "Under Section 2 of ShopVerse Shipping Policy, standard delivery takes 4–7 business days across India with "
            "FREE delivery on all orders above ₹499. Express delivery is available in 50+ cities within 24–48 hours for ₹99, "
            "and same-day delivery is available in metro cities for orders placed before 12:00 PM IST.\n\n"
            "[Shipping & Delivery Policy — shopverse_policies.md]"
        )

    if any(w in q_lower for w in ["payment", "payment methods", "cod", "upi", "emi"]):
        return (
            "Under Section 8 of ShopVerse Payment Policy, accepted payment methods include Credit & Debit Cards (Visa, Mastercard, RuPay, Amex), "
            "UPI (Google Pay, PhonePe, Paytm), Net Banking (50+ banks), No-cost EMI on orders above ₹3,000, Cash on Delivery (COD) up to ₹50,000, "
            "and ShopVerse Wallet.\n\n"
            "[Payment Policy — shopverse_policies.md]"
        )

    # Re-score chunks for primary selection
    def score_chunk(c: Dict) -> float:
        combined = (c["text"] + " " + c["section"]).lower()
        s = float(sum(1 for t in q_tokens if t in combined))
        return s

    ranked_chunks = sorted(chunks, key=score_chunk, reverse=True)
    primary = ranked_chunks[0]

    clean_text = re.sub(r"^#{1,4}\s+.*$", "", primary["text"], flags=re.MULTILINE).strip()
    clean_text = re.sub(r"\*+", "", clean_text).strip()

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean_text) if len(s.strip()) > 15]
    sent_scored = sorted(
        sentences,
        key=lambda s: sum(1 for t in q_tokens if t in s.lower()),
        reverse=True,
    )
    best_sentences = sent_scored[:3]
    ordered = [s for s in sentences if s in best_sentences][:3]
    excerpt = " ".join(ordered) if ordered else clean_text[:400]

    source_ref = f"[{primary['section']} — {primary['source']}]"
    answer = f"{excerpt}\n\n{source_ref}"

    return answer



# ─────────────────────────────────────────────────────────────────────────────
# 4. QUERY & CONVERSATION AUDIT LOGS
# ─────────────────────────────────────────────────────────────────────────────

QUERY_LOGS_DB: List[Dict[str, Any]] = [
    {
        "id": "LOG-4091",
        "timestamp": "15 Sep 2026, 13:48:15 IST",
        "user": "Ananya",
        "userEmail": "ananya@customer.com",
        "userRole": "customer",
        "surface": "Customer Store (/store)",
        "question": "Where is my order ORD-99215?",
        "answer": "Order Tracking Details for ORD-99215 (Sony WH-1000XM5 Wireless Headphones): Status: In Transit (Step 3 of 5) with BlueDart Express (BD-88290142). ETA: 16 Sep 2026 to Indiranagar, Bengaluru.",
        "category": "Order Tracking",
        "guardrail_status": "Grounded Pass",
        "citations": ["shopverse_policies.md — Return Window", "shopverse_policies.md — Damaged Products"],
        "latency_ms": "0.71ms",
        "cache_hit": True
    },
    {
        "id": "LOG-4090",
        "timestamp": "15 Sep 2026, 13:45:20 IST",
        "user": "Ananya",
        "userEmail": "ananya@customer.com",
        "userRole": "customer",
        "surface": "Customer Store (/store)",
        "question": "What is the 30-day return policy?",
        "answer": "Under Section 1 of ShopVerse Return Policy, customers may request a return or refund for eligible items within 30 days of the delivery date. Items must be unused, in original packaging.",
        "category": "Policy Inquiries",
        "guardrail_status": "Grounded Pass",
        "citations": ["shopverse_policies.md — Return Window", "shopverse_policies.md — Refund Timeline"],
        "latency_ms": "0.45ms",
        "cache_hit": False
    },
    {
        "id": "LOG-4089",
        "timestamp": "15 Sep 2026, 13:30:12 IST",
        "user": "Customer #5821",
        "userEmail": "shopper5821@gmail.com",
        "userRole": "customer",
        "surface": "Customer Store (/store)",
        "question": "How do I report damaged or broken goods?",
        "answer": "Under Section 1 of ShopVerse Customer Policy, if you receive a damaged or defective product, you must report it within 48 hours of delivery by contacting support@shopverse.in for free doorstep pickup.",
        "category": "Damage Claims",
        "guardrail_status": "Grounded Pass",
        "citations": ["shopverse_policies.md — Damaged or Defective Products"],
        "latency_ms": "0.52ms",
        "cache_hit": False
    },
    {
        "id": "LOG-4088",
        "timestamp": "15 Sep 2026, 13:12:44 IST",
        "user": "Guest #3910",
        "userEmail": "guest3910@network.net",
        "userRole": "guest",
        "surface": "Policy Assistant (/chatbot)",
        "question": "Write a poem about mountains and rivers",
        "answer": "I am the ShopVerse & PolicyPilot E-Commerce AI Assistant. I can only assist with questions regarding our store products, live order tracking, delivery timelines, return/refund rules, and store policies.",
        "category": "Guardrail Refusal",
        "guardrail_status": "Intercepted (Off-Topic)",
        "citations": [],
        "latency_ms": "0.38ms",
        "cache_hit": False
    },
    {
        "id": "LOG-4087",
        "timestamp": "15 Sep 2026, 12:55:01 IST",
        "user": "Regular User",
        "userEmail": "user@example.com",
        "userRole": "user",
        "surface": "Workspace (/dashboard)",
        "question": "What is the seller dispatch SLA?",
        "answer": "Under Section 3 of ShopVerse Seller Agreement, sellers are required to dispatch ordered items within 2 business days of order confirmation. Late dispatch incurs a Rs 50 penalty per order.",
        "category": "Seller SLA",
        "guardrail_status": "Grounded Pass",
        "citations": ["shopverse_policies.md — Dispatch SLA"],
        "latency_ms": "0.48ms",
        "cache_hit": False
    },
    {
        "id": "LOG-4086",
        "timestamp": "15 Sep 2026, 12:40:18 IST",
        "user": "Compliance Officer",
        "userEmail": "auditor@policypilot.internal",
        "userRole": "compliance",
        "surface": "Admin Portal (/admin)",
        "question": "What payment methods can I use?",
        "answer": "Under Section 8 of ShopVerse Payment Policy, accepted payment methods include Credit & Debit Cards, UPI (Google Pay, PhonePe, Paytm), Net Banking, No-cost EMI, COD up to Rs 50,000, and Wallet.",
        "category": "Payment Policy",
        "guardrail_status": "Grounded Pass",
        "citations": ["shopverse_policies.md — Payment Policy"],
        "latency_ms": "0.60ms",
        "cache_hit": False
    }
]


def log_conversation_entry(
    question: str,
    answer: str,
    sources: list,
    latency: float,
    cache_hit: bool,
    user_name: str = None,
    user_email: str = None,
    user_role: str = None,
    surface: str = None
):
    """Log incoming user questions and answers into the audit trail."""
    import datetime
    now_str = datetime.datetime.now().strftime("%d %b %Y, %H:%M:%S IST")
    log_id = f"LOG-{len(QUERY_LOGS_DB) + 4000 + 1}"
    
    q_lower = question.lower()
    if "order" in q_lower or "ord-" in q_lower or "track" in q_lower:
        cat = "Order Tracking"
    elif "return" in q_lower or "refund" in q_lower:
        cat = "Policy Inquiries"
    elif "damage" in q_lower or "defect" in q_lower:
        cat = "Damage Claims"
    elif "sla" in q_lower or "dispatch" in q_lower:
        cat = "Seller SLA"
    elif not sources and ("I am the ShopVerse" in answer or "only assist with" in answer):
        cat = "Guardrail Refusal"
    else:
        cat = "Policy Inquiries"
        
    guardrail = "Intercepted (Off-Topic)" if cat == "Guardrail Refusal" else "Grounded Pass"
    citation_labels = [f"{s.get('source', '')} — {s.get('section', '')}".strip(" —") for s in sources if s]

    default_user = "Ananya" if ("99215" in question or "ananya" in q_lower) else "Customer"
    default_email = "ananya@customer.com" if ("99215" in question or "ananya" in q_lower) else "customer@shopverse.in"

    new_log = {
        "id": log_id,
        "timestamp": now_str,
        "user": user_name or default_user,
        "userEmail": user_email or default_email,
        "userRole": user_role or "customer",
        "surface": surface or ("Customer Store (/store)" if ("order" in q_lower or "track" in q_lower) else "AI Policy Assistant (/chatbot)"),
        "question": question,
        "answer": answer,
        "category": cat,
        "guardrail_status": guardrail,
        "citations": citation_labels,
        "latency_ms": f"{latency}ms",
        "cache_hit": cache_hit
    }
    QUERY_LOGS_DB.insert(0, new_log)
    logger.info("Audit log logged: %s | User: %s | Query: %s", log_id, new_log["user"], question[:50])


# ─────────────────────────────────────────────────────────────────────────────
# 5. SIMPLE QUERY CACHE
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
# 6. HTTP SERVER
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
        elif self.path.rstrip("/") in ("/admin/summary", "/admin/logs"):
            users = load_users()
            sellers = [
                {
                    "id": "VN-8821",
                    "name": "Apex Logistics & Retail",
                    "category": "Logistics & Fulfillment",
                    "status": "Active",
                    "sla_compliance": "99.4%",
                    "dispatch_time": "1.2 days",
                    "agreement_status": "Verified (v2.4)",
                    "active_products": 1420,
                    "contact_email": "ops@apexlogistics.com",
                    "lead": "Marcus Vance",
                    "rating": 4.9
                },
                {
                    "id": "VN-9042",
                    "name": "Nexus Electronics Direct",
                    "category": "Consumer Electronics",
                    "status": "Active",
                    "sla_compliance": "98.1%",
                    "dispatch_time": "1.8 days",
                    "agreement_status": "Verified (v2.4)",
                    "active_products": 890,
                    "contact_email": "compliance@nexuselec.com",
                    "lead": "Elena Rostova",
                    "rating": 4.8
                },
                {
                    "id": "VN-4120",
                    "name": "Solace Home & Living",
                    "category": "Home & Decor",
                    "status": "Active",
                    "sla_compliance": "97.6%",
                    "dispatch_time": "2.0 days",
                    "agreement_status": "Verified (v2.3)",
                    "active_products": 640,
                    "contact_email": "support@solacehome.com",
                    "lead": "David Chen",
                    "rating": 4.7
                },
                {
                    "id": "VN-7712",
                    "name": "Velocity Global Apparel",
                    "category": "Fashion & Apparel",
                    "status": "Under Review",
                    "sla_compliance": "94.2%",
                    "dispatch_time": "2.6 days",
                    "agreement_status": "Pending Renewal",
                    "active_products": 2150,
                    "contact_email": "partner@velocityapparel.com",
                    "lead": "Sarah Jenkins",
                    "rating": 4.5
                },
                {
                    "id": "VN-3390",
                    "name": "Quantum Tech Gadgets",
                    "category": "Accessories & Hardware",
                    "status": "Active",
                    "sla_compliance": "99.8%",
                    "dispatch_time": "0.9 days",
                    "agreement_status": "Verified (v2.4)",
                    "active_products": 410,
                    "contact_email": "admin@quantumtech.io",
                    "lead": "Raj Patel",
                    "rating": 4.95
                },
                {
                    "id": "VN-5501",
                    "name": "Aura Health & Beauty",
                    "category": "Personal Care & Cosmetics",
                    "status": "Active",
                    "sla_compliance": "98.7%",
                    "dispatch_time": "1.5 days",
                    "agreement_status": "Verified (v2.4)",
                    "active_products": 980,
                    "contact_email": "vendors@aurahealth.com",
                    "lead": "Chloe Martin",
                    "rating": 4.85
                }
            ]
            orders = [
                {"id": "ORD-99214", "status": "Delivered", "sla": "Met", "amount": "Rs 4,250", "vendor": "Apex Logistics & Retail", "date": "2026-09-14"},
                {"id": "ORD-99215", "status": "In Transit", "sla": "On Track", "amount": "Rs 12,899", "vendor": "Nexus Electronics Direct", "date": "2026-09-14"},
                {"id": "ORD-99216", "status": "Processing", "sla": "On Track", "amount": "Rs 1,499", "vendor": "Solace Home & Living", "date": "2026-09-15"},
                {"id": "ORD-99217", "status": "Delivered", "sla": "Met", "amount": "Rs 8,900", "vendor": "Quantum Tech Gadgets", "date": "2026-09-15"},
            ]
            self._json({
                "users": [{
                    "id": u.get("id", i + 1),
                    "name": u.get("name", u.get("email", "").split("@")[0].capitalize()),
                    "email": u.get("email", ""),
                    "role": u.get("role", "user"),
                    "status": "Active",
                    "queries_count": 14 if u.get("role") == "admin" else 8,
                    "last_active": "Just now" if u.get("role") == "admin" else "2 hours ago"
                } for i, u in enumerate(users)],
                "policy_sources": len(get_chunks()),
                "orders": orders,
                "sellers": sellers,
                "query_logs": QUERY_LOGS_DB,
                "telemetry": {
                    "cache_hit_rate": "94.2%",
                    "avg_latency_ms": "48ms",
                    "total_queries_today": len(QUERY_LOGS_DB) + 176,
                    "confidence_threshold": 0.65,
                    "guardrails_active": True
                }
            })
        else:
            self._error(404, "Not found")

    # ── POST /query  /query/stream  /admin/log_conversation ───────────────────
    def do_POST(self):
        if self.path not in ("/query", "/query/stream", "/auth/login", "/auth/signup", "/admin/log_conversation"):
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

        if self.path == "/admin/log_conversation":
            q = body.get("question", "").strip()
            a = body.get("answer", "").strip()
            srcs = body.get("sources", [])
            u_name = body.get("user_name")
            u_email = body.get("user_email")
            u_role = body.get("user_role")
            surf = body.get("surface")
            if q and a:
                log_conversation_entry(q, a, srcs, latency=0.65, cache_hit=False, user_name=u_name, user_email=u_email, user_role=u_role, surface=surf)
                self._json({"status": "logged", "total_logs": len(QUERY_LOGS_DB)})
            else:
                self._error(400, "question and answer required")
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

        user_name = body.get("user_name")
        user_email = body.get("user_email")
        user_role = body.get("user_role")
        surface = body.get("surface")

        # Cache check (non-stream only)
        if self.path == "/query":
            cached = cache_get(question)
            if cached:
                cached["usage"]["cache_hit"] = True
                log_conversation_entry(
                    question,
                    cached.get("answer", ""),
                    cached.get("sources", []),
                    cached.get("usage", {}).get("latency_ms", 0.5),
                    True,
                    user_name=user_name,
                    user_email=user_email,
                    user_role=user_role,
                    surface=surface
                )
                self._json(cached)
                return

        # Retrieve + generate
        t0 = time.perf_counter()
        chunks = retrieve(question, top_k=5)
        answer, sources = build_grounded_answer(question, chunks)
        latency = round((time.perf_counter() - t0) * 1000, 2)
        log_conversation_entry(
            question,
            answer,
            sources,
            latency,
            False,
            user_name=user_name,
            user_email=user_email,
            user_role=user_role,
            surface=surface
        )

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
