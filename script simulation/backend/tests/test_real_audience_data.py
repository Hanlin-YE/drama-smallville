from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(BACKEND_ROOT))

from main import app
from population.distribution_loader import load_distribution
from real_audience.build_distributions import build_distributions
from real_audience.normalize_audience_text import normalize_files


FIXTURE_RAW = PROJECT_ROOT / "real_audience" / "fixtures" / "offline_raw_samples.jsonl"
CATALOG = PROJECT_ROOT / "real_audience" / "platform_catalog.json"


def test_normalize_dedupes_masks_and_tags() -> None:
    samples = normalize_files([FIXTURE_RAW])

    assert len(samples) == 3
    fanqie = next(sample for sample in samples if sample["platform_type"] == "fanqie_web_novel")
    assert "13800138000" not in fanqie["text"]
    assert "test@example.com" not in fanqie["text"]
    assert "[phone]" in fanqie["text"]
    assert "[email]" in fanqie["text"]
    assert fanqie["behavior_signals"]["paid_propensity"] > 0.2

    douyin = next(sample for sample in samples if sample["platform_type"] == "douyin_short_drama")
    assert douyin["behavior_signals"]["share_propensity"] > 0.3
    assert douyin["behavior_signals"]["face_slapping_preference"] > 0.4
    assert set(douyin["genre_signals"]) == {"revenge", "romance", "suspense", "comedy", "family", "workplace"}


def test_build_distributions_from_normalized_fixture(tmp_path: Path) -> None:
    normalized_path = tmp_path / "audience_samples.jsonl"
    samples = normalize_files([FIXTURE_RAW])
    normalized_path.write_text(
        "".join(json.dumps(sample, ensure_ascii=False) + "\n" for sample in samples),
        encoding="utf-8",
    )

    distributions = build_distributions(normalized_path=normalized_path, catalog_path=CATALOG)

    assert len(distributions) == 8
    jinjiang = distributions["jinjiang_public_seed_v1"]
    assert jinjiang["platform_type"] == "jinjiang"
    assert jinjiang["sample_size"] == 1
    assert jinjiang["confidence"] <= 0.75
    assert set(jinjiang["beta_distributions"]) >= {
        "paid_propensity",
        "comment_propensity",
        "share_propensity",
        "face_slapping_preference",
        "emotion_preference",
        "quality_sensitivity",
    }
    assert len(jinjiang["dirichlet_distributions"]["genre_preferences"]) == 6


def test_loader_prefers_real_audience_exact_and_platform_then_fallback() -> None:
    exact = load_distribution("jinjiang_public_seed_v1", "jinjiang")
    assert exact.distribution_id == "jinjiang_public_seed_v1"
    assert exact.platform_type == "jinjiang"
    assert exact.sample_size is None or exact.sample_size >= 0

    platform = load_distribution(None, "qidian")
    assert platform.distribution_id == "qidian_public_seed_v1"

    fallback = load_distribution(None, "unknown_platform")
    assert fallback.distribution_id == "web_novel_2024_default"


def test_population_profile_set_api_accepts_distribution_id() -> None:
    client = TestClient(app)

    response = client.get(
        "/api/population/profile-set",
        params={
            "platform_type": "jinjiang",
            "distribution_id": "jinjiang_public_seed_v1",
            "business_goal": "retention",
            "max_agents": 4,
            "seed": 7,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["distribution_id"] == "jinjiang_public_seed_v1"
    assert data["platform_type"] == "jinjiang"
    assert 1 <= len(data["representative_agents"]) <= 4
    assert data["population_fit"]["distribution_error"] >= 0
