from __future__ import annotations

import pandas as pd

from airbnb_analysis.queries import (
    local_neighborhood_summary,
    mongo_neighborhood_pipeline,
    nearby_listings_pipeline,
    summarize_mongo_groups,
)


def test_local_and_mongo_grouped_results_have_analytical_parity() -> None:
    listings = pd.DataFrame(
        {
            "listing_id": ["1", "2", "3", "4"],
            "market": ["A", "A", "A", "B"],
            "government_area": ["North", "North", "South", "Elsewhere"],
            "price": [10.0, 30.0, 20.0, 999.0],
            "review_score_rating": [80.0, 100.0, 90.0, 10.0],
        }
    )
    local = local_neighborhood_summary(listings, "A").sort_values("government_area").reset_index(drop=True)
    groups = [
        {
            "_id": "North",
            "listing_ids": ["1", "2"],
            "prices": [10.0, 30.0],
            "ratings": [80.0, 100.0],
        },
        {
            "_id": "South",
            "listing_ids": ["3"],
            "prices": [20.0],
            "ratings": [90.0],
        },
    ]
    mongo = summarize_mongo_groups(groups, "A").sort_values("government_area").reset_index(drop=True)
    pd.testing.assert_frame_equal(local, mongo, check_dtype=False)


def test_mongo_pipeline_filters_one_market_and_positive_prices() -> None:
    pipeline = mongo_neighborhood_pipeline("Sydney")
    assert pipeline[0]["$match"]["address.market"] == "Sydney"
    assert {"$match": {"price": {"$gt": 0}}} in pipeline


def test_geospatial_pipeline_keeps_longitude_first() -> None:
    pipeline = nearby_listings_pipeline(151.2, -33.8)
    near = pipeline[0]["$geoNear"]["near"]
    assert near == {"type": "Point", "coordinates": [151.2, -33.8]}
    assert pipeline[0]["$geoNear"]["key"] == "address.location"

