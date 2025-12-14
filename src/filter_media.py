from __future__ import annotations
from typing import Dict, List, Any


def _collect_media_candidates(tweet: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Collect all media-like objects from common tweet shapes.

    Handles both snake_case and camelCase keys, like:
    - extended_entities
    - extendedEntities
    - entities
    - extended_tweet / extendedTweet
    """
    media_items: List[Dict[str, Any]] = []

    entities = (
        tweet.get("extended_entities")
        or tweet.get("extendedEntities")
        or tweet.get("entities")
        or {}
    )
    if isinstance(entities, dict):
        media_items.extend(entities.get("media", []))

    if isinstance(tweet.get("media"), list):
        media_items.extend(tweet["media"])

    ext = tweet.get("extended_tweet") or tweet.get("extendedTweet") or {}
    if isinstance(ext, dict):
        ext_entities = (
            ext.get("extended_entities")
            or ext.get("extendedEntities")
            or ext.get("entities")
            or {}
        )
        if isinstance(ext_entities, dict):
            media_items.extend(ext_entities.get("media", []))

    return media_items


def extract_image_urls(tweet: Dict[str, Any]) -> List[str]:
    """
    Return a list of image URLs for a tweet.
    Filters out videos/GIFs and deduplicates URLs.
    """
    media_items = _collect_media_candidates(tweet)
    urls: List[str] = []

    for m in media_items:
        m_type = m.get("type")

        if m_type not in ("photo", "image", None):
            continue

        url = (
            m.get("media_url_https")
            or m.get("media_url")
            or m.get("url")
            or m.get("src")
        )
        if url:
            urls.append(url)

    seen = set()
    unique_urls: List[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique_urls.append(u)

    return unique_urls
