from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "raw"
NORMALIZED_DIR = ROOT / "normalized"
DEFAULT_OUTPUT = NORMALIZED_DIR / "audience_samples.jsonl"

GENRE_KEYS = ["revenge", "romance", "suspense", "comedy", "family", "workplace"]

KEYWORDS = {
    "paid_propensity": ["付费", "解锁", "会员", "充值", "短剧币", "花钱", "追更", "下一集"],
    "comment_propensity": ["评论", "吐槽", "弹幕", "讨论", "热评", "想说", "气死", "笑死"],
    "share_propensity": ["分享", "安利", "转发", "推荐", "拉朋友", "朋友圈"],
    "face_slapping_preference": ["爽", "打脸", "逆袭", "反杀", "复仇", "开挂", "上头", "过瘾"],
    "emotion_preference": ["虐", "哭", "感动", "心疼", "甜", "嗑", "代入", "误会", "拉扯"],
    "quality_sensitivity": ["演技", "剧情", "逻辑", "人设", "剪辑", "节奏", "台词", "制作"],
}

GENRE_KEYWORDS = {
    "revenge": ["复仇", "逆袭", "打脸", "反杀", "爽"],
    "romance": ["甜", "恋爱", "嗑", "CP", "感情", "拉扯"],
    "suspense": ["悬疑", "真相", "证据", "身份", "反转", "谜"],
    "comedy": ["搞笑", "笑死", "喜剧", "沙雕", "轻松"],
    "family": ["家庭", "亲情", "婆媳", "孩子", "父母"],
    "workplace": ["职场", "老板", "同事", "公司", "事业"],
}


def main() -> None:
    args = _parse_args()
    raw_paths = args.input or sorted(RAW_DIR.glob("*.jsonl"))
    samples = normalize_files(raw_paths)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for sample in samples:
            handle.write(json.dumps(sample, ensure_ascii=False) + "\n")
    print(f"Wrote {len(samples)} normalized audience samples to {args.output}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize and tag public audience samples.")
    parser.add_argument("--input", type=Path, action="append", help="Raw JSONL input; defaults to real_audience/raw/*.jsonl.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def normalize_files(paths: list[Path]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                raw = json.loads(line)
                sample = normalize_sample(raw)
                if not sample:
                    continue
                key = f"{sample['platform_type']}:{sample['text_hash']}"
                if key in seen:
                    continue
                seen.add(key)
                result.append(sample)
    return result


def normalize_sample(raw: dict[str, Any]) -> dict[str, Any] | None:
    text = sanitize_text(str(raw.get("text", "")))
    if len(text) < 4:
        return None
    signals = score_signals(text, raw.get("rating"))
    return {
        "sample_id": make_sample_id(raw.get("platform_type", "unknown"), text),
        "platform_type": raw.get("platform_type", "unknown"),
        "platform_display_name": raw.get("platform_display_name"),
        "source_kind": raw.get("source_kind", "unknown"),
        "source_url": raw.get("source_url"),
        "collected_at": raw.get("collected_at"),
        "published_at": raw.get("published_at"),
        "public_item": raw.get("public_item"),
        "rating": raw.get("rating"),
        "metrics": raw.get("metrics", {}),
        "text": text,
        "text_hash": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16],
        "behavior_signals": {key: signals[key] for key in KEYWORDS},
        "genre_signals": {key: signals[key] for key in GENRE_KEYS},
    }


def sanitize_text(text: str) -> str:
    text = re.sub(r"https?://\S+", "[url]", text)
    text = re.sub(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", "[email]", text)
    text = re.sub(r"(?<!\d)1[3-9]\d{9}(?!\d)", "[phone]", text)
    text = re.sub(r"@\S+", "@[user]", text)
    text = re.sub(r"\b\d{12,}\b", "[id]", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def score_signals(text: str, rating: Any = None) -> dict[str, float]:
    signal_scores: dict[str, float] = {}
    rating_adjustment = _rating_adjustment(rating)
    for key, keywords in KEYWORDS.items():
        signal_scores[key] = _score_keyword_group(text, keywords, rating_adjustment)

    genre_raw = {
        key: max(0.05, _keyword_hits(text, keywords))
        for key, keywords in GENRE_KEYWORDS.items()
    }
    total = sum(genre_raw.values()) or 1.0
    for key in GENRE_KEYS:
        signal_scores[key] = round(genre_raw[key] / total, 4)
    return signal_scores


def make_sample_id(platform_type: str, text: str) -> str:
    digest = hashlib.sha256(f"{platform_type}:{text}".encode("utf-8")).hexdigest()[:12]
    return f"aud_{digest}"


def _score_keyword_group(text: str, keywords: list[str], rating_adjustment: float) -> float:
    hits = _keyword_hits(text, keywords)
    score = min(1.0, 0.18 + hits * 0.18 + rating_adjustment)
    return round(max(0.02, score), 4)


def _keyword_hits(text: str, keywords: list[str]) -> int:
    lowered = text.lower()
    return sum(1 for keyword in keywords if keyword.lower() in lowered)


def _rating_adjustment(rating: Any) -> float:
    try:
        value = float(rating)
    except (TypeError, ValueError):
        return 0.0
    return max(-0.1, min(0.1, (value - 3.0) * 0.05))


if __name__ == "__main__":
    main()

