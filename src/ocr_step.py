from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv
from PIL import Image
import pytesseract


ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"
load_dotenv(ENV_PATH)

TESSERACT_CMD = os.getenv("TESSERACT_CMD")
if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

OCR_LANG = os.getenv("OCR_LANG", "eng")

SESSION = requests.Session()


def _ocr_image(img: Image.Image, lang: Optional[str] = None) -> str:
    """Run Tesseract OCR on a PIL image."""
    lang = lang or OCR_LANG
    text = pytesseract.image_to_string(img, lang=lang)
    return text.strip()


def ocr_image_url(image_url: str, lang: Optional[str] = None) -> str:
    """OCR for a remote image URL (Twitter, etc.)."""
    resp = SESSION.get(image_url, timeout=30)
    resp.raise_for_status()
    img = Image.open(io.BytesIO(resp.content)).convert("RGB")
    return _ocr_image(img, lang=lang)


def ocr_local_image(image_path: str | Path, lang: Optional[str] = None) -> str:
    """OCR for a local image file."""
    p = Path(image_path)
    if not p.exists():
        raise FileNotFoundError(f"Local image file not found: {p}")
    img = Image.open(p).convert("RGB")
    return _ocr_image(img, lang=lang)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 -m src.ocr_step <image_url_or_local_path>")
        sys.exit(1)

    arg = sys.argv[1]

    if arg.startswith("http://") or arg.startswith("https://"):
        print("Mode: URL")
        print("Image URL:", arg)
        text = ocr_image_url(arg)
    else:
        print("Mode: local file")
        print("Image path:", arg)
        text = ocr_local_image(arg)

    print("\n--- OCR result ---")
    print(text if text else "(no readable text)")
