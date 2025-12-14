from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any

from .filter_media import extract_image_urls


def build_image_tweet_dataset(
    input_path: str = "raw_health_tweets.json",
    output_path: str = "health_tweets_with_images.json",
) -> int:
    """
    Read a raw tweets JSON file (list of tweet objects), keep only those
    that have at least one image URL, and save a cleaned dataset to output_path.

    - input_path: JSON produced by the collector (e.g. raw_health_tweets.json)
    - output_path: JSON with only tweets that contain images, with selected fields

    Returns the number of tweets saved.
    """
    in_path = Path(input_path)
    if not in_path.exists():
        raise FileNotFoundError(f"Input file not found: {in_path}")

    print(f"Loading raw tweets from {in_path}...")
    raw_text = in_path.read_text(encoding="utf-8")
    try:
        tweets: List[Dict[str, Any]] = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from {in_path}: {e}") from e

    print(f"Loaded {len(tweets)} raw tweets.")

    rows: List[Dict[str, Any]] = []

    for tw in tweets:
        image_urls = extract_image_urls(tw)


        if not image_urls:
            continue

        user = tw.get("user") or {}
        if not isinstance(user, dict):
            user = {}

        row = {
            "tweet_id": tw.get("id"),
            "author_id": user.get("id"),
            "author_screen_name": user.get("screen_name"),
            "text": tw.get("full_text") or tw.get("text"),
            "created_at": tw.get("created_at"),
            "lang": tw.get("lang"),
            "image_urls": image_urls,
            "raw": tw,
        }
        rows.append(row)

    out_path = Path(output_path)
    out_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(rows)} tweets with images to {out_path}")

    return len(rows)


def main():
    build_image_tweet_dataset(
        input_path="raw_health_tweets.json",
        output_path="health_tweets_with_images.json",
    )


if __name__ == "__main__":
    main()