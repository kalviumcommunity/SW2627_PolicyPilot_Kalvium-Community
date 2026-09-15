# Real‑world user store backed by a JSON file (data/users.json)

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Path to the JSON file containing user records (relative to project root)
DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "users.json"

def _load_users() -> List[Dict]:
    """Load the list of users from the JSON file.

    Returns an empty list on failure and logs a warning.
    """
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.warning("Failed to load users from %s: %s", DATA_FILE, exc)
        return []

# Cache the users in memory after first load for performance
_USERS_CACHE: Optional[List[Dict]] = None

def _get_cached_users() -> List[Dict]:
    global _USERS_CACHE
    if _USERS_CACHE is None:
        _USERS_CACHE = _load_users()
    return _USERS_CACHE

def get_user_by_email(email: str) -> Optional[Dict]:
    """Return the user dict matching the given email, or ``None`` if not found.
    """
    for user in _get_cached_users():
        if user.get("email") == email:
            return user
    return None

def list_users() -> List[Dict]:
    """Return a list of all users **without** password fields.
    """
    users = _get_cached_users()
    return [{k: v for k, v in u.items() if k != "password"} for u in users]
