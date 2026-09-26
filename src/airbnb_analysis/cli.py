"""Command-line interface for cleaning, EDA, and Atlas ingestion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from airbnb_analysis.config import Settings
from airbnb_analysis.eda import generate_eda
from airbnb_analysis.mongo import get_collection, ingest_json
from airbnb_analysis.pipeline import run_cleaning


def _settings_defaults() -> Settings:
    return Settings.from_env()


def build_parser() -> argparse.ArgumentParser:
    settings = _settings_defaults()
    parser = argparse.ArgumentParser(
        prog="airbnb-analysis",
        description="Clean, analyze, export, and ingest the Airbnb capstone dataset.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    clean = subparsers.add_parser("clean", help="Create cleaned CSV and Parquet tables")
    clean.add_argument("--json", type=Path, default=settings.json_path)
    clean.add_argument("--output", type=Path, default=settings.processed_dir)

    eda = subparsers.add_parser("eda", help="Generate EDA summaries and report")
    eda.add_argument("--processed", type=Path, default=settings.processed_dir)
    eda.add_argument("--report", type=Path, default=Path("reports/eda_report.md"))

    all_steps = subparsers.add_parser("all", help="Run cleaning then EDA")
    all_steps.add_argument("--json", type=Path, default=settings.json_path)
    all_steps.add_argument("--output", type=Path, default=settings.processed_dir)
    all_steps.add_argument("--report", type=Path, default=Path("reports/eda_report.md"))

    ingest = subparsers.add_parser("ingest", help="Idempotently upsert JSON into MongoDB Atlas")
    ingest.add_argument("--json", type=Path, default=settings.json_path)
    ingest.add_argument("--batch-size", type=int, default=500)
    ingest.add_argument("--database", default=settings.mongodb_database)
    ingest.add_argument("--collection", default=settings.mongodb_collection)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = Settings.from_env()

    if args.command == "clean":
        result = run_cleaning(args.json, args.output)
        print(json.dumps(result.quality, indent=2, default=str))
        return 0
    if args.command == "eda":
        summary = generate_eda(args.processed, args.report)
        print(json.dumps(summary, indent=2, default=str))
        return 0
    if args.command == "all":
        result = run_cleaning(args.json, args.output)
        summary = generate_eda(args.output, args.report)
        print(json.dumps({"quality": result.quality, "eda": summary}, indent=2, default=str))
        return 0
    if args.command == "ingest":
        if not settings.mongodb_uri:
            parser.error("MONGODB_URI is required for Atlas ingestion. Copy .env.example to .env.")
        collection = get_collection(settings.mongodb_uri, args.database, args.collection)
        result = ingest_json(args.json, collection, args.batch_size)
        print(json.dumps(result, indent=2))
        return 0
    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
