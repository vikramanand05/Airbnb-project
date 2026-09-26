# Demo video script

Target length: four to five minutes. This is a recording script; no video has been recorded or posted.

## 0:00-0:30 - Project and safeguards

“This project turns the supplied Airbnb JSON into a reproducible analytical model, an optional MongoDB Atlas source, a Streamlit application, and Power BI or Tableau-ready exports. The source covers multiple countries but has no currency field, so every monetary value is labeled source price units and price comparisons stay within one market. Availability is presented only as a snapshot, never as occupancy.”

## 0:30-1:10 - Reproducible pipeline

Show the repository tree and terminal.

“The `all` command validates and cleans the nested JSON, preserves source IDs and provenance, writes CSV and Parquet tables, and generates the EDA report. MongoDB ingestion uses environment variables, batched idempotent upserts, retries, and indexes. Credentials are never stored in the repository.”

Run:

```text
airbnb-analysis all --json data/raw/sample_airbnb.json
```

## 1:10-2:30 - Streamlit overview, filters, and map

Open Overview, change Market and Room Type filters, and point out the filtered sample count and freshness notice. Open Map. Show that the global map colors points by room type, then select one market and show price coloring in source units.

## 2:30-3:20 - Price and location insights

Open Prices with one market selected. Explain the median, interquartile range, retained outliers, distribution, and neighborhood sample sizes. Emphasize that no market-to-market price ranking is presented.

## 3:20-3:55 - Availability and reviews

Open Availability and switch horizons. Read the snapshot warning. Open Reviews and read the review-activity proxy warning. Explain why these visuals do not establish bookings, occupancy, demand, revenue, or seasonality.

## 3:55-4:30 - Data quality and BI handoff

Open Data Quality and show missingness, coordinate validation, and anomaly flags. Show the exported tables and BI guide. Explain the one-to-many listings-to-reviews model and the guarded single-market price measure.

## 4:30-4:50 - Verification

Show the passing test and lint commands. Close with the local run command and note that Atlas is optional.

