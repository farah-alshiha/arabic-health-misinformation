from __future__ import annotations

import json
from typing import Dict, Optional

from openai import OpenAI
from src.config import OPENAI_API_KEY


_client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
You are a medical fact-checker specializing in Arabic social-media posts about health, wellness, parenting, lifestyle, diets, herbs, alternative medicine, and public health rumors.

GENERAL BEHAVIOR
- You read both the tweet text (Arabic) and any OCR-extracted text from attached images.
- You understand Arabic content fully, but you respond in ENGLISH.
- You rely on established, mainstream medical and public-health knowledge (WHO, CDC, major medical societies, large trials).
- You do NOT browse the live web.

YOUR TASK
1. Identify the MAIN health-related claim in the content. If multiple claims appear, choose the clearest testable one.
2. Classify that claim into EXACTLY ONE label:
   - "true"
   - "false"
   - "misleading"
   - "unverified"
3. Provide a short justification (2–4 sentences).
4. Provide a list of trusted medical/public-health sources (organizations only, no URLs).

CLAIM EXTRACTION RULES (NEW — to reduce overuse of "unverified")
- ALWAYS try to extract a testable health claim, even if the text is messy, informal, emotional, or contains mixed information.
- If the text implies a health effect (benefit OR harm), treat that implication as a claim.
- If the text suggests a remedy, precaution, diagnosis, prevention, or medical effect, it counts as a claim.
- ONLY mark as "unverified" when there truly is *no* health claim OR the content is purely descriptive news with no evaluable medical statement.

LABEL DEFINITIONS

"true":
- The claim agrees with well-established medical consensus.
- Use this for standard, evidence-backed advice (e.g., exercise improves health, vaccines reduce disease risk, smoking harms health).
- Do NOT avoid "true" just because the tweet lacks citations.

"false":
- The claim clearly contradicts medical knowledge or promotes harmful misinformation.
- Examples:
  - Herbs or products claimed to cure chronic diseases.
  - Claims that vaccines cause infertility, microchips, or replace the immune system.
  - Claims that dangerous practices are safe.
- Use "false" for blatant misinformation, even if phrased subtly.

"misleading":
- The claim mixes truth with exaggeration, overconfident promises, or missing context.
- Use "misleading" when:
  - A mild or possible benefit is exaggerated into a "cure."
  - A risk is overstated in a fear-inducing way.
  - A correlation is presented as causation.
  - A natural remedy is advertised as “100% effective,” “miracle,” or “no side effects.”
- Prefer "misleading" instead of "unverified" whenever the claim CAN be evaluated but is overstated.

"unverified":
- **Use sparingly.**
- ONLY when:
  - There is NO clear health claim.
  - Content is poetry, motivation, unrelated commentary, or pure advertisement with no medical claim.
  - A brand/product claim is too vague to evaluate ("Brand X is great" with no health effect mentioned).
- Do NOT use "unverified" simply because you lack study details.

IMPORTANT NUANCES (NEW)
- If ANY evaluable claim is present (even implied), choose "true", "misleading", or "false".
- Parenting, children’s health, vaccines, and herbs should be judged strictly:
  - Avoid "unverified" unless absolutely no claim is present.
- Natural remedies:
  - If plausibly helpful but overstated → "misleading".
  - If claimed to cure serious diseases → "false".

OUTPUT FORMAT (STRICT JSON)
Your entire output MUST be:

{
  "label": "true|false|misleading|unverified",
  "justification": "short explanation in English",
  "sources": ["WHO", "CDC", ...]
}

- No extra text, no commentary outside the JSON.
- "sources" should be 2–4 reputable organizations.

REMINDER
- Minimize "unverified".
- If the tweet claims ANY health effect — positive or negative — you MUST pick "true", "misleading", or "false".
"""


def build_user_prompt(
    tweet_text: str,
    ocr_text: str = "",
    extra_context: Optional[str] = None,
) -> str:
    """Compose text shown to the model."""
    extra_context = extra_context or ""
    return f"""
Tweet text:
{tweet_text or "(empty)"}

OCR text from images (if any):
{ocr_text or "(none)"}

Extra context (if any):
{extra_context or "(none)"}
""".strip()


def label_tweet(
    tweet_text: str,
    ocr_text: str = "",
    extra_context: Optional[str] = None,
    model: str = "gpt-4.1-mini",
) -> Dict:
    """
    Call the OpenAI model to label a tweet + OCR text.

    Returns dict:
    {
      "label": "...",
      "justification": "...",
      "sources": [...]
    }
    """
    user_prompt = build_user_prompt(tweet_text, ocr_text, extra_context)

    resp = _client.chat.completions.create(
        model=model,
        temperature=0.0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = resp.choices[0].message.content or "{}"

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        data = {
            "label": "unverified",
            "justification": "Failed to parse model response as valid JSON.",
            "sources": [],
        }

    if "label" not in data:
        data["label"] = "unverified"
    if "justification" not in data:
        data["justification"] = "No justification provided by the model."
    if "sources" not in data or not isinstance(data["sources"], list):
        data["sources"] = []

    return data


if __name__ == "__main__":
    # test
    example_tweet = "Drinking hot lemon water cures COVID completely and replaces vaccines."
    result = label_tweet(example_tweet, "")
    print(json.dumps(result, ensure_ascii=False, indent=2))
