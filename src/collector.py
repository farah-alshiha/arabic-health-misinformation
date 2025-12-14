from __future__ import annotations

import os
import time
from typing import List, Dict, Any, Optional
import requests
import json

from .config import TWITTERAPI_KEY, BRIGHT_DATA_AUTH
from .cookies_utils import get_twitter_cookies

BASE_URL = "https://api.twitterapi.io/twitter/tweet/advanced_search"
USE_BRIGHT_DATA_FOR_TWITTERAPI = os.getenv("USE_BRIGHT_DATA_FOR_TWITTERAPI", "false").lower() == "true"

PROXIES = {
    "http":  f"http://{BRIGHT_DATA_AUTH}@brd.superproxy.io:22225",
    "https": f"http://{BRIGHT_DATA_AUTH}@brd.superproxy.io:22225",
}


AR_HEALTH_QUERY = (
    '('
    '(صحة OR "الصحة" OR "صحة الأطفال" OR "وزارة الصحة" OR سكري OR "ضغط الدم" OR سمنة '
    'OR لقاح OR تطعيم OR "طب بديل" OR "وصفات طبيعية" OR خلطات OR "خل التفاح" '
    'OR "الحبة السوداء" OR الكركم OR "المكملات الغذائية" OR "الطب النبوي") '
    '(يشفي OR يعالج OR "يقضي على" OR "بدون دواء" OR "بدون أدوية" OR "بدون دكتور" '
    'OR "بدون طبيب" OR "بدون آثار جانبية" OR "طبيعي 100%" OR "مضمون 100%" '
    'OR "معجزة" OR "خلطة سحرية" OR "سر لا يريدونك أن تعرفه" '
    'OR "الحقيقة التي لا تخبرك بها وزارة الصحة" OR "خداع شركات الأدوية" '
    'OR "لقاح" NEAR "خطر" OR "سرطان" NEAR "لقاح")'
    ') lang:ar has:images -is:retweet -is:reply -is:quote -has:videos'
)

def fetch_all_tweets(
    query: str,
    target_n: int = 1000,
    max_pages: int = 50,
) -> List[Dict[str, Any]]:
    headers = {"x-api-key": TWITTERAPI_KEY}
    all_tweets: List[Dict[str, Any]] = []
    seen_ids = set()
    cursor = None
    page_count = 0
    max_retries = 3

    twitter_cookies = get_twitter_cookies()
    if twitter_cookies:
        print(f"Loaded {len(twitter_cookies)} Twitter cookies (not used by twitterapi.io).")

    while len(all_tweets) < target_n and page_count < max_pages:
        params = {"query": query, "queryType": "Top"}
        if cursor:
            params["cursor"] = cursor

        retry = 0
        while retry < max_retries:
            try:
                resp = requests.get(
                    BASE_URL,
                    headers=headers,
                    params=params,
                    proxies=PROXIES if USE_BRIGHT_DATA_FOR_TWITTERAPI else None,
                    timeout=30,
                )

                if resp.status_code != 200:
                    print(f"HTTP {resp.status_code} from twitterapi.io")
                    try:
                        print("Response body:", resp.text[:1000])
                    except Exception:
                        pass
                    resp.raise_for_status()

                data = resp.json()

                # printing first page just to verify schema
                if page_count == 0:
                    print("--- Raw response (page 1) ---")
                    print(json.dumps(data, ensure_ascii=False, indent=2))


                tweets = (
                    data.get("tweets")
                    or data.get("data")
                    or data.get("results")
                    or data.get("statuses")
                    or []
                )

                has_next = bool(
                    data.get("has_next_page")
                    or data.get("has_next")
                    or data.get("next_cursor")
                    or data.get("next_token")
                    or data.get("next")
                )

                cursor = (
                    data.get("next_cursor")
                    or data.get("next_token")
                    or data.get("next")
                )

                new_count = 0
                for tw in tweets:
                    tid = tw.get("id") or tw.get("tweet_id") or tw.get("rest_id")
                    if tid and tid not in seen_ids:
                        seen_ids.add(tid)
                        all_tweets.append(tw)
                        new_count += 1

                page_count += 1
                print(
                    f"Page {page_count}: raw={len(tweets)}, new={new_count}, "
                    f"total={len(all_tweets)}"
                )

                if not has_next or not tweets:
                    if not has_next:
                        print("No more pages (no next cursor / flag).")
                    if not tweets:
                        print("This page contained 0 tweets.")
                    return all_tweets

                break

            except requests.exceptions.RequestException as e:
                print(f"Request error on page {page_count + 1}, attempt {retry + 1}: {e}")

                if hasattr(e, "response") and e.response is not None:
                    try:
                        print("Error response body:", e.response.text[:1000])
                    except Exception:
                        pass
                retry += 1
                time.sleep(2 ** retry)

        if retry == max_retries:
            print("Max retries reached, stopping collection.")
            break

    return all_tweets


def main():
    print("Starting twitterapi.io collector...")
    
    tweets = fetch_all_tweets(AR_HEALTH_QUERY, max_pages=20, target_n=100)
    print(f"Total tweets collected: {len(tweets)}")

    if tweets:
        print("--- Sample tweet ---")
        print(json.dumps(tweets[0], ensure_ascii=False, indent=2))

    out_path = "raw_health_tweets.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(tweets, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(tweets)} tweets to {out_path}")


if __name__ == "__main__":
    main()
