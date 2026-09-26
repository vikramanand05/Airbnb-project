# LinkedIn post draft

I built an end-to-end Airbnb analysis capstone from a nested JSON dataset.

The project includes:

- A deterministic Python cleaning and validation pipeline
- Optional MongoDB Atlas ingestion with idempotent upserts and geospatial indexes
- A Streamlit application with overview, map, price, availability, review-activity, and data-quality views
- CSV and Parquet exports plus a documented Power BI/Tableau model
- Automated tests for nested extraction, coordinates, duplicates, missing data, price outliers, availability interpretation, and analytical parity

Two data limitations shaped the design. The source has no currency field, so prices are labeled “source price units” and compared only within a selected market. Availability is a forward-looking snapshot, so I did not present it as occupancy, bookings, demand, or revenue. Historical review counts are labeled as a review-activity proxy rather than true seasonality.

The result is reproducible locally without database credentials, while still supporting MongoDB Atlas when configured.

#Python #Streamlit #MongoDB #DataAnalytics #PowerBI #Tableau #Geospatial #DataQuality

This is a draft only. It has not been posted.
