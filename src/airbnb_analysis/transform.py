"""Deterministic transformation from nested source documents to analysis tables."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class CleanResult:
    """Cleaned tables plus auditable quality metadata."""

    listings: pd.DataFrame
    reviews: pd.DataFrame
    quality: dict[str, Any]


def get_nested(document: dict[str, Any], path: str, default: Any = None) -> Any:
    """Safely read a dot-delimited nested field."""
    value: Any = document
    for key in path.split("."):
        if not isinstance(value, dict) or key not in value:
            return default
        value = value[key]
    return value


def parse_number(value: Any) -> float | None:
    """Parse ordinary values and common extended-JSON numeric wrappers."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, dict):
        for key in ("$numberDecimal", "$numberDouble", "$numberInt", "$numberLong"):
            if key in value:
                value = value[key]
                break
        else:
            return None
    if isinstance(value, int | float | Decimal):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        if not cleaned:
            return None
        try:
            number = float(Decimal(cleaned))
            return number if math.isfinite(number) else None
        except (InvalidOperation, ValueError):
            return None
    return None


def parse_bool(value: Any) -> bool | None:
    """Parse nullable source booleans without inventing a default."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "t", "yes", "y", "1"}:
            return True
        if normalized in {"false", "f", "no", "n", "0"}:
            return False
    if value in (0, 1):
        return bool(value)
    return None


def validate_coordinates(coordinates: Any) -> tuple[float | None, float | None, bool, str]:
    """Validate a GeoJSON `[longitude, latitude]` pair and world bounds."""
    if not isinstance(coordinates, list | tuple) or len(coordinates) < 2:
        return None, None, False, "missing_or_malformed"
    longitude = parse_number(coordinates[0])
    latitude = parse_number(coordinates[1])
    if longitude is None or latitude is None:
        return longitude, latitude, False, "non_numeric"
    if not -180 <= longitude <= 180:
        return longitude, latitude, False, "longitude_out_of_bounds"
    if not -90 <= latitude <= 90:
        return longitude, latitude, False, "latitude_out_of_bounds"
    return longitude, latitude, True, ""


def _availability_is_valid(row: dict[str, Any]) -> bool:
    horizons = {30: row["availability_30"], 60: row["availability_60"], 90: row["availability_90"], 365: row["availability_365"]}
    supplied = [(days, value) for days, value in horizons.items() if value is not None]
    return bool(supplied) and all(0 <= value <= days for days, value in supplied)


def extract_listing(
    document: dict[str, Any], source_file: str, source_row: int
) -> dict[str, Any]:
    """Flatten analysis-relevant source fields while retaining provenance."""
    longitude, latitude, coordinate_valid, coordinate_issue = validate_coordinates(
        get_nested(document, "address.location.coordinates")
    )
    amenities = document.get("amenities")
    amenity_list = [str(item).strip() for item in amenities or [] if str(item).strip()]
    price = parse_number(document.get("price"))

    row: dict[str, Any] = {
        "listing_id": str(document.get("_id", "")).strip(),
        "name": document.get("name"),
        "listing_url": document.get("listing_url"),
        "host_id": str(get_nested(document, "host.host_id", "") or "").strip(),
        "host_name": get_nested(document, "host.host_name"),
        "host_is_superhost": parse_bool(get_nested(document, "host.host_is_superhost")),
        "host_identity_verified": parse_bool(
            get_nested(document, "host.host_identity_verified")
        ),
        "country": get_nested(document, "address.country"),
        "country_code": get_nested(document, "address.country_code"),
        "market": get_nested(document, "address.market"),
        "government_area": get_nested(document, "address.government_area"),
        "suburb": get_nested(document, "address.suburb"),
        "longitude": longitude,
        "latitude": latitude,
        "coordinate_valid": coordinate_valid,
        "coordinate_issue": coordinate_issue,
        "location_exact": parse_bool(
            get_nested(document, "address.location.is_location_exact")
        ),
        "property_type": document.get("property_type"),
        "room_type": document.get("room_type"),
        "bed_type": document.get("bed_type"),
        "accommodates": parse_number(document.get("accommodates")),
        "bedrooms": parse_number(document.get("bedrooms")),
        "bathrooms": parse_number(document.get("bathrooms")),
        "beds": parse_number(document.get("beds")),
        "minimum_nights": parse_number(document.get("minimum_nights")),
        "maximum_nights": parse_number(document.get("maximum_nights")),
        "price": price,
        "price_unit": "source price units",
        "currency_verified": False,
        "cleaning_fee": parse_number(document.get("cleaning_fee")),
        "security_deposit": parse_number(document.get("security_deposit")),
        "extra_people": parse_number(document.get("extra_people")),
        "guests_included": parse_number(document.get("guests_included")),
        "price_missing": price is None,
        "price_non_positive": price is not None and price <= 0,
        "review_score_rating": parse_number(
            get_nested(document, "review_scores.review_scores_rating")
        ),
        "number_of_reviews": parse_number(document.get("number_of_reviews")),
        "availability_30": parse_number(
            get_nested(document, "availability.availability_30")
        ),
        "availability_60": parse_number(
            get_nested(document, "availability.availability_60")
        ),
        "availability_90": parse_number(
            get_nested(document, "availability.availability_90")
        ),
        "availability_365": parse_number(
            get_nested(document, "availability.availability_365")
        ),
        "first_review": document.get("first_review"),
        "last_review": document.get("last_review"),
        "last_scraped": document.get("last_scraped"),
        "calendar_last_scraped": document.get("calendar_last_scraped"),
        "amenities_count": len(amenity_list),
        "amenities": " | ".join(amenity_list),
        "source_file": source_file,
        "source_row": source_row,
    }
    row["availability_valid"] = _availability_is_valid(row)
    return row


def _review_rows(
    document: dict[str, Any], listing: dict[str, Any]
) -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    invalid_dates = 0
    for review in document.get("reviews") or []:
        date = pd.to_datetime(review.get("date"), errors="coerce")
        if pd.isna(date):
            invalid_dates += 1
            continue
        review_id = str(review.get("_id", "")).strip()
        rows.append(
            {
                "review_id": review_id or None,
                "listing_id": listing["listing_id"],
                "review_date": date,
                "review_year_month": date.strftime("%Y-%m"),
                "market": listing["market"],
                "government_area": listing["government_area"],
                "country": listing["country"],
                "source_listing_row": listing["source_row"],
            }
        )
    return rows, invalid_dates


def flag_price_outliers(listings: pd.DataFrame) -> pd.DataFrame:
    """Flag market-specific outer-fence outliers without removing records."""
    result = listings.copy()
    result["price_outlier_lower"] = np.nan
    result["price_outlier_upper"] = np.nan
    result["price_extreme"] = False

    for market, indexes in result.groupby("market", dropna=False).groups.items():
        del market
        values = result.loc[indexes, "price"]
        valid = values[(values > 0) & values.notna()]
        if len(valid) < 4:
            continue
        q1, q3 = valid.quantile([0.25, 0.75])
        iqr = q3 - q1
        lower = max(0.0, q1 - 3 * iqr)
        upper = q3 + 3 * iqr
        result.loc[indexes, "price_outlier_lower"] = lower
        result.loc[indexes, "price_outlier_upper"] = upper
        comparable = result.loc[indexes, "price"].notna() & (
            result.loc[indexes, "price"] > 0
        )
        extreme = comparable & (
            (result.loc[indexes, "price"] < lower)
            | (result.loc[indexes, "price"] > upper)
        )
        result.loc[indexes, "price_extreme"] = extreme
    return result


def _missingness(listings: pd.DataFrame, columns: Iterable[str]) -> dict[str, int]:
    return {column: int(listings[column].isna().sum()) for column in columns}


def clean_documents(
    documents: list[dict[str, Any]], source_path: str | Path
) -> CleanResult:
    """Create the listing and review-event tables with documented exclusion rules."""
    source_name = Path(source_path).name
    listing_rows: list[dict[str, Any]] = []
    review_rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    duplicate_ids: list[str] = []
    missing_id_rows: list[int] = []
    invalid_review_dates = 0

    for source_row, document in enumerate(documents):
        listing = extract_listing(document, source_name, source_row)
        listing_id = listing["listing_id"]
        if not listing_id:
            missing_id_rows.append(source_row)
            continue
        if listing_id in seen_ids:
            duplicate_ids.append(listing_id)
            continue
        seen_ids.add(listing_id)
        listing_rows.append(listing)
        extracted_reviews, invalid_dates = _review_rows(document, listing)
        review_rows.extend(extracted_reviews)
        invalid_review_dates += invalid_dates

    listings = pd.DataFrame(listing_rows)
    reviews = pd.DataFrame(review_rows)
    if listings.empty:
        raise ValueError("No valid listing rows were produced from the source.")

    date_columns = [
        "first_review",
        "last_review",
        "last_scraped",
        "calendar_last_scraped",
    ]
    for column in date_columns:
        listings[column] = pd.to_datetime(listings[column], errors="coerce")
    listings = flag_price_outliers(listings)
    listings = listings.sort_values("source_row", kind="stable").reset_index(drop=True)
    if not reviews.empty:
        reviews = reviews.sort_values(
            ["review_date", "listing_id", "review_id"], kind="stable"
        ).reset_index(drop=True)

    expected_fields = {
        "address.location.coordinates": sum(
            get_nested(item, "address.location.coordinates") is not None
            for item in documents
        ),
        "address.market": sum(
            get_nested(item, "address.market") is not None for item in documents
        ),
        "address.government_area": sum(
            get_nested(item, "address.government_area") is not None
            for item in documents
        ),
        "host": sum(isinstance(item.get("host"), dict) for item in documents),
        "availability": sum(
            isinstance(item.get("availability"), dict) for item in documents
        ),
        "review_scores.review_scores_rating": sum(
            get_nested(item, "review_scores.review_scores_rating") is not None
            for item in documents
        ),
        "reviews": sum(isinstance(item.get("reviews"), list) for item in documents),
    }
    currency_fields = sorted(
        {
            key
            for item in documents
            for key in item
            if "currenc" in key.lower() and item.get(key) is not None
        }
    )
    quality: dict[str, Any] = {
        "source_file": source_name,
        "source_document_count": len(documents),
        "clean_listing_count": len(listings),
        "excluded_missing_id_count": len(missing_id_rows),
        "excluded_missing_id_rows": missing_id_rows,
        "duplicate_listing_count": len(duplicate_ids),
        "duplicate_listing_ids": sorted(set(duplicate_ids)),
        "review_event_count": len(reviews),
        "invalid_review_date_count": invalid_review_dates,
        "valid_coordinate_count": int(listings["coordinate_valid"].sum()),
        "invalid_coordinate_count": int((~listings["coordinate_valid"]).sum()),
        "coordinate_order": "GeoJSON [longitude, latitude]",
        "coordinate_bounds_rule": "longitude [-180, 180]; latitude [-90, 90]",
        "price_missing_count": int(listings["price_missing"].sum()),
        "price_non_positive_count": int(listings["price_non_positive"].sum()),
        "price_extreme_count": int(listings["price_extreme"].sum()),
        "price_outlier_rule": "Within each market: positive price outside Q1-3*IQR or Q3+3*IQR",
        "currency_fields_found": currency_fields,
        "currency_verified": False,
        "price_unit": "source price units",
        "price_comparison_rule": "Compare prices only within one market; no global rankings or guessed conversions.",
        "availability_interpretation": "Forward-looking availability snapshots; not reservations, occupancy, demand, or revenue.",
        "review_interpretation": "Review dates are an incomplete and biased review-activity proxy, not stays or demand.",
        "expected_nested_field_presence": expected_fields,
        "countries": int(listings["country"].nunique(dropna=True)),
        "markets": int(listings["market"].replace("", np.nan).nunique(dropna=True)),
        "missingness_counts": _missingness(
            listings,
            [
                "market",
                "government_area",
                "bedrooms",
                "bathrooms",
                "cleaning_fee",
                "security_deposit",
                "review_score_rating",
                "price",
                "longitude",
                "latitude",
            ],
        ),
        "availability_invalid_count": int((~listings["availability_valid"]).sum()),
        "schema_discrepancies_from_brief": [
            "Location is address.location, not a top-level location field.",
            "Host attributes are nested under host.",
            "Availability contains 30/60/90/365-day snapshot counts, not start/end dates.",
            "Overall rating is review_scores.review_scores_rating.",
            "Reviews contain dates but no review-level rating field in the supplied data.",
            "No currency field is supplied for prices or fees.",
        ],
    }
    return CleanResult(listings=listings, reviews=reviews, quality=quality)
