from __future__ import annotations

import json
import os
from pathlib import Path

from schemas.audience_distribution import AudienceDistributionConfig


CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "audience_research.json"


def _real_audience_config_path() -> Path:
    """real_audience/profiles 的位置。

    原实现硬编码 `parents[3]`,把目录层级当隐式契约——backend 一旦迁移
    到别处就崩。改为环境变量优先、默认值兜底,保持向后兼容。
    """
    env = os.getenv("REAL_AUDIENCE_PROFILES_DIR")
    if env:
        p = Path(env)
        return p / "audience_distributions.json" if p.is_dir() else p
    # 默认:项目根/real_audience/profiles/(backend 在 script simulation/backend)
    return (
        Path(__file__).resolve().parents[3]
        / "real_audience"
        / "profiles"
        / "audience_distributions.json"
    )


SHORT_DRAMA_PLATFORMS = {
    "wechat_minidrama",
    "xidian_short_drama",
    "hongguo_short_drama",
    "douyin_short_drama",
    "kuaishou_short_drama",
}
WEB_NOVEL_PLATFORMS = {
    "fanqie",
    "fanqie_web_novel",
    "jinjiang",
    "qimao_web_novel",
    "qidian",
}


def load_distribution(distribution_id: str | None, platform_type: str) -> AudienceDistributionConfig:
    default_configs = _load_configs(CONFIG_PATH)
    real_configs = _load_configs(_real_audience_config_path())
    if distribution_id:
        if distribution_id in real_configs:
            return AudienceDistributionConfig.model_validate(real_configs[distribution_id])
        if distribution_id in default_configs:
            return AudienceDistributionConfig.model_validate(default_configs[distribution_id])

    real_platform_config = _find_platform_config(real_configs, platform_type)
    if real_platform_config:
        return AudienceDistributionConfig.model_validate(real_platform_config)

    if platform_type in SHORT_DRAMA_PLATFORMS:
        return AudienceDistributionConfig.model_validate(default_configs["micro_drama_2024_default"])
    if platform_type in WEB_NOVEL_PLATFORMS:
        return AudienceDistributionConfig.model_validate(default_configs["web_novel_2024_default"])
    return AudienceDistributionConfig.model_validate(default_configs["web_novel_2024_default"])


def _load_configs(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _find_platform_config(configs: dict, platform_type: str) -> dict | None:
    matches = [
        config
        for config in configs.values()
        if config.get("platform_type") == platform_type
    ]
    if not matches:
        return None
    return max(matches, key=lambda config: config.get("confidence", 0.0))
