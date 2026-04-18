from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    offline_mode: bool = os.getenv("OFFLINE_MODE", "true").lower() == "true"
    max_reasoning_depth: int = int(os.getenv("MAX_REASONING_DEPTH", "3"))
    default_language: str = os.getenv("DEFAULT_LANGUAGE", "ar")


settings = Settings()
