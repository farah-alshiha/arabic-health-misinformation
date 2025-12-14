from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any

from src.ocr_step import ocr_image_url
from src.ocr_cleaning import clean_ocr_text


INPUT_PATH = Path("health_tweets_with_images.json")
OUTPUT_PATH = Path("health_tweets_with_ocr.json")


def add_ocr_to_dataset(
    input_path: Path = INPUT_PATH,
    output_path: Path = OUTPUT_PATH,
) -> int:
    """
    Read tweets with images from input_path, run OCR on each image URL,
    and write a new JSON file with OCR text attached.

    Returns number of tweets processed.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    data: List[Dict[str, Any]] = json.loads(input_path.read_text(encoding="utf-8"))
    print(f"Loaded {len(data)} tweets from {input_path}")

    for idx, row in enumerate(data, start=1):
        image_urls: List[str] = row.get("image_urls") or []
        ocr_texts: List[str] = []

        print(f"[{idx}/{len(data)}] OCR for tweet_id={row.get('tweet_id')} with {len(image_urls)} image(s)")

        for url in image_urls:
            try:
                raw_txt = ocr_image_url(url)
                cleaned = clean_ocr_text(raw_txt, keep_english=False, keep_digits=True)
                if cleaned:
                    ocr_texts.append(cleaned)
            except Exception as e:
                print(f"  - Error OCRing {url}: {e}")


        row["ocr_texts"] = ocr_texts
        row["ocr_text_combined"] = "\n\n".join(ocr_texts)

    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(data)} tweets with OCR to {output_path}")

    return len(data)


def main():
    add_ocr_to_dataset()


if __name__ == "__main__":
    main()