from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    scriptmind_base_url: str = os.getenv(
        "SCRIPTMIND_BASE_URL", "https://scriptmind-50bc6328.eazo.dev"
    )
    scriptmind_api_key: str = os.getenv(
        "SCRIPTMIND_API_KEY", "sm_live_a8f3k2x9p1q7n5m4j6r0w8e2t"
    )
    model_name: str = os.getenv("MODEL_NAME", "mock")
    llm_timeout_seconds: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "120"))
    trace_dir: str = os.getenv("TRACE_DIR", "backend/storage/traces")
    schema_version: str = "p0.v1"
    use_scriptmind: bool = os.getenv("USE_SCRIPTMIND", "true").lower() in ("1", "true", "yes")


settings = Settings()
