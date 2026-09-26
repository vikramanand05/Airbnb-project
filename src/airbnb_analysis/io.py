"""Input and output helpers for local JSON and analytical tables."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd


def load_json_documents(path: str | Path) -> list[dict[str, Any]]:
    """Load a JSON array and validate its top-level structure."""
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(
            f"JSON source not found: {source}. Set AIRBNB_JSON_PATH or pass --json."
        )
    with source.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError("Expected the JSON source to contain a top-level array.")
    if not all(isinstance(item, dict) for item in payload):
        raise ValueError("Every element in the JSON array must be an object.")
    return payload


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    """Return a streaming SHA-256 checksum for source provenance."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_processed_tables(
    processed_dir: str | Path,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Read the cleaned analytical model, preferring Parquet."""
    directory = Path(processed_dir)
    listings_parquet = directory / "listings.parquet"
    reviews_parquet = directory / "review_events.parquet"
    listings_csv = directory / "listings.csv"
    reviews_csv = directory / "review_events.csv"

    if listings_parquet.exists() and reviews_parquet.exists():
        listings = pd.read_parquet(listings_parquet)
        reviews = pd.read_parquet(reviews_parquet)
    elif listings_csv.exists() and reviews_csv.exists():
        listings = pd.read_csv(listings_csv, low_memory=False)
        reviews = pd.read_csv(reviews_csv, low_memory=False)
        for column in ("first_review", "last_review", "last_scraped"):
            if column in listings:
                listings[column] = pd.to_datetime(
                    listings[column], errors="coerce"
                )
        if "review_date" in reviews:
            reviews["review_date"] = pd.to_datetime(
                reviews["review_date"], errors="coerce"
            )
    else:
        raise FileNotFoundError(
            f"Cleaned tables are missing in {directory}. Run `airbnb-analysis clean`."
        )

    quality_path = directory / "data_quality.json"
    quality = (
        json.loads(quality_path.read_text(encoding="utf-8"))
        if quality_path.exists()
        else {}
    )
    return listings, reviews, quality


def write_json(payload: dict[str, Any], path: str | Path) -> None:
    """Write deterministic, human-readable JSON."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
