"""Reproducible exploratory analysis and findings report generation."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from airbnb_analysis.io import read_processed_tables, write_json


def _clean_label(value: Any) -> str:
    if pd.isna(value) or str(value).strip() == "":
        return "Unknown"
    return str(value).strip()


def _markdown_table(frame: pd.DataFrame, digits: int = 1) -> str:
    if frame.empty:
        return "_No rows available._"
    display = frame.copy()
    for column in display.select_dtypes(include=["number"]).columns:
        precision = 0 if column.endswith("_count") or column == "horizon_days" else digits
        display[column] = display[column].map(
            lambda value, places=precision: ""
            if pd.isna(value)
            else f"{value:,.{places}f}"
        )
    headers = [str(column).replace("_", " ").title() for column in display.columns]
    rows = []
    for values in display.astype(str).itertuples(index=False, name=None):
        rows.append("| " + " | ".join(value.replace("|", "\\|") for value in values) + " |")
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
            *rows,
        ]
    )


def build_market_summary(listings: pd.DataFrame) -> pd.DataFrame:
    """Build independent, alphabetical within-market price summaries."""
    valid = listings[listings["price"].notna() & (listings["price"] > 0)].copy()
    valid["market"] = valid["market"].map(_clean_label)
    summary = (
        valid.groupby("market", dropna=False)
        .agg(
            listing_count=("listing_id", "nunique"),
            median_price=("price", "median"),
            price_q1=("price", lambda values: values.quantile(0.25)),
            price_q3=("price", lambda values: values.quantile(0.75)),
            extreme_price_count=("price_extreme", "sum"),
        )
        .reset_index()
    )
    return summary.sort_values("market", kind="stable").reset_index(drop=True)


def _top_amenities(listings: pd.DataFrame, limit: int = 15) -> pd.DataFrame:
    counts: Counter[str] = Counter()
    for value in listings["amenities"].dropna():
        counts.update(item.strip() for item in str(value).split("|") if item.strip())
    return pd.DataFrame(counts.most_common(limit), columns=["amenity", "listing_count"])


def _missingness(listings: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "government_area",
        "bedrooms",
        "bathrooms",
        "cleaning_fee",
        "security_deposit",
        "review_score_rating",
        "price",
        "longitude",
        "latitude",
    ]
    return pd.DataFrame(
        {
            "field": columns,
            "missing_count": [int(listings[column].isna().sum()) for column in columns],
            "missing_percent": [
                listings[column].isna().mean() * 100 for column in columns
            ],
        }
    ).sort_values(["missing_count", "field"], ascending=[False, True])


def generate_eda(
    processed_dir: str | Path, report_path: str | Path
) -> dict[str, Any]:
    """Compute and export the EDA report and compact BI summary tables."""
    listings, reviews, quality = read_processed_tables(processed_dir)
    destination = Path(processed_dir)
    report_target = Path(report_path)
    report_target.parent.mkdir(parents=True, exist_ok=True)

    countries = (
        listings.assign(country=listings["country"].map(_clean_label))
        .groupby("country")
        .size()
        .rename("listing_count")
        .reset_index()
        .sort_values(["listing_count", "country"], ascending=[False, True])
    )
    markets = (
        listings.assign(market=listings["market"].map(_clean_label))
        .groupby("market")
        .size()
        .rename("listing_count")
        .reset_index()
        .sort_values(["listing_count", "market"], ascending=[False, True])
    )
    room_types = (
        listings.assign(room_type=listings["room_type"].map(_clean_label))
        .groupby("room_type")
        .size()
        .rename("listing_count")
        .reset_index()
        .sort_values(["listing_count", "room_type"], ascending=[False, True])
    )
    property_types = (
        listings.assign(property_type=listings["property_type"].map(_clean_label))
        .groupby("property_type")
        .size()
        .rename("listing_count")
        .reset_index()
        .sort_values(["listing_count", "property_type"], ascending=[False, True])
        .head(15)
    )
    market_summary = build_market_summary(listings)
    missingness = _missingness(listings)
    amenities = _top_amenities(listings)

    availability_rows = []
    for horizon in (30, 60, 90, 365):
        values = listings[f"availability_{horizon}"].dropna()
        availability_rows.append(
            {
                "horizon_days": horizon,
                "listing_count": len(values),
                "median_available_days": values.median(),
                "q1_available_days": values.quantile(0.25),
                "q3_available_days": values.quantile(0.75),
            }
        )
    availability = pd.DataFrame(availability_rows)

    valid_ratings = listings["review_score_rating"].dropna()
    review_start = reviews["review_date"].min() if not reviews.empty else pd.NaT
    review_end = reviews["review_date"].max() if not reviews.empty else pd.NaT
    last_scraped = listings["last_scraped"].max()

    market_summary.to_csv(destination / "market_summary.csv", index=False)
    countries.to_csv(destination / "country_coverage.csv", index=False)
    missingness.to_csv(destination / "missingness.csv", index=False)
    availability.to_csv(destination / "availability_summary.csv", index=False)

    summary = {
        "listing_count": int(len(listings)),
        "review_event_count": int(len(reviews)),
        "country_count": int(listings["country"].nunique(dropna=True)),
        "market_count": int(listings["market"].replace("", np.nan).nunique(dropna=True)),
        "valid_coordinate_count": int(listings["coordinate_valid"].sum()),
        "median_rating": float(valid_ratings.median()) if not valid_ratings.empty else None,
        "rating_sample_size": int(len(valid_ratings)),
        "review_date_min": review_start,
        "review_date_max": review_end,
        "data_freshness": last_scraped,
        "price_unit": "source price units",
    }
    write_json(summary, destination / "eda_summary.json")

    report = f"""# Airbnb exploratory data analysis

Generated from `{quality.get('source_file', 'source JSON')}` using the deterministic cleaning pipeline.

## Scope and coverage

- Clean listings: **{len(listings):,}** from **{quality.get('source_document_count', len(listings)):,}** source documents.
- Dated review events: **{len(reviews):,}** spanning **{review_start:%Y-%m-%d}** to **{review_end:%Y-%m-%d}**.
- Geography: **{summary['country_count']} countries** and **{summary['market_count']} named markets**.
- Valid GeoJSON coordinate pairs: **{int(listings['coordinate_valid'].sum()):,}**. Coordinates are interpreted as `[longitude, latitude]`.
- Latest source scrape date: **{last_scraped:%Y-%m-%d}**.

### Country coverage

{_markdown_table(countries, digits=0)}

### Largest markets by listing count

{_markdown_table(markets.head(15), digits=0)}

## Missingness and data quality

Missing numeric values remain null. They are not imputed with zero or a median.

{_markdown_table(missingness, digits=1)}

- Duplicate listing IDs excluded: **{quality.get('duplicate_listing_count', 0):,}**. The deterministic rule keeps the first source occurrence.
- Listings with missing IDs excluded: **{quality.get('excluded_missing_id_count', 0):,}**.
- Missing prices: **{int(listings['price_missing'].sum()):,}**; zero or negative prices: **{int(listings['price_non_positive'].sum()):,}**.
- Extreme positive prices retained and flagged: **{int(listings['price_extreme'].sum()):,}**, using each market's 3-IQR outer fences.
- Invalid availability snapshots: **{int((~listings['availability_valid']).sum()):,}**.

## Property and room mix

### Room types

{_markdown_table(room_types, digits=0)}

### Most common property types

{_markdown_table(property_types, digits=0)}

## Prices

The source contains **no currency field**. All monetary figures are labeled **source price units**. Each row below is an independent description inside one market, sorted alphabetically. Do not compare or rank markets, countries, or the global dataset by these values, and do not convert currencies by guessing.

{_markdown_table(market_summary, digits=1)}

## Ratings

- Listings with an overall rating: **{len(valid_ratings):,}** of **{len(listings):,}**.
- Median source rating: **{valid_ratings.median():.1f} / 100**.
- Interquartile range: **{valid_ratings.quantile(0.25):.1f} to {valid_ratings.quantile(0.75):.1f}**.

Ratings are guest-submitted and subject to selection bias. Missing ratings are not scored as zero.

## Amenities

Amenity labels are counted exactly as supplied after whitespace trimming.

{_markdown_table(amenities, digits=0)}

## Availability snapshots

These values are forward-looking counts of available days at the source scrape date. They are **not reservations, realized occupancy, bookings, demand, or revenue**. The pipeline deliberately does not calculate `1 - availability_365 / 365` as occupancy.

{_markdown_table(availability, digits=1)}

## Review activity proxy

The review-event table supports historical review counts by month from **{review_start:%Y-%m-%d}** to **{review_end:%Y-%m-%d}**. This is a **review-activity proxy** only. Reviews are an incomplete, delayed, and biased sample of stays, so the project does not present them as bookings, demand, occupancy, or true seasonality.

## Source-schema verification

The JSON, not the brief's example, is the source of truth. Verified differences:

- Location is nested at `address.location`, with GeoJSON coordinates in `[longitude, latitude]` order.
- Market and government area are under `address`.
- Host details are nested under `host`.
- Availability contains 30-, 60-, 90-, and 365-day snapshot counts rather than start/end dates.
- Overall rating is `review_scores.review_scores_rating`.
- All supplied reviews have a usable date, but no review-level rating field is present.
- No price currency field is present.
"""
    report_target.write_text(report, encoding="utf-8")
    return summary

