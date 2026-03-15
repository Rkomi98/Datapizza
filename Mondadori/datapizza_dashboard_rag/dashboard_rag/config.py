from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PACKAGE_DIR = Path(__file__).resolve().parent
APP_DIR = PACKAGE_DIR.parent
REPO_DIR = APP_DIR.parent


@dataclass(frozen=True)
class Settings:
    app_dir: Path
    repo_dir: Path
    datasets_dir: Path
    storage_dir: Path
    qdrant_dir: Path
    sqlite_path: Path
    manifests_dir: Path
    profiles_dir: Path
    monitoring_path: Path
    openai_api_key: str
    chat_model: str
    embedding_model: str
    embedding_dimensions: int


def load_environment() -> None:
    load_dotenv(REPO_DIR / ".env", override=False)
    load_dotenv(APP_DIR / ".env", override=False)


def ensure_directories() -> None:
    for path in (
        APP_DIR / "datasets",
        APP_DIR / "storage",
        APP_DIR / "storage" / "qdrant",
        APP_DIR / "storage" / "sqlite",
        APP_DIR / "storage" / "manifests",
        APP_DIR / "storage" / "profiles",
        APP_DIR / "storage" / "monitoring",
    ):
        path.mkdir(parents=True, exist_ok=True)


def load_settings() -> Settings:
    load_environment()
    ensure_directories()

    return Settings(
        app_dir=APP_DIR,
        repo_dir=REPO_DIR,
        datasets_dir=APP_DIR / "datasets",
        storage_dir=APP_DIR / "storage",
        qdrant_dir=APP_DIR / "storage" / "qdrant",
        sqlite_path=APP_DIR / "storage" / "sqlite" / "dashboard.db",
        manifests_dir=APP_DIR / "storage" / "manifests",
        profiles_dir=APP_DIR / "storage" / "profiles",
        monitoring_path=APP_DIR / "storage" / "monitoring" / "events.jsonl",
        openai_api_key=(os.getenv("Openai") or "").strip(),
        chat_model=(os.getenv("DATAPIZZA_CHAT_MODEL") or "gpt-4o-mini").strip(),
        embedding_model=(os.getenv("DATAPIZZA_EMBEDDING_MODEL") or "text-embedding-3-small").strip(),
        embedding_dimensions=1536,
    )


def has_openai_key(settings: Settings) -> bool:
    return bool(settings.openai_api_key)

