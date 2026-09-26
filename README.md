# Airbnb analysis capstone

A complete, reproducible analysis project for the supplied Airbnb listings-and-reviews JSON. It provides optional MongoDB Atlas ingestion, deterministic cleaning, exploratory analysis, an interactive Streamlit application, and Power BI/Tableau-ready exports.

The project follows two non-negotiable interpretation rules:

1. The source has no currency field. Monetary values are labeled **source price units**, price comparisons stay inside one market, and the project does not rank countries or markets by guessed conversions.
2. Availability values are forward-looking snapshots. They are not reservations or realized occupancy, and the project does not infer bookings, demand, revenue, or seasonality from them. Review dates support a clearly labeled **review-activity proxy** only.

## What is included

- Repeatable JSON-to-MongoDB Atlas ingestion with environment-based credentials, batching, retries, idempotent `_id` upserts, and useful indexes.
- A local JSON fallback that produces the same cleaned analytical model without Atlas credentials.
- Deterministic flattening of analysis-relevant nested fields with source IDs and row provenance.
- Coordinate, availability, missing-value, duplicate, and price-anomaly checks.
- CSV and Parquet listing and review-event tables, a data dictionary, and compact BI summary tables.
- A six-section Streamlit application: Overview, Map, Prices, Availability, Reviews, and Data Quality.
- Reproducible EDA with computed tables and a generated Markdown report.
- A Power BI/Tableau model, measures, page designs, safeguards, and build checklist.
- Automated unit, parity, dataset-integration, and Streamlit smoke tests.
- A demo-video script and LinkedIn post draft. Neither is claimed as recorded or posted.

## Repository layout

```text
.
├── app.py
├── data/
│   ├── raw/                     # local source JSON; ignored by Git
│   └── processed/               # generated CSV, Parquet, JSON summaries
├── docs/
│   ├── bi_dashboard_guide.md
│   ├── data_model.md
│   ├── demo_video_script.md
│   └── linkedin_post_draft.md
├── reports/
│   └── eda_report.md            # generated from the real dataset
├── src/airbnb_analysis/
│   ├── charts.py
│   ├── cli.py
│   ├── config.py
│   ├── eda.py
│   ├── io.py
│   ├── mongo.py
│   ├── pipeline.py
│   ├── queries.py
│   ├── schema.py
│   └── transform.py
├── tests/
├── .env.example
├── .gitignore
└── pyproject.toml
```

## Prerequisites

- Python 3.11, 3.12, or 3.13 is recommended.
- Approximately 1 GB of free disk space for the environment and generated exports.
- The supplied `sample_airbnb.json` file.
- MongoDB Atlas is optional. Local cleaning, EDA, Streamlit, and BI exports do not require credentials.

## Setup

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
New-Item -ItemType Directory -Force data\raw | Out-Null
Copy-Item "C:\path\to\sample_airbnb.json" data\raw\sample_airbnb.json
```

If script execution is restricted, run `Set-ExecutionPolicy -Scope Process Bypass` in that PowerShell session before activation.

### macOS or Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
mkdir -p data/raw
cp /path/to/sample_airbnb.json data/raw/sample_airbnb.json
```

## Run the complete local workflow

```text
airbnb-analysis all --json data/raw/sample_airbnb.json
```

This command:

1. Loads and validates the top-level JSON array.
2. Keeps the first record for each listing ID and excludes only rows with no listing ID.
3. Flattens analysis-relevant nested fields.
4. Parses numeric values and dates without inventing missing data.
5. Validates GeoJSON coordinate order and bounds.
6. Flags missing, non-positive, and market-specific extreme prices without deleting them.
7. Creates listing and dated review-event tables.
8. Writes CSV and Parquet exports, quality metadata, summary tables, and the EDA report.

Run the steps separately when needed:

```text
airbnb-analysis clean --json data/raw/sample_airbnb.json --output data/processed
airbnb-analysis eda --processed data/processed --report reports/eda_report.md
```

## Run Streamlit

```text
streamlit run app.py
```

The app uses `data/processed` by default. Run the cleaning command first. The sidebar offers:

- Data source: local cleaned files, plus MongoDB Atlas when `MONGODB_URI` exists.
- Market.
- Neighborhood/government area.
- Room type and property type.
- Rating range.
- Price range only when one market is selected.
- Availability horizon on the Availability page.

The map displays at most a deterministic sample of 1,500 points for responsive interaction. With multiple markets selected, it colors by room type rather than price. With one market selected, it may color by source price units.

## MongoDB Atlas configuration

Atlas is optional. To enable it:

1. Create a MongoDB Atlas project and cluster.
2. Create a database user with read/write permission for the target database.
3. Add your current IP address to Atlas Network Access.
4. Copy `.env.example` to `.env`.
5. Replace only the placeholders in `MONGODB_URI`. Never commit `.env`.

Example `.env` keys:

```text
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster-host>/?retryWrites=true&w=majority
MONGODB_DATABASE=sample_airbnb
MONGODB_COLLECTION=listingsAndReviews
AIRBNB_JSON_PATH=data/raw/sample_airbnb.json
AIRBNB_PROCESSED_DIR=data/processed
```

Ingest the source:

```text
airbnb-analysis ingest --json data/raw/sample_airbnb.json --batch-size 500
```

The command uses unordered `UpdateOne(..., upsert=True)` operations keyed by listing `_id`, retries transient PyMongo errors up to three times with exponential backoff, and creates indexes for:

- `address.location` as `2dsphere`.
- `address.market` plus `address.government_area`.
- `room_type` plus `property_type`.
- `price`.
- `review_scores.review_scores_rating`.
- `last_scraped`.

Rerunning ingestion is safe: existing listing IDs are updated and new IDs are inserted. The application and query module use the same analytical schema for Atlas and local data. MongoDB handles the initial market filtering and neighborhood grouping; Python completes medians and quartiles from grouped price arrays so the output remains compatible with Atlas versions that do not expose a median accumulator.

## Cleaning and validation rules

### Nested fields

The real JSON schema takes precedence over the example in the project brief. Important paths are:

- `address.location.coordinates` in GeoJSON `[longitude, latitude]` order.
- `address.market` and `address.government_area`.
- `host.*`.
- `availability.availability_30`, `_60`, `_90`, and `_365`.
- `review_scores.review_scores_rating`.
- `reviews[].date`.

### Missing values

- Missing ratings, fees, bedrooms, bathrooms, beds, and coordinates stay null.
- Zero is retained only when it is actually present in the source.
- Missing ratings are excluded from rating medians; they are not treated as zero.

### Duplicates and exclusions

- A listing ID is the primary key.
- If duplicates occur, the first source occurrence is retained deterministically and later duplicates are excluded.
- A source row without a listing ID is excluded because it cannot support safe upserts or model relationships.
- Review events are emitted only for retained listings and usable review dates.

### Prices

- Missing, zero, and negative prices are flagged.
- Positive extreme prices are flagged within each market using outer Tukey fences: below `Q1 - 3 × IQR` or above `Q3 + 3 × IQR`.
- No price row is deleted because of an anomaly flag.
- There is no currency field, so monetary values are **source price units**.
- Cross-market and cross-country price rankings are prohibited.

### Coordinates

- The first element is longitude and must be between -180 and 180.
- The second is latitude and must be between -90 and 90.
- Invalid or malformed points remain in the listing table but are excluded from maps.

### Availability and review activity

- Availability is a snapshot of available days in fixed forward horizons.
- The project never calculates or labels `1 - availability_365 / 365` as occupancy.
- Review dates are charted only as a **review-activity proxy**.
- Reviews are incomplete and biased, so their counts cannot establish stays, demand, revenue, or true seasonality.

## Generated outputs

After `airbnb-analysis all`, `data/processed` contains:

- `listings.csv` and `listings.parquet`: one row per retained listing.
- `review_events.csv` and `review_events.parquet`: one row per usable dated review.
- `data_dictionary.csv`: table, column, type, and description.
- `data_quality.json`: source counts, checksum, schema verification, exclusions, and quality flags.
- `eda_summary.json`: compact computed facts.
- `market_summary.csv`: alphabetical, independent within-market distributions; not a global ranking.
- `country_coverage.csv`: listing counts by country.
- `missingness.csv`: missing counts and percentages.
- `availability_summary.csv`: snapshot distributions by horizon.

The generated `reports/eda_report.md` covers dataset scope, missingness, geography, property and room types, market-contained price distributions, ratings, amenities, availability snapshots, review activity, and schema discrepancies.

## Power BI or Tableau

See [docs/data_model.md](docs/data_model.md) for the relationship model and [docs/bi_dashboard_guide.md](docs/bi_dashboard_guide.md) for imports, DAX and Tableau calculations, page layouts, filter behavior, labels, and a validation checklist.

The Python environment cannot produce a native Power BI `.pbix` or Tableau `.twb` file. The repository therefore does not claim one exists. It provides typed Parquet and portable CSV tables plus the exact build instructions needed in either desktop application.

## Tests and linting

Run cleaning before the dataset and app integration tests:

```text
airbnb-analysis all --json data/raw/sample_airbnb.json
pytest
ruff check .
```

The suite covers:

- Nested-field extraction and extended-JSON numeric parsing.
- GeoJSON coordinate order and bounds.
- Duplicate and missing-ID behavior.
- Missing values without silent imputation.
- Market-specific price outlier flags.
- Availability interpretation and the absence of an occupancy calculation.
- Local and MongoDB-grouped analytical parity.
- Supplied-dataset counts and schema facts.
- Rendering of every main Streamlit view with the cleaned dataset.

## BI and application workflow

```text
source JSON
    ├── optional idempotent Atlas ingestion + indexes
    └── deterministic cleaning
            ├── listings table ───────┐
            ├── review-event table ───┼── Streamlit
            ├── quality metadata ─────┤
            ├── EDA report ───────────┤
            └── BI summary tables ────┴── Power BI / Tableau
```

## Short live-demo walkthrough

1. Run the complete local pipeline and point out the verified counts printed by the CLI.
2. Start Streamlit and show the data-freshness label.
3. On Overview, filter to one market and room type.
4. On Map, explain GeoJSON coordinate order and the marker cap.
5. On Prices, show the median, quartiles, neighborhood sample sizes, and retained extremes.
6. On Availability, change the horizon and read the snapshot warning.
7. On Reviews, show the review-activity proxy warning.
8. On Data Quality, show missingness and the deterministic rules.
9. Open the BI guide and explain the single-market price guard.
10. Run `pytest` and `ruff check .`.

The longer recording script is in [docs/demo_video_script.md](docs/demo_video_script.md). A draft post is in [docs/linkedin_post_draft.md](docs/linkedin_post_draft.md). No video has been recorded and no post has been published.

## Limitations

- No currency field or exchange-rate date exists. Currency conversions would be invented, so they are not attempted.
- Availability snapshots do not reveal whether unavailable days were booked, blocked, or otherwise unavailable.
- Review events omit unreviewed stays and may be delayed, selective, or removed.
- The data is a historical snapshot. The application labels the source scrape date and does not imply current availability or price.
- Neighborhood names follow the source and may not be standardized across markets.
- MongoDB Atlas ingestion requires user-supplied credentials and network access.
- A native `.pbix` or `.twb` requires the corresponding desktop software and is not fabricated by this repository.

## Security and publishing

- `.env` and Streamlit secrets are ignored by Git.
- `.env.example` contains placeholders only.
- The raw JSON is ignored to avoid accidentally committing a large source file.
- The project does not publish to GitHub, LinkedIn, or any external service.
- Before creating a public repository, review the source-data license and decide whether the raw dataset may be redistributed.
