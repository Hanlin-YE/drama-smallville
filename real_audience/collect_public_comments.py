from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
CATALOG_PATH = ROOT / "platform_catalog.json"
RAW_DIR = ROOT / "raw"
DEFAULT_OUTPUT = RAW_DIR / "public_comments.jsonl"


class TextBlockParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.blocks: list[str] = []
        self._current: list[str] = []
        self._capture_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"p", "li", "article", "blockquote"}:
            self._capture_depth += 1
            self._current = []

    def handle_endtag(self, tag: str) -> None:
        if tag in {"p", "li", "article", "blockquote"} and self._capture_depth:
            text = _compact_text("".join(self._current))
            if len(text) >= 12:
                self.blocks.append(text)
            self._current = []
            self._capture_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._capture_depth:
            self._current.append(data)


def main() -> None:
    args = _parse_args()
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    platforms = catalog.get("platforms", [])
    selected = set(args.platform or [])
    if selected:
        platforms = [item for item in platforms if item.get("platform_type") in selected]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with args.output.open("a", encoding="utf-8") as handle:
        for platform in platforms:
            for url in platform.get("public_comment_urls", []):
                for text in fetch_public_text_blocks(url):
                    sample = {
                        "platform_type": platform["platform_type"],
                        "platform_display_name": platform.get("display_name", platform["platform_type"]),
                        "source_kind": "public_comment_page",
                        "source_url": url,
                        "collected_at": datetime.now(timezone.utc).isoformat(),
                        "published_at": None,
                        "public_item": None,
                        "rating": None,
                        "metrics": {},
                        "text": text,
                    }
                    handle.write(json.dumps(sample, ensure_ascii=False) + "\n")
                    written += 1
    print(f"Wrote {written} public comment samples to {args.output}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect text blocks from configured public comment URLs only.")
    parser.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--platform", action="append", help="Optional platform_type filter; can be repeated.")
    return parser.parse_args()


def fetch_public_text_blocks(url: str) -> list[str]:
    request = Request(url, headers={"User-Agent": "DramaSmallvilleRealAudience/1.0"})
    try:
        with urlopen(request, timeout=20) as response:
            html = response.read().decode("utf-8", errors="ignore")
    except (HTTPError, URLError, TimeoutError) as exc:
        print(f"Fetch skipped: {url} ({exc})")
        return []
    parser = TextBlockParser()
    parser.feed(html)
    return dedupe_blocks(parser.blocks)


def dedupe_blocks(blocks: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for block in blocks:
        key = block.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(block)
    return result


def _compact_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


if __name__ == "__main__":
    main()

