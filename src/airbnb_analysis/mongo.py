"""MongoDB Atlas connectivity and idempotent source ingestion."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

from pymongo import ASCENDING, GEOSPHERE, MongoClient, UpdateOne
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from airbnb_analysis.io import load_json_documents


def get_collection(uri: str, database: str, collection: str) -> Collection:
    """Connect to Atlas and fail quickly with a useful error."""
    try:
        client = MongoClient(
            uri,
            appname="airbnb-analysis-capstone",
            serverSelectionTimeoutMS=10_000,
            connectTimeoutMS=10_000,
            retryWrites=True,
        )
        client.admin.command("ping")
        return client[database][collection]
    except PyMongoError as exc:
        raise ConnectionError(
            "MongoDB connection failed. Check MONGODB_URI, Atlas network access, "
            "database-user permissions, and DNS connectivity."
        ) from exc


def batched(items: list[dict[str, Any]], size: int) -> Iterator[list[dict[str, Any]]]:
    """Yield deterministic ingestion batches."""
    for start in range(0, len(items), size):
        yield items[start : start + size]


@retry(
    retry=retry_if_exception_type(PyMongoError),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    stop=stop_after_attempt(3),
    reraise=True,
)
def _upsert_batch(collection: Collection, batch: list[dict[str, Any]]) -> int:
    operations = [
        UpdateOne(
            {"_id": document["_id"]},
            {"$set": {key: value for key, value in document.items() if key != "_id"}},
            upsert=True,
        )
        for document in batch
    ]
    result = collection.bulk_write(operations, ordered=False)
    return result.upserted_count + result.modified_count + result.matched_count


def ensure_indexes(collection: Collection) -> list[str]:
    """Create indexes used by the app's filters and geospatial queries."""
    return [
        collection.create_index(
            [("address.location", GEOSPHERE)], name="location_2dsphere"
        ),
        collection.create_index(
            [("address.market", ASCENDING), ("address.government_area", ASCENDING)],
            name="market_area",
        ),
        collection.create_index(
            [("room_type", ASCENDING), ("property_type", ASCENDING)],
            name="room_property",
        ),
        collection.create_index([("price", ASCENDING)], name="price"),
        collection.create_index(
            [("review_scores.review_scores_rating", ASCENDING)], name="rating"
        ),
        collection.create_index([("last_scraped", ASCENDING)], name="last_scraped"),
    ]


def ingest_json(
    source_path: str | Path,
    collection: Collection,
    batch_size: int = 500,
) -> dict[str, int]:
    """Idempotently upsert the supplied JSON documents by listing `_id`."""
    documents = load_json_documents(source_path)
    if any("_id" not in document for document in documents):
        raise ValueError("Every source document must contain `_id` for safe upserts.")
    processed = 0
    for batch in batched(documents, batch_size):
        _upsert_batch(collection, batch)
        processed += len(batch)
    ensure_indexes(collection)
    return {"source_documents": len(documents), "processed_documents": processed}


def fetch_documents(collection: Collection) -> list[dict[str, Any]]:
    """Retrieve raw documents for the same local cleaning model."""
    return list(collection.find({}))
