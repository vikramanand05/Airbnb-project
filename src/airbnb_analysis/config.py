"""Runtime configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Application settings with safe local defaults."""

    mongodb_uri: str | None
    mongodb_database: str
    mongodb_collection: str
    json_path: Path
    processed_dir: Path

    @classmethod
    def from_env(cls) -> Settings:
        load_dotenv()
        return cls(
            mongodb_uri=os.getenv("MONGODB_URI") or None,
            mongodb_database=os.getenv("MONGODB_DATABASE", "sample_airbnb"),
            mongodb_collection=os.getenv(
                "MONGODB_COLLECTION", "listingsAndReviews"
            ),
            json_path=Path(
                os.getenv("AIRBNB_JSON_PATH", "data/raw/sample_airbnb.json")
            ),
            processed_dir=Path(
                os.getenv("AIRBNB_PROCESSED_DIR", "data/processed")
            ),
        )

