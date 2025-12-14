from __future__ import annotations

import re
import unicodedata


# Arabic diacritics ranges
ARABIC_DIACRITICS_PATTERN = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u06D6-\u06ED]"
)

# Direction marks / zero-width etc.
CONTROL_CHARS_PATTERN = re.compile(
    r"[\u200c-\u200f\u202a-\u202e\u2066-\u2069]"
)


def normalize_arabic_letters(text: str) -> str:
    """Normalize common Arabic forms (alef variants, ya, etc.)."""
    # Alef variants → ا
    text = re.sub(r"[أإآٱ]", "ا", text)
    # Ya/Alif Maqsura → ي
    text = re.sub(r"[ى]", "ي", text)
    # Teh marbuta → ه (or keep كـة if you prefer)
    # If you want to KEEP ة, comment this line:
    text = text.replace("ة", "ه")
    return text


def clean_ocr_text(
    text: str,
    keep_english: bool = False,
    keep_digits: bool = True,
) -> str:
    """
    Clean noisy OCR text (Arabic-focused).

    Steps:
      - Unicode normalize
      - Remove control chars and diacritics
      - Normalize Arabic letters
      - Optionally drop non-Arabic/English characters
      - Collapse whitespace
    """
    if not text:
        return ""

    # 1) Normalize Unicode
    text = unicodedata.normalize("NFKC", text)

    # 2) Remove control chars (RTL marks, zero-width, etc.)
    text = CONTROL_CHARS_PATTERN.sub("", text)

    # 3) Remove Arabic diacritics & tatweel (ـ)
    text = ARABIC_DIACRITICS_PATTERN.sub("", text)
    text = text.replace("ـ", "")

    # 4) Normalize Arabic letter variants
    text = normalize_arabic_letters(text)

    # 5) Optionally restrict allowed characters
    if keep_english:
        # Arabic letters, English letters, digits, basic punctuation, space
        allowed_pattern = r"[^0-9A-Za-z\u0600-\u06FF\s\.\,\:\;\-\(\)\[\]\!\؟\!\"\'،]"
    else:
        # Arabic letters, digits, basic punctuation, space
        allowed_pattern = r"[^0-9\u0600-\u06FF\s\.\,\:\;\-\(\)\[\]\!\؟\!\"\'،]"

    text = re.sub(allowed_pattern, " ", text)

    # 6) If you want to drop digits entirely
    if not keep_digits:
        text = re.sub(r"[0-9]", " ", text)

    # 7) Collapse multiple spaces / lines
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    return text
