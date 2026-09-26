from __future__ import annotations

import pandas as pd

from airbnb_analysis.transform import (
    clean_documents,
    extract_listing,
    flag_price_outliers,
    get_nested,
    parse_number,
    validate_coordinates,
)


def source_document(
    listing_id: str = "1", price: float | None = 100.0
) -> dict:
    return {
        "_id": listing_id,
        "name": "Test listing",
        "price": price,
        "bedrooms": None,
        "bathrooms": None,
        "address": {
            "country": "Testland",
            "country_code": "TL",
            "market": "Test Market",
            "government_area": "Central",
            "location": {
                "type": "Point",
                "coordinates": [77.5946, 12.9716],
                "is_location_exact": False,
            },
        },
        "host": {"host_id": "h1", "host_name": "Host"},
        "availability": {
            "availability_30": 5,
            "availability_60": 10,
            "availability_90": 20,
            "availability_365": 100,
        },
        "review_scores": {"review_scores_rating": 93},
        "reviews": [
            {"_id": f"r-{listing_id}", "date": "2020-01-02 00:00:00"}
        ],
        "amenities": ["Wifi", "Kitchen"],
    }


def test_get_nested_and_extended_json_numbers() -> None:
    document = {"a": {"b": {"$numberDecimal": "12.50"}}}
    assert get_nested(document, "a.b") == {"$numberDecimal": "12.50"}
    assert parse_number(get_nested(document, "a.b")) == 12.5
    assert get_nested(document, "a.missing") is None


def test_coordinate_order_and_bounds() -> None:
    longitude, latitude, valid, issue = validate_coordinates([151.2, -33.8])
    assert (longitude, latitude, valid, issue) == (151.2, -33.8, True, "")
    assert validate_coordinates([181, 20])[2:] == (
        False,
        "longitude_out_of_bounds",
    )
    assert validate_coordinates([20, -91])[2:] == (
        False,
        "latitude_out_of_bounds",
    )
    assert validate_coordinates(None)[2:] == (False, "missing_or_malformed")


def test_nested_listing_extraction_preserves_missing_values() -> None:
    row = extract_listing(source_document(), "fixture.json", 7)
    assert row["listing_id"] == "1"
    assert row["market"] == "Test Market"
    assert row["longitude"] == 77.5946
    assert row["latitude"] == 12.9716
    assert row["review_score_rating"] == 93
    assert row["bedrooms"] is None
    assert row["bathrooms"] is None
    assert row["source_row"] == 7
    assert row["currency_verified"] is False
    assert row["price_unit"] == "source price units"


def test_duplicate_and_missing_id_rules_keep_first() -> None:
    first = source_document("same", 10)
    duplicate = source_document("same", 999)
    missing_id = source_document("", 25)
    result = clean_documents([first, duplicate, missing_id], "fixture.json")
    assert len(result.listings) == 1
    assert result.listings.iloc[0]["price"] == 10
    assert result.quality["duplicate_listing_count"] == 1
    assert result.quality["excluded_missing_id_count"] == 1
    assert len(result.reviews) == 1


def test_price_outliers_are_flagged_not_removed() -> None:
    frame = pd.DataFrame(
        {
            "market": ["A"] * 5,
            "price": [10.0, 11.0, 12.0, 13.0, 100.0],
        }
    )
    flagged = flag_price_outliers(frame)
    assert len(flagged) == 5
    assert flagged["price_extreme"].tolist() == [False, False, False, False, True]


def test_availability_is_snapshot_not_occupancy() -> None:
    result = clean_documents([source_document()], "fixture.json")
    columns = set(result.listings.columns)
    prohibited = {"occupancy", "occupancy_rate", "bookings", "demand", "revenue"}
    assert columns.isdisjoint(prohibited)
    assert result.listings.iloc[0]["availability_365"] == 100
    assert "not reservations" in result.quality["availability_interpretation"]


def test_invalid_availability_is_flagged() -> None:
    document = source_document()
    document["availability"]["availability_30"] = 31
    row = extract_listing(document, "fixture.json", 0)
    assert row["availability_valid"] is False

