# Airbnb exploratory data analysis

Generated from `sample_airbnb.json` using the deterministic cleaning pipeline.

## Scope and coverage

- Clean listings: **5,555** from **5,555** source documents.
- Dated review events: **149,792** spanning **2009-10-27** to **2019-03-11**.
- Geography: **9 countries** and **14 named markets**.
- Valid GeoJSON coordinate pairs: **5,555**. Coordinates are interpreted as `[longitude, latitude]`.
- Latest source scrape date: **2019-03-11**.

### Country coverage

| Country | Listing Count |
| --- | --- |
| United States | 1,222 |
| Turkey | 661 |
| Canada | 649 |
| Spain | 633 |
| Australia | 610 |
| Brazil | 606 |
| Hong Kong | 600 |
| Portugal | 555 |
| China | 19 |

### Largest markets by listing count

| Market | Listing Count |
| --- | --- |
| Istanbul | 660 |
| Montreal | 648 |
| Barcelona | 632 |
| Hong Kong | 619 |
| Sydney | 609 |
| New York | 607 |
| Rio De Janeiro | 603 |
| Porto | 554 |
| Oahu | 253 |
| Maui | 153 |
| The Big Island | 139 |
| Kauai | 67 |
| Unknown | 6 |
| Other (International) | 4 |
| Other (Domestic) | 1 |

## Missingness and data quality

Missing numeric values remain null. They are not imputed with zero or a median.

| Field | Missing Count | Missing Percent |
| --- | --- | --- |
| security_deposit | 2,084 | 37.5 |
| cleaning_fee | 1,531 | 27.6 |
| review_score_rating | 1,474 | 26.5 |
| bathrooms | 10 | 0.2 |
| bedrooms | 5 | 0.1 |
| government_area | 0 | 0.0 |
| latitude | 0 | 0.0 |
| longitude | 0 | 0.0 |
| price | 0 | 0.0 |

- Duplicate listing IDs excluded: **0**. The deterministic rule keeps the first source occurrence.
- Listings with missing IDs excluded: **0**.
- Missing prices: **0**; zero or negative prices: **0**.
- Extreme positive prices retained and flagged: **215**, using each market's 3-IQR outer fences.
- Invalid availability snapshots: **0**.

## Property and room mix

### Room types

| Room Type | Listing Count |
| --- | --- |
| Entire home/apt | 3,489 |
| Private room | 1,983 |
| Shared room | 83 |

### Most common property types

| Property Type | Listing Count |
| --- | --- |
| Apartment | 3,626 |
| House | 606 |
| Condominium | 399 |
| Serviced apartment | 185 |
| Loft | 142 |
| Townhouse | 108 |
| Guest suite | 81 |
| Bed and breakfast | 69 |
| Boutique hotel | 53 |
| Guesthouse | 50 |
| Hostel | 34 |
| Villa | 32 |
| Hotel | 26 |
| Aparthotel | 23 |
| Cottage | 20 |

## Prices

The source contains **no currency field**. All monetary figures are labeled **source price units**. Each row below is an independent description inside one market, sorted alphabetically. Do not compare or rank markets, countries, or the global dataset by these values, and do not convert currencies by guessing.

| Market | Listing Count | Median Price | Price Q1 | Price Q3 | Extreme Price Count |
| --- | --- | --- | --- | --- | --- |
| Barcelona | 632 | 60.0 | 35.0 | 100.0 | 32 |
| Hong Kong | 619 | 550.0 | 353.0 | 848.0 | 17 |
| Istanbul | 660 | 179.0 | 105.0 | 301.0 | 27 |
| Kauai | 67 | 239.0 | 139.0 | 400.0 | 0 |
| Maui | 153 | 228.0 | 174.0 | 320.0 | 6 |
| Montreal | 648 | 75.0 | 48.0 | 110.0 | 21 |
| New York | 607 | 110.0 | 72.0 | 160.0 | 15 |
| Oahu | 253 | 142.0 | 97.0 | 265.0 | 7 |
| Other (Domestic) | 1 | 128.0 | 128.0 | 128.0 | 0 |
| Other (International) | 4 | 446.5 | 318.8 | 573.5 | 0 |
| Porto | 554 | 59.0 | 41.0 | 80.0 | 17 |
| Rio De Janeiro | 603 | 257.0 | 149.0 | 522.0 | 40 |
| Sydney | 609 | 132.0 | 80.0 | 218.0 | 27 |
| The Big Island | 139 | 120.0 | 84.0 | 177.0 | 6 |
| Unknown | 6 | 120.5 | 47.8 | 143.0 | 0 |

## Ratings

- Listings with an overall rating: **4,081** of **5,555**.
- Median source rating: **95.0 / 100**.
- Interquartile range: **90.0 to 99.0**.

Ratings are guest-submitted and subject to selection bias. Missing ratings are not scored as zero.

## Amenities

Amenity labels are counted exactly as supplied after whitespace trimming.

| Amenity | Listing Count |
| --- | --- |
| Wifi | 5,303 |
| Essentials | 5,048 |
| Kitchen | 4,951 |
| TV | 4,295 |
| Hangers | 4,226 |
| Hair dryer | 3,900 |
| Washer | 3,877 |
| Shampoo | 3,709 |
| Iron | 3,692 |
| Laptop friendly workspace | 3,442 |
| Air conditioning | 3,431 |
| Heating | 3,300 |
| Hot water | 2,973 |
| Smoke detector | 2,886 |
| Family/kid friendly | 2,487 |

## Availability snapshots

These values are forward-looking counts of available days at the source scrape date. They are **not reservations, realized occupancy, bookings, demand, or revenue**. The pipeline deliberately does not calculate `1 - availability_365 / 365` as occupancy.

| Horizon Days | Listing Count | Median Available Days | Q1 Available Days | Q3 Available Days |
| --- | --- | --- | --- | --- |
| 30 | 5,555 | 8.0 | 0.0 | 24.0 |
| 60 | 5,555 | 23.0 | 0.0 | 52.0 |
| 90 | 5,555 | 43.0 | 0.0 | 80.0 |
| 365 | 5,555 | 171.0 | 17.0 | 317.0 |

## Review activity proxy

The review-event table supports historical review counts by month from **2009-10-27** to **2019-03-11**. This is a **review-activity proxy** only. Reviews are an incomplete, delayed, and biased sample of stays, so the project does not present them as bookings, demand, occupancy, or true seasonality.

## Source-schema verification

The JSON, not the brief's example, is the source of truth. Verified differences:

- Location is nested at `address.location`, with GeoJSON coordinates in `[longitude, latitude]` order.
- Market and government area are under `address`.
- Host details are nested under `host`.
- Availability contains 30-, 60-, 90-, and 365-day snapshot counts rather than start/end dates.
- Overall rating is `review_scores.review_scores_rating`.
- All supplied reviews have a usable date, but no review-level rating field is present.
- No price currency field is present.
