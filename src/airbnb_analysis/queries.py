"""Equivalent local and MongoDB analytical queries."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd

SUMMARY_COLUMNS = [
    "market",
    "government_area",
    "listing_count",
    "median_price",
    "price_q1",
    "price_q3",
    "median_rating",
]


def local_neighborhood_summary(
    listings: pd.DataFrame, market: str
) -> pd.DataFrame:
    """Summarize distributions inside one market only."""
    subset = listings[
        (listings["market"] == market)
        & listings["price"].notna()
        & (listings["price"] > 0)
    ].copy()
    if subset.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)
    grouped = (
        subset.groupby("government_area", dropna=False)
        .agg(
            listing_count=("listing_id", "nunique"),
            median_price=("price", "median"),
            price_q1=("price", lambda values: values.quantile(0.25)),
            price_q3=("price", lambda values: values.quantile(0.75)),
            median_rating=("review_score_rating", "median"),
        )
        .reset_index()
    )
    grouped.insert(0, "market", market)
    return grouped[SUMMARY_COLUMNS].sort_values(
        ["listing_count", "government_area"], ascending=[False, True]
    )


def mongo_neighborhood_pipeline(market: str) -> list[dict[str, Any]]:
    """Build an aggregation that performs market filtering and grouping in Atlas."""
    return [
        {
            "$match": {
                "address.market": market,
                "price": {"$ne": None},
            }
        },
        {
            "$project": {
                "government_area": "$address.government_area",
                "listing_id": {"$toString": "$_id"},
                "price": {
                    "$convert": {
                        "input": "$price",
                        "to": "double",
                        "onError": None,
                        "onNull": None,
                    }
                },
                "rating": {
                    "$convert": {
                        "input": "$review_scores.review_scores_rating",
                        "to": "double",
                        "onError": None,
                        "onNull": None,
                    }
                },
            }
        },
        {"$match": {"price": {"$gt": 0}}},
        {
            "$group": {
                "_id": "$government_area",
                "listing_ids": {"$addToSet": "$listing_id"},
                "prices": {"$push": "$price"},
                "ratings": {"$push": "$rating"},
            }
        },
    ]


def summarize_mongo_groups(
    groups: Iterable[dict[str, Any]], market: str
) -> pd.DataFrame:
    """Finish robust medians and quartiles from MongoDB-grouped arrays."""
    rows: list[dict[str, Any]] = []
    for group in groups:
        prices = pd.Series(group.get("prices") or [], dtype="float64").dropna()
        ratings = pd.Series(group.get("ratings") or [], dtype="float64").dropna()
        if prices.empty:
            continue
        rows.append(
            {
                "market": market,
                "government_area": group.get("_id"),
                "listing_count": len(set(group.get("listing_ids") or [])),
                "median_price": prices.median(),
                "price_q1": prices.quantile(0.25),
                "price_q3": prices.quantile(0.75),
                "median_rating": ratings.median() if not ratings.empty else None,
            }
        )
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS).sort_values(
        ["listing_count", "government_area"], ascending=[False, True]
    ) if rows else pd.DataFrame(columns=SUMMARY_COLUMNS)


def mongo_neighborhood_summary(collection: Any, market: str) -> pd.DataFrame:
    """Run the Atlas aggregation and return the local-equivalent schema."""
    groups = collection.aggregate(mongo_neighborhood_pipeline(market), allowDiskUse=True)
    return summarize_mongo_groups(groups, market)


def nearby_listings_pipeline(
    longitude: float, latitude: float, max_distance_meters: int = 5_000, limit: int = 100
) -> list[dict[str, Any]]:
    """Build a correct GeoJSON near query for the indexed location field."""
    return [
        {
            "$geoNear": {
                "near": {"type": "Point", "coordinates": [longitude, latitude]},
                "distanceField": "distance_meters",
                "maxDistance": max_distance_meters,
                "spherical": True,
                "key": "address.location",
            }
        },
        {"$limit": limit},
    ]

