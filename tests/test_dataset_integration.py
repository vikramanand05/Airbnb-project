from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

PROCESSED = Path("data/processed")


@pytest.mark.integration
def test_supplied_dataset_verified_facts() -> None:
    quality_path = PROCESSED / "data_quality.json"
    listings_path = PROCESSED / "listings.parquet"
    reviews_path = PROCESSED / "review_events.parquet"
    if not all(path.exists() for path in (quality_path, listings_path, reviews_path)):
        pytest.skip("Run `airbnb-analysis all` to create integration-test data.")
    quality = json.loads(quality_path.read_text(encoding="utf-8"))
    listings = pd.read_parquet(listings_path)
    reviews = pd.read_parquet(reviews_path)

    assert quality["source_document_count"] == 5_555
    assert len(listings) == 5_555
    assert listings["listing_id"].is_unique
    assert int(listings["coordinate_valid"].sum()) == 5_555
    assert len(reviews) == 149_792
    assert reviews["review_date"].notna().all()
    assert quality["currency_fields_found"] == []
    assert quality["currency_verified"] is False
    assert set([30, 60, 90, 365]) == {
        int(column.rsplit("_", 1)[1])
        for column in listings.columns
        if column.startswith("availability_") and column != "availability_valid"
    }

