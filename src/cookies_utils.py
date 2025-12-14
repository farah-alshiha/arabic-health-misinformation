from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any

# Project root = parent of src/
ROOT_DIR = Path(__file__).resolve().parent.parent
COOKIES_FILE = ROOT_DIR / "cookies.txt"


def load_raw_cookies(path: Path = COOKIES_FILE) -> List[Dict[str, Any]]:
    """
    Load cookies from cookies.txt.
    Expected format: JSON list of cookie objects (e.g., from a browser export).
    """
    if not path.exists():
        raise FileNotFoundError(f"cookies file not found at: {path}")

    text = path.read_text(encoding="utf-8")
    data = json.loads(text)

    if not isinstance(data, list):
        raise ValueError("cookies.txt must contain a JSON list of cookie objects")

    return data


def cookies_list_to_requests_dict(
    cookies: List[Dict[str, Any]],
    domain_filter_substrings: List[str] | None = None,
) -> Dict[str, str]:
    """
    Convert a list of cookie objects to a dict suitable for requests.cookies.

    - domain_filter_substrings: if provided, only cookies whose 'domain' contains
      ANY of these substrings will be kept (e.g., [\"twitter.com\", \"x.com\"]).
    """
    jar: Dict[str, str] = {}

    for c in cookies:
        name = c.get("name")
        value = c.get("value")
        domain = c.get("domain", "")

        if not name or value is None:
            continue

        if domain_filter_substrings:
            if not any(substr in domain for substr in domain_filter_substrings):
                continue

        jar[name] = value

    return jar


def get_twitter_cookies() -> Dict[str, str]:
    """
    Convenience helper: load cookies.txt and return only cookies for Twitter/X.
    """
    raw = load_raw_cookies()
    return cookies_list_to_requests_dict(raw, ["twitter.com", "x.com"])


if __name__ == "__main__":
    # Quick manual test if you run: python -m src.cookies_utils
    cookies = get_twitter_cookies()
    print("Loaded cookies:", list(cookies.keys()))
