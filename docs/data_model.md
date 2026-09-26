# Analytical data model

The cleaning pipeline creates a small star-style model for Streamlit, Power BI, and Tableau.

```text
listings (one row per listing)
    listing_id  1 ─────────── *  listing_id
                              review_events (one row per dated review)
```

## `listings`

Grain: one row per retained source listing ID. The full field dictionary is exported to `data/processed/data_dictionary.csv`.

Key dimensions:

- `listing_id`: primary key.
- `country`, `country_code`, `market`, `government_area`, `suburb`: geographic filters.
- `property_type`, `room_type`, `bed_type`: listing classifications.
- `host_id`, `host_is_superhost`, `host_identity_verified`: selected host fields.
- `longitude`, `latitude`, `coordinate_valid`: GeoJSON point fields.

Key measures and flags:

- `price`, `cleaning_fee`, `security_deposit`, `extra_people`: monetary source values. The source has no currency field, so these are **source price units**.
- `price_missing`, `price_non_positive`, `price_extreme`: quality flags; flagged rows are retained.
- `review_score_rating`: overall source rating on a 0-100 scale.
- `availability_30`, `availability_60`, `availability_90`, `availability_365`: forward-looking available-day snapshots.
- `availability_valid`: every supplied horizon is within its possible range.

Provenance:

- `source_file`: input file name.
- `source_row`: zero-based source-array position.
- `last_scraped`, `calendar_last_scraped`: source freshness dates.

## `review_events`

Grain: one row per source review with a usable date.

- `review_id`: source review ID.
- `listing_id`: foreign key to `listings`.
- `review_date`, `review_year_month`: event date and month.
- `market`, `government_area`, `country`: denormalized attributes for simple BI filtering.
- `source_listing_row`: source-listing provenance.

Review text and reviewer names are intentionally omitted from the analytical export. The dashboard needs only event dates, and omitting free text reduces unnecessary personal data handling.

## Relationship and filter direction

Create a one-to-many relationship from `listings[listing_id]` to `review_events[listing_id]`. Use single-direction filtering from listings to review events. Do not create a relationship on denormalized geographic columns.

## Interpretation constraints

1. Price comparisons require exactly one market in filter context. Never rank markets or countries by unconverted values.
2. Availability counts are snapshots, not reservations or occupancy. Do not derive `1 - availability_365 / 365` as occupancy.
3. Review counts are a **review-activity proxy**. They are not bookings, stays, demand, revenue, or true seasonality.
4. Missing ratings, fees, bedrooms, bathrooms, and coordinates remain null.
5. Outliers remain in the tables and are exposed through flags.

