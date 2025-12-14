from __future__ import annotations

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import re

from .labeler import label_tweet

INPUT_PATH = Path("health_tweets_with_ocr.json")
OUTPUT_PATH = Path("health_tweets_labeled.json")


CLAIM_PATTERN = re.compile(
    r"(يشفي|يعالج|يقضي على|يمنع|يحمي من|يسبب|"
    r"يزيد\s+خطر|بدون\s+آثار\s+جانبية|بدون\s+دواء|بدون\s+أدوية|"
    r"طبيعي\s*100%|مضمون\s*100%|معجزة|خلطة\s+سحرية|"
    r"سر\s+لا\s+يريدونك\s+أن\s+تعرفه|"
    r"الحقيقة\s+التي\s+لا\s+تخبرك\s+بها\s+وزارة\s+الصحة|"
    r"خداع\s+شركات\s+الأدوية)"
)

def looks_like_claim(text: str) -> bool:
    if not text:
        return False
    return bool(CLAIM_PATTERN.search(text))


def already_labeled(row: Dict[str, Any]) -> bool:
    label = (row.get("label") or "").strip()
    return bool(label)


def add_labels_to_dataset(
    input_path: Path = INPUT_PATH,
    output_path: Path = OUTPUT_PATH,
    max_items: Optional[int] = None,
    sleep_seconds: float = 0.0,
    skip_already_labeled: bool = False,
) -> int:
    """
    Read tweets with OCR from input_path, label them with the LLM,
    and write the updated dataset to output_path.

    IMPORTANT: The LLM is called for *every* tweet (up to max_items),
    regardless of whether a clear claim is detected or not.

    - max_items: if set, limit the number of LLM calls in this run.
                 The file is NOT truncated; all rows are written back.
    - sleep_seconds: optional pause between API calls.
    - skip_already_labeled: if True, rows that already have a 'label' are left as-is.

    Returns: number of tweets that were (re)labeled in this run.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    data: List[Dict[str, Any]] = json.loads(input_path.read_text(encoding="utf-8"))
    total = len(data)
    print(f"Loaded {total} tweets from {input_path}")

    labeled_count = 0

    for idx, row in enumerate(data, start=1):
        tweet_id = row.get("tweet_id")
        tweet_text = row.get("text") or ""
        ocr_text = row.get("ocr_text_combined") or ""

        if max_items is not None and labeled_count >= max_items:
            print(
                f"Reached max_items={max_items} LLM calls; "
                f"stopping further labeling but keeping all existing data."
            )
            break

        if skip_already_labeled and already_labeled(row):
            print(f"[{idx}/{total}] Skipping tweet_id={tweet_id}: already labeled.")
            continue

        full_text = (tweet_text or "") + "\n" + (ocr_text or "")
        row["has_claim_pattern"] = looks_like_claim(full_text)
        row["is_strong_claim"] = bool(CLAIM_PATTERN.search(ocr_text or ""))

        print(f"[{idx}/{total}] Labeling tweet_id={tweet_id}")

        try:
            label_info = label_tweet(tweet_text, ocr_text)
        except Exception as e:
            print(f"  - Error labeling tweet_id={tweet_id}: {e}")
            label_info = {
                "label": "unverified",
                "justification": f"Labeling error: {e}",
                "sources": [],
            }

        row["label"] = label_info.get("label", "unverified")
        row["label_justification"] = label_info.get(
            "justification",
            "No justification provided by labeling step.",
        )
        row["label_sources"] = label_info.get("sources", [])

        labeled_count += 1

        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {total} tweets (with {labeled_count} newly labeled) to {output_path}")
    return labeled_count


def main():
    add_labels_to_dataset(
        max_items=None,
        sleep_seconds=0.5,
        skip_already_labeled=False,
    )

if __name__ == "__main__":
    main()