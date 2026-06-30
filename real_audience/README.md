# Real Audience Data Layer

This directory stores public-only audience evidence used to seed the
Audience Population fitting pipeline.

## Data Notice (Public Repo)

本目录下的 `raw/`、`normalized/`、`profiles/` **已通过 `.gitignore` 从公开仓库移除**，仅保留本地副本。原因：这些文件含从公开 App Store / 评论页采集的真实用户评论文本，虽为公开数据且已做去标识化（无用户 ID、无头像、无设备信息、无位置信息），但出于对真实用户的尊重，不纳入公开仓库。

保留入库的内容：
- `fixtures/*.jsonl` — 合成的离线测试数据，可安全公开
- `*.py` — 采集 / 清洗 / 建分布的代码
- `platform_catalog.json` — 平台目录（无用户数据）
- 本 README

如需在本地复现完整数据，按下方 Typical Commands 重新采集即可。

## Boundaries

- Collect only public app reviews, public comment pages, public rankings, and
  public report summaries.
- Do not collect login-only pages, private messages, user homepages, avatars,
  device details, location details, or persistent user identifiers.
- Raw samples must keep source provenance, platform, timestamp, public text,
  rating, and aggregate public metrics only.
- Generated persona cards must summarize patterns; they must not quote long
  user-identifiable comments.

## Layout

- `platform_catalog.json`: platform pool and collection status.
- `raw/*.jsonl`: public raw samples without user identifiers.
- `normalized/*.jsonl`: cleaned and tagged audience samples.
- `profiles/audience_distributions.json`: backend-loadable distribution config.
- `profiles/persona_seed_cards.md`: human-readable platform seed cards.
- `fixtures/*.jsonl`: offline test fixtures.

## Typical Commands

```bash
python -m real_audience.collect_app_reviews --limit-per-platform 20
python -m real_audience.collect_public_comments
python -m real_audience.normalize_audience_text
python -m real_audience.build_distributions
```

Network collection is intentionally separate from tests. Tests use fixtures and
do not call public services.

