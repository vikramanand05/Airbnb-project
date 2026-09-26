"""End-to-end cleaning pipeline and BI-ready exports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from airbnb_analysis.io import (
    load_json_documents,
    sha256_file,
    write_json,
)
from airbnb_analysis.schema import LISTING_DICTIONARY, REVIEW_DICTIONARY
from airbnb_analysis.transform import CleanResult, clean_documents


def _write_table(frame: pd.DataFrame, stem: Path) -> None:
    """Write equivalent CSV and Parquet representations."""
    frame.to_csv(stem.with_suffix(".csv"), index=False, date_format="%Y-%m-%d")
    frame.to_parquet(stem.with_suffix(".parquet"), index=False)


def export_clean_result(
    result: CleanResult, output_dir: str | Path, source_path: str | Path
) -> dict[str, Any]:
    """Export the analytical model, dictionary, and quality report."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    _write_table(result.listings, destination / "listings")
    _write_table(result.reviews, destination / "review_events")

    dictionary = pd.DataFrame(
        [
            {"table": "listings", "column": column, "type": dtype, "description": description}
            for column, dtype, description in LISTING_DICTIONARY
        ]
        + [
            {"table": "review_events", "column": column, "type": dtype, "description": description}
            for column, dtype, description in REVIEW_DICTIONARY
        ]
    )
    dictionary.to_csv(destination / "data_dictionary.csv", index=False)

    quality = dict(result.quality)
    quality["source_sha256"] = sha256_file(source_path)
    quality["output_files"] = [
        "listings.csv",
        "listings.parquet",
        "review_events.csv",
        "review_events.parquet",
        "data_dictionary.csv",
        "data_quality.json",
    ]
    write_json(quality, destination / "data_quality.json")
    return quality


def run_cleaning(
    source_path: str | Path, output_dir: str | Path
) -> CleanResult:
    """Load, clean, and export the source dataset."""
    documents = load_json_documents(source_path)
    result = clean_documents(documents, source_path)
    result.quality = export_clean_result(result, output_dir, source_path)
    return result

