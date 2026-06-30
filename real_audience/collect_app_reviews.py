from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
CATALOG_PATH = ROOT / "platform_catalog.json"
RAW_DIR = ROOT / "raw"
DEFAULT_OUTPUT = RAW_DIR / "app_store_reviews.jsonl"
ITUNES_SEARCH_URL = "https://itunes.apple.com/search"
ITUNES_REVIEW_URL = "https://itunes.apple.com/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"


def main() -> None:
    args = _parse_args()
    catalog = _load_catalog(args.catalog)
    platforms = catalog.get("platforms", [])
    selected = set(args.platform or [])
    if selected:
        platforms = [item for item in platforms if item.get("platform_type") in selected]

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    with output.open("a", encoding="utf-8") as handle:
        for platform in platforms:
            app = find_app(platform, country=args.country)
            if not app:
                continue
            for review in fetch_reviews(app["track_id"], args.country, args.limit_per_platform):
                sample = build_review_sample(platform, app, review)
                handle.write(json.dumps(sample, ensure_ascii=False) + "\n")
                written += 1
            time.sleep(args.delay)
    print(f"Wrote {written} public app review samples to {output}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect public Apple App Store reviews without user identifiers.")
    parser.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--country", default="cn")
    parser.add_argument("--limit-per-platform", type=int, default=20)
    parser.add_argument("--delay", type=float, default=0.4)
    parser.add_argument("--platform", action="append", help="Optional platform_type filter; can be repeated.")
    return parser.parse_args()


def _load_catalog(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_app(platform: dict[str, Any], country: str = "cn") -> dict[str, Any] | None:
    for term in platform.get("app_store_search_terms", []):
        url = f"{ITUNES_SEARCH_URL}?term={quote_plus(term)}&country={country}&entity=software&limit=5"
        data = _fetch_json(url)
        for item in data.get("results", []):
            track_name = str(item.get("trackName", ""))
            if _looks_like_match(track_name, term, platform.get("display_name", "")):
                return {
                    "track_id": item.get("trackId"),
                    "track_name": track_name,
                    "track_url": item.get("trackViewUrl"),
                    "search_term": term,
                }
    return None


def fetch_reviews(app_id: int | str, country: str = "cn", limit: int = 20) -> list[dict[str, Any]]:
    reviews: list[dict[str, Any]] = []
    page = 1
    while len(reviews) < limit and page <= 10:
        url = f"{ITUNES_REVIEW_URL.format(page=page, app_id=app_id)}?l=zh_cn&cc={country}"
        data = _fetch_json(url)
        entries = data.get("feed", {}).get("entry", [])
        if not isinstance(entries, list) or not entries:
            break
        for entry in entries:
            if "im:rating" not in entry:
                continue
            reviews.append(entry)
            if len(reviews) >= limit:
                break
        page += 1
    return reviews


def build_review_sample(platform: dict[str, Any], app: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    title = _label(review.get("title"))
    content = _label(review.get("content"))
    rating_raw = _label(review.get("im:rating"))
    rating = int(rating_raw) if str(rating_raw).isdigit() else None
    source_url = _href(review.get("link")) or app.get("track_url") or ""
    return {
        "platform_type": platform["platform_type"],
        "platform_display_name": platform.get("display_name", platform["platform_type"]),
        "source_kind": "app_store_review",
        "source_url": source_url,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "published_at": _label(review.get("updated")),
        "public_item": app.get("track_name"),
        "rating": rating,
        "metrics": {},
        "text": " ".join(part for part in [title, content] if part).strip(),
    }


def _fetch_json(url: str) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "DramaSmallvilleRealAudience/1.0"})
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"Fetch skipped: {url} ({exc})")
        return {}


def _looks_like_match(track_name: str, term: str, display_name: str) -> bool:
    normalized_name = track_name.lower()
    candidates = [term.lower(), display_name.lower()]
    return any(candidate and candidate in normalized_name for candidate in candidates)


def _label(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("label", "")).strip()
    return str(value or "").strip()


def _href(value: Any) -> str:
    if isinstance(value, dict):
        attrs = value.get("attributes", {})
        if isinstance(attrs, dict):
            return str(attrs.get("href", "")).strip()
    return ""


if __name__ == "__main__":
    main()

