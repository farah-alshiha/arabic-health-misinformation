from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, parse_qs

import requests


DEFAULT_INPUT_PATH = Path("health_tweets_labeled.json")
DEFAULT_OUTPUT_PATH = Path("health_tweets_with_local_images.json")
DEFAULT_IMAGE_DIR = Path("tweet_images")
DEFAULT_INDEX_CSV = Path("images_index.csv")


def _guess_extension_from_url(url: str) -> str:
    url_lower = url.lower()

    parsed = urlparse(url_lower)
    qs = parse_qs(parsed.query)
    if "format" in qs and qs["format"]:
        fmt = qs["format"][0]
        if re.match(r"^[a-z0-9]{3,4}$", fmt):
            return f".{fmt}"

    if ".png" in parsed.path:
        return ".png"
    if ".jpeg" in parsed.path:
        return ".jpeg"
    if ".jpg" in parsed.path:
        return ".jpg"
    if ".webp" in parsed.path:
        return ".webp"

    return ".jpg"


def _safe_tweet_id(raw_id: Any) -> str:
    """Convert tweet_id to a filesystem-safe string."""
    if raw_id is None:
        return "unknown"
    return re.sub(r"[^0-9A-Za-z_-]", "_", str(raw_id))


def download_images_for_dataset(
    input_path: Path = DEFAULT_INPUT_PATH,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    image_dir: Path = DEFAULT_IMAGE_DIR,
    index_csv_path: Path = DEFAULT_INDEX_CSV,
    max_tweets: Optional[int] = None,
    timeout: int = 20,
) -> None:
    """
    Read a tweet dataset JSON (list of dicts) containing 'image_urls',
    download all images to a local directory, attach 'image_paths'
    to each tweet, and write:
      - an updated JSON with local paths
      - a flat CSV index (one row per image) to facilitate training.

    Parameters
    ----------
    input_path : Path
        JSON file with tweets (e.g. health_tweets_labeled.json).
    output_path : Path
        JSON file to write updated tweets with 'image_paths'.
    image_dir : Path
        Directory where images will be saved.
    index_csv_path : Path
        CSV file with (tweet_id, image_idx, image_path, label, text, ocr_text).
    max_tweets : Optional[int]
        If set, only process the first N tweets (useful for testing).
    timeout : int
        HTTP timeout in seconds for image downloads.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    print(f"Loading tweets from {input_path}...")
    data: List[Dict[str, Any]] = json.loads(input_path.read_text(encoding="utf-8"))
    total = len(data)
    print(f"Loaded {total} tweets.")

    if max_tweets is not None:
        data = data[:max_tweets]
        print(f"Limiting to first {max_tweets} tweets for image download.")

    image_dir.mkdir(parents=True, exist_ok=True)

    index_rows: List[str] = []
    header = "tweet_id,image_idx,image_path,label,text,ocr_text\n"
    index_rows.append(header)

    total_images = 0
    downloaded_images = 0

    for i, row in enumerate(data, start=1):
        tweet_id = row.get("tweet_id")
        tweet_id_safe = _safe_tweet_id(tweet_id)
        image_urls = row.get("image_urls") or []
        if not isinstance(image_urls, list):
            continue

        label = (row.get("label") or "").replace("\n", " ").replace('"', "'")
        text = (row.get("text") or "").replace("\n", " ").replace('"', "'")
        ocr_text = (row.get("ocr_text_combined") or "").replace("\n", " ").replace('"', "'")

        local_paths: List[str] = []
        if image_urls:
            print(f"[{i}/{len(data)}] Tweet {tweet_id_safe}: {len(image_urls)} image(s).")

        for j, url in enumerate(image_urls):
            total_images += 1
            if not isinstance(url, str) or not url.strip():
                continue

            ext = _guess_extension_from_url(url)
            fname = f"{tweet_id_safe}_{j}{ext}"
            fpath = image_dir / fname
            
            if fpath.exists():
                local_paths.append(str(fpath))
            
                index_rows.append(
                    f'{tweet_id_safe},{j},"{fpath}","{label}","{text}","{ocr_text}"\n'
                )
                continue

            try:
                resp = requests.get(url, timeout=timeout)
                resp.raise_for_status()
                with fpath.open("wb") as out:
                    out.write(resp.content)
                downloaded_images += 1
                local_paths.append(str(fpath))
                index_rows.append(
                    f'{tweet_id_safe},{j},"{fpath}","{label}","{text}","{ocr_text}"\n'
                )
            except Exception as e:
                print(f"  - Failed to download image {j} for tweet {tweet_id_safe}: {e}")

        row["image_paths"] = local_paths

    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved updated dataset with local image paths to {output_path}")

    index_csv_path.write_text("".join(index_rows), encoding="utf-8")
    print(f"Saved image index CSV with {len(index_rows) - 1} rows to {index_csv_path}")

    print(f"\nTotal images referenced: {total_images}")
    print(f"Images successfully downloaded (new): {downloaded_images}")
    print(f"Images (existing or new) with paths stored in dataset: "
          f"{sum(len(r.get('image_paths', [])) for r in data)}")


def main() -> None:
    download_images_for_dataset(
        input_path=DEFAULT_INPUT_PATH,
        output_path=DEFAULT_OUTPUT_PATH,
        image_dir=DEFAULT_IMAGE_DIR,
        index_csv_path=DEFAULT_INDEX_CSV,
        max_tweets=None,
    )

if __name__ == "__main__":
    main()