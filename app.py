"""Streamlit entry point for the Airbnb capstone application."""

from __future__ import annotations

from html import escape

import numpy as np
import pandas as pd
import streamlit as st

from airbnb_analysis.charts import (
    availability_distribution,
    count_bar,
    listing_map,
    missingness_chart,
    neighborhood_price,
    price_histogram,
    review_activity,
)
from airbnb_analysis.config import Settings
from airbnb_analysis.io import read_processed_tables
from airbnb_analysis.mongo import fetch_documents, get_collection
from airbnb_analysis.queries import local_neighborhood_summary
from airbnb_analysis.transform import clean_documents

st.set_page_config(
    page_title="Airbnb Market Explorer",
    page_icon="A",
    layout="wide",
    initial_sidebar_state="expanded",
)

PLOTLY_CONFIG = {
    "displayModeBar": False,
    "displaylogo": False,
    "responsive": True,
    "scrollZoom": False,
}

st.markdown(
    """
    <style>
      :root {
        --ink: #102A43;
        --muted: #627386;
        --line: #E2E8F0;
        --surface: #FFFFFF;
        --canvas: #F5F7FA;
        --coral: #FF5A5F;
        --coral-soft: #FFF0F1;
        --teal: #00A699;
        --navy: #16324F;
        --gold: #E59F25;
      }

      html { scroll-behavior: smooth; }
      .stApp { background: var(--canvas); color: var(--ink); }
      .block-container {
        max-width: 1440px;
        padding-top: 4rem;
        padding-bottom: 3.5rem;
      }
      header[data-testid="stHeader"] { background: rgba(245,247,250,.86); }
      [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none; }
      #MainMenu, footer { visibility: hidden; }

      [data-testid="stSidebar"] {
        background: #FCFDFE;
        border-right: 1px solid var(--line);
        box-shadow: 8px 0 28px rgba(16,42,67,.035);
      }
      [data-testid="stSidebar"] > div:first-child { padding-top: 1.1rem; }
      [data-testid="stSidebar"] div[role="radiogroup"] { gap: .25rem; }
      [data-testid="stSidebar"] div[role="radiogroup"] label {
        border-radius: 10px;
        padding: .32rem .5rem;
        transition: background .15s ease, transform .15s ease;
      }
      [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: #F1F5F9;
        transform: translateX(2px);
      }
      [data-testid="stSidebar"] label:has(input:checked) {
        background: var(--coral-soft);
      }
      [data-baseweb="select"] > div,
      [data-testid="stMultiSelect"] > div > div {
        background: #FFFFFF;
        border-color: var(--line);
        border-radius: 10px;
        min-height: 2.75rem;
      }
      [data-baseweb="select"] > div:focus-within,
      [data-testid="stMultiSelect"] > div > div:focus-within {
        border-color: var(--coral);
        box-shadow: 0 0 0 3px rgba(255,90,95,.1);
      }

      .brand {
        display: flex;
        align-items: center;
        gap: .8rem;
        padding: .35rem 0 1.25rem;
      }
      .brand-mark {
        width: 42px;
        height: 42px;
        display: grid;
        place-items: center;
        border-radius: 13px;
        color: white;
        font-size: 1.15rem;
        font-weight: 800;
        letter-spacing: -.04em;
        background: linear-gradient(145deg, var(--coral), #E83E67);
        box-shadow: 0 8px 20px rgba(255,90,95,.25);
      }
      .brand-copy strong { display: block; color: var(--ink); font-size: 1rem; }
      .brand-copy span {
        display: block;
        color: #8795A5;
        font-size: .65rem;
        font-weight: 750;
        letter-spacing: .13em;
        margin-top: .1rem;
      }
      .sidebar-label {
        color: #8492A6;
        font-size: .67rem;
        font-weight: 800;
        letter-spacing: .13em;
        margin: 1rem 0 .5rem;
      }
      .sidebar-hint {
        color: #718096;
        font-size: .76rem;
        line-height: 1.45;
        padding: .1rem .15rem .5rem;
      }
      .selection-card {
        margin-top: 1rem;
        padding: .8rem .9rem;
        background: linear-gradient(145deg, #FFFFFF, #F8FAFC);
        border: 1px solid var(--line);
        border-radius: 12px;
      }
      .selection-card span {
        display: block;
        color: #8A98A8;
        font-size: .63rem;
        font-weight: 800;
        letter-spacing: .12em;
      }
      .selection-card strong { color: var(--ink); font-size: 1.1rem; }
      .selection-card small { color: #718096; }
      .status-line {
        display: flex;
        align-items: center;
        gap: .45rem;
        color: #718096;
        font-size: .72rem;
        margin: 1rem .1rem .2rem;
      }
      .status-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: var(--teal);
        box-shadow: 0 0 0 4px rgba(0,166,153,.12);
      }

      .hero {
        position: relative;
        overflow: hidden;
        min-height: 220px;
        padding: 2rem 2.2rem;
        border-radius: 24px;
        color: white;
        background:
          radial-gradient(circle at 78% 12%, rgba(73,220,207,.3), transparent 27%),
          radial-gradient(circle at 92% 84%, rgba(255,90,95,.25), transparent 27%),
          linear-gradient(118deg, #102A43 0%, #0C4A60 52%, #007F78 100%);
        box-shadow: 0 18px 44px rgba(16,42,67,.18);
        margin-bottom: 1.1rem;
      }
      .hero::after {
        content: "";
        position: absolute;
        inset: 0;
        opacity: .15;
        background-image: radial-gradient(rgba(255,255,255,.75) .8px, transparent .8px);
        background-size: 18px 18px;
        mask-image: linear-gradient(to left, black, transparent 65%);
        pointer-events: none;
      }
      .hero-inner {
        position: relative;
        z-index: 1;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 2rem;
      }
      .hero-eyebrow {
        color: #91F0E7;
        font-size: .69rem;
        font-weight: 800;
        letter-spacing: .15em;
        margin-bottom: .55rem;
      }
      .hero h1 {
        margin: 0;
        color: white;
        font-size: clamp(2.05rem, 4vw, 3rem);
        line-height: 1.02;
        letter-spacing: -.045em;
      }
      .hero h1 span { color: #9AF2EA; }
      .hero p {
        max-width: 650px;
        margin: .75rem 0 0;
        color: rgba(255,255,255,.82);
        font-size: .98rem;
        line-height: 1.55;
      }
      .hero-pills { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: 1rem; }
      .hero-pill {
        display: inline-flex;
        align-items: center;
        gap: .35rem;
        padding: .38rem .68rem;
        border: 1px solid rgba(255,255,255,.18);
        border-radius: 999px;
        background: rgba(255,255,255,.09);
        color: rgba(255,255,255,.92);
        font-size: .72rem;
        backdrop-filter: blur(8px);
      }
      .hero-orbit {
        flex: 0 0 150px;
        width: 150px;
        height: 150px;
        display: grid;
        place-content: center;
        text-align: center;
        border-radius: 50%;
        border: 1px solid rgba(255,255,255,.24);
        background: rgba(255,255,255,.09);
        box-shadow: inset 0 0 0 10px rgba(255,255,255,.035);
        backdrop-filter: blur(10px);
      }
      .hero-orbit span {
        color: #A8F5ED;
        font-size: .59rem;
        font-weight: 800;
        letter-spacing: .11em;
      }
      .hero-orbit strong { color: white; font-size: 2rem; line-height: 1.15; }
      .hero-orbit small { color: rgba(255,255,255,.68); font-size: .65rem; }

      .page-heading {
        display: flex;
        justify-content: space-between;
        align-items: end;
        gap: 1rem;
        padding: .65rem .1rem .9rem;
      }
      .page-heading .eyebrow {
        color: var(--coral);
        font-size: .65rem;
        font-weight: 800;
        letter-spacing: .13em;
        margin-bottom: .22rem;
      }
      .page-heading h2 {
        margin: 0;
        color: var(--ink);
        font-size: 1.55rem;
        letter-spacing: -.025em;
      }
      .page-heading p {
        margin: .3rem 0 0;
        color: var(--muted);
        font-size: .88rem;
      }
      .sample-chip {
        flex: 0 0 auto;
        padding: .42rem .72rem;
        color: #35546F;
        background: #EAF2F7;
        border-radius: 999px;
        font-size: .73rem;
        font-weight: 700;
      }
      .section-kicker {
        color: #8291A3;
        font-size: .65rem;
        font-weight: 800;
        letter-spacing: .13em;
        margin: 1rem .1rem .15rem;
      }
      .section-title {
        color: var(--ink);
        font-size: 1.08rem;
        font-weight: 730;
        margin: 0 .1rem .15rem;
      }
      .section-copy {
        color: var(--muted);
        font-size: .8rem;
        margin: 0 .1rem .65rem;
      }

      div[data-testid="stMetric"] {
        min-height: 112px;
        padding: 1rem 1.05rem;
        border: 1px solid var(--line);
        border-top: 3px solid rgba(0,166,153,.7);
        border-radius: 16px;
        background: linear-gradient(145deg, #FFFFFF, #FBFCFE);
        box-shadow: 0 8px 24px rgba(16,42,67,.055);
        transition: transform .16s ease, box-shadow .16s ease;
      }
      div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 28px rgba(16,42,67,.09);
      }
      div[data-testid="stMetricLabel"] { color: #6A7C8E; }
      div[data-testid="stMetricValue"] { color: var(--ink); letter-spacing: -.035em; }

      [data-testid="stPlotlyChart"] {
        overflow: hidden;
        border: 1px solid var(--line);
        border-radius: 18px;
        background: var(--surface);
        box-shadow: 0 10px 28px rgba(16,42,67,.055);
        padding: .2rem;
      }
      [data-testid="stAlert"] { border-radius: 13px; border-width: 1px; }
      [data-testid="stExpander"] {
        border-color: var(--line);
        border-radius: 14px;
        background: #FFFFFF;
      }
      div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: var(--line);
        border-radius: 16px;
        background: #FFFFFF;
        box-shadow: 0 8px 22px rgba(16,42,67,.045);
      }
      hr { border-color: var(--line); }

      .callout {
        display: flex;
        gap: .8rem;
        align-items: flex-start;
        margin: .3rem 0 1rem;
        padding: .85rem 1rem;
        border: 1px solid;
        border-radius: 13px;
      }
      .callout .callout-mark {
        flex: 0 0 26px;
        width: 26px;
        height: 26px;
        display: grid;
        place-items: center;
        border-radius: 8px;
        font-size: .75rem;
        font-weight: 850;
      }
      .callout strong { display: block; font-size: .82rem; margin-bottom: .08rem; }
      .callout span { display: block; font-size: .78rem; line-height: 1.48; }
      .callout.amber { background: #FFF9ED; border-color: #F5DCA8; color: #704B0D; }
      .callout.amber .callout-mark { background: #FBE7B8; color: #7A510A; }
      .callout.blue { background: #EFF7FC; border-color: #C9E3F1; color: #244F68; }
      .callout.blue .callout-mark { background: #D8EDF7; color: #1D566E; }
      .callout.teal { background: #ECFBF8; border-color: #BCEBE4; color: #145A54; }
      .callout.teal .callout-mark { background: #CFF3ED; color: #12645C; }

      .footer-note {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        color: #7D8B9A;
        font-size: .72rem;
        padding: .35rem .1rem 0;
      }

      @media (max-width: 900px) {
        .block-container { padding: 3.7rem .8rem 2.5rem; }
        .hero { min-height: auto; padding: 1.45rem; border-radius: 18px; }
        .hero-orbit { display: none; }
        .hero h1 { font-size: 2rem; }
        .page-heading { align-items: flex-start; flex-direction: column; }
        .sample-chip { align-self: flex-start; }
        div[data-testid="stMetric"] { min-height: 100px; }
        [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
          flex: 1 1 260px;
          min-width: 260px;
        }
        .footer-note { flex-direction: column; gap: .25rem; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Loading cleaned analytical tables…", ttl=3600)
def load_local_data(processed_dir: str) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    return read_processed_tables(processed_dir)


@st.cache_data(show_spinner="Retrieving and cleaning MongoDB Atlas data…", ttl=900)
def load_atlas_data(
    uri: str, database: str, collection_name: str
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    collection = get_collection(uri, database, collection_name)
    documents = fetch_documents(collection)
    result = clean_documents(documents, "mongodb_atlas")
    return result.listings, result.reviews, result.quality


def _options(series: pd.Series) -> list[str]:
    return sorted(
        value for value in series.dropna().astype(str).unique() if value.strip()
    )


def _plot(figure) -> None:
    st.plotly_chart(
        figure,
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )


def _page_heading(
    eyebrow: str, title: str, description: str, sample_size: int
) -> None:
    st.markdown(
        f"""
        <div class="page-heading">
          <div>
            <div class="eyebrow">{escape(eyebrow.upper())}</div>
            <h2>{escape(title)}</h2>
            <p>{escape(description)}</p>
          </div>
          <div class="sample-chip">{sample_size:,} listings in view</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _section_intro(kicker: str, title: str, description: str) -> None:
    st.markdown(
        f"""
        <div class="section-kicker">{escape(kicker.upper())}</div>
        <div class="section-title">{escape(title)}</div>
        <div class="section-copy">{escape(description)}</div>
        """,
        unsafe_allow_html=True,
    )


def _callout(title: str, body: str, tone: str = "blue", mark: str = "i") -> None:
    st.markdown(
        f"""
        <div class="callout {escape(tone)}">
          <div class="callout-mark">{escape(mark)}</div>
          <div><strong>{escape(title)}</strong><span>{escape(body)}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_filters(listings: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    st.sidebar.markdown('<div class="sidebar-label">FILTERS</div>', unsafe_allow_html=True)
    markets = _options(listings["market"])
    selected_market = st.sidebar.selectbox("Market", ["All markets", *markets])
    filtered = listings.copy()
    if selected_market != "All markets":
        filtered = filtered[filtered["market"] == selected_market]

    area_values = _options(filtered["government_area"])
    areas = st.sidebar.multiselect("Neighborhood / government area", area_values)
    if areas:
        filtered = filtered[filtered["government_area"].isin(areas)]

    room_types = st.sidebar.multiselect("Room type", _options(filtered["room_type"]))
    if room_types:
        filtered = filtered[filtered["room_type"].isin(room_types)]

    property_types = st.sidebar.multiselect(
        "Property type", _options(filtered["property_type"])
    )
    if property_types:
        filtered = filtered[filtered["property_type"].isin(property_types)]

    ratings = filtered["review_score_rating"].dropna()
    if not ratings.empty:
        rating_range = st.sidebar.slider(
            "Rating range (0-100)",
            0,
            100,
            (
                int(max(0, np.floor(ratings.min()))),
                int(min(100, np.ceil(ratings.max()))),
            ),
        )
        filtered = filtered[
            filtered["review_score_rating"].isna()
            | filtered["review_score_rating"].between(*rating_range)
        ]

    if selected_market != "All markets":
        prices = filtered.loc[filtered["price"].gt(0), "price"].dropna()
        if not prices.empty:
            low = float(prices.min())
            high = float(prices.max())
            chosen = st.sidebar.slider(
                "Price range (source price units)",
                min_value=low,
                max_value=high,
                value=(low, high),
            )
            filtered = filtered[
                filtered["price"].isna() | filtered["price"].between(*chosen)
            ]
    else:
        st.sidebar.markdown(
            '<div class="sidebar-hint">Select one market to unlock a comparable price range.</div>',
            unsafe_allow_html=True,
        )
    return filtered, selected_market


def _hero(
    frame: pd.DataFrame,
    total_size: int,
    market: str,
    source_label: str,
    freshness: pd.Timestamp | None,
) -> None:
    market_label = "Global coverage" if market == "All markets" else market
    freshness_label = (
        freshness.strftime("%d %b %Y") if pd.notna(freshness) else "Date unavailable"
    )
    coordinate_coverage = (
        frame["coordinate_valid"].mean() * 100 if not frame.empty else 0.0
    )
    st.markdown(
        f"""
        <div class="hero">
          <div class="hero-inner">
            <div>
              <div class="hero-eyebrow">MARKET INTELLIGENCE / TRUSTED ANALYTICS</div>
              <h1>Airbnb <span>Market Explorer</span></h1>
              <p>Explore listing composition, location patterns, price distributions,
              availability snapshots, review activity, and source quality with transparent guardrails.</p>
              <div class="hero-pills">
                <span class="hero-pill">{escape(market_label)}</span>
                <span class="hero-pill">{len(frame):,} of {total_size:,} listings</span>
                <span class="hero-pill">Source refreshed {escape(freshness_label)}</span>
                <span class="hero-pill">{escape(source_label)}</span>
              </div>
            </div>
            <div class="hero-orbit">
              <span>MAP COVERAGE</span>
              <strong>{coordinate_coverage:.0f}%</strong>
              <small>valid coordinates</small>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def overview_page(frame: pd.DataFrame, market: str) -> None:
    _page_heading(
        "Portfolio pulse",
        "Overview",
        "A high-level view of geographic reach, listing mix, and source ratings.",
        len(frame),
    )
    if frame.empty:
        st.info("No listings match the current filters.")
        return
    ratings = frame["review_score_rating"].dropna()
    named_markets = frame["market"].replace("", np.nan).nunique(dropna=True)
    columns = st.columns(4)
    columns[0].metric("Listings", f"{frame['listing_id'].nunique():,}")
    columns[1].metric("Named markets", f"{named_markets:,}")
    columns[2].metric("Countries", f"{frame['country'].nunique(dropna=True):,}")
    columns[3].metric(
        "Median rating",
        f"{ratings.median():.1f} / 100" if not ratings.empty else "No data",
    )
    st.caption(
        f"Filtered sample: {len(frame):,} listings. Missing ratings are excluded from the rating median."
    )
    _section_intro(
        "Composition",
        "Where supply sits",
        "Listing counts provide comparable coverage context without mixing monetary units.",
    )
    left, right = st.columns(2, gap="large")
    with left:
        _plot(count_bar(frame, "market", "Listings by market"))
    with right:
        _plot(count_bar(frame, "property_type", "Most common property types"))
    if market == "All markets":
        _callout(
            "Price context protected",
            "Price summaries stay hidden across markets because the source does not provide currencies. Select one market for comparable price analysis.",
            tone="blue",
            mark="P",
        )


def map_page(frame: pd.DataFrame, market: str) -> None:
    _page_heading(
        "Spatial explorer",
        "Map",
        "Inspect where listings are concentrated and open rich listing-level hover details.",
        len(frame),
    )
    mapped = frame[frame["coordinate_valid"]].dropna(
        subset=["longitude", "latitude"]
    ).copy()
    if mapped.empty:
        st.info("No valid coordinates match the current filters.")
        return
    sample_note = ""
    if len(mapped) > 1_500:
        mapped = mapped.sample(1_500, random_state=42)
        sample_note = " A deterministic 1,500-listing sample keeps the map responsive."
    mapped["map_size"] = 1.0
    if market == "All markets":
        _callout(
            "Multi-market color rule",
            "Markers use room type rather than price because currencies are unavailable across markets." + sample_note,
            tone="teal",
            mark="M",
        )
    else:
        mapped = mapped[mapped["price"].notna() & mapped["price"].gt(0)]
        if sample_note:
            st.caption(sample_note.strip())
    _section_intro(
        "Geography",
        "Listing locations",
        "Hover a point for market, neighborhood, room type, source price units, and rating.",
    )
    _plot(listing_map(mapped, market != "All markets"))
    st.caption(
        f"Map sample: {len(mapped):,} listings. Coordinates follow GeoJSON [longitude, latitude] order."
    )


def prices_page(frame: pd.DataFrame, market: str) -> None:
    _page_heading(
        "Market-contained analysis",
        "Prices",
        "Robust distributions and neighborhood medians, restricted to one market at a time.",
        len(frame),
    )
    available_markets = _options(frame["market"])
    if not available_markets:
        st.info("No priced listings match the current filters.")
        return
    selected = market
    if market == "All markets":
        selected = st.selectbox(
            "Choose one market for valid price comparisons", available_markets
        )
    priced = frame[
        (frame["market"] == selected)
        & frame["price"].notna()
        & frame["price"].gt(0)
    ].copy()
    if priced.empty:
        st.info("No positive prices are available for this filter combination.")
        return
    _callout(
        "Source price units",
        "The source has no currency field. This page does not rank markets or perform guessed currency conversions.",
        tone="amber",
        mark="U",
    )
    median = priced["price"].median()
    q1, q3 = priced["price"].quantile([0.25, 0.75])
    metrics = st.columns(4)
    metrics[0].metric("Listings", f"{len(priced):,}")
    metrics[1].metric("Median price", f"{median:,.1f}")
    metrics[2].metric("Middle 50%", f"{q1:,.0f}–{q3:,.0f}")
    metrics[3].metric(
        "Flagged extremes", f"{int(priced['price_extreme'].sum()):,}"
    )
    _section_intro(
        "Distribution",
        f"Price shape in {selected}",
        "The marginal box plot keeps medians, quartiles, and long tails visible.",
    )
    _plot(price_histogram(priced, selected))
    summary = local_neighborhood_summary(priced, selected)
    if not summary.empty:
        _section_intro(
            "Location insight",
            "Neighborhood medians",
            "Bubble size represents sample size; hover for quartiles and median rating.",
        )
        _plot(neighborhood_price(summary, selected))


def availability_page(frame: pd.DataFrame) -> None:
    _page_heading(
        "Forward-looking snapshot",
        "Availability",
        "Compare available-day distributions across source horizons without inferring occupancy.",
        len(frame),
    )
    if frame.empty:
        st.info("No listings match the current filters.")
        return
    _callout(
        "Interpretation boundary",
        "Availability is not reservations or realized occupancy. This view does not infer bookings, demand, revenue, or seasonality.",
        tone="amber",
        mark="A",
    )
    horizon = st.selectbox("Availability horizon", [30, 60, 90, 365], index=3)
    column = f"availability_{horizon}"
    available = frame.dropna(subset=[column]).copy()
    if available.empty:
        st.info("No availability values match the current filters.")
        return
    values = available[column]
    metrics = st.columns(3)
    metrics[0].metric("Listings", f"{len(available):,}")
    metrics[1].metric("Median available days", f"{values.median():,.0f}")
    metrics[2].metric(
        "Middle 50%",
        f"{values.quantile(.25):,.0f}–{values.quantile(.75):,.0f}",
    )
    _section_intro(
        "Distribution",
        f"Next {horizon} days",
        "Room-type box plots show the median and spread of snapshot availability.",
    )
    _plot(availability_distribution(available, horizon))


def reviews_page(frame: pd.DataFrame, reviews: pd.DataFrame) -> None:
    listing_ids = set(frame["listing_id"].astype(str))
    events = reviews[reviews["listing_id"].astype(str).isin(listing_ids)].copy()
    _page_heading(
        "Historical proxy",
        "Review activity",
        "Track dated review volume while keeping its limits explicit and visible.",
        len(frame),
    )
    if events.empty:
        st.info("No dated review events match the current filters.")
        return
    _callout(
        "Proxy, not stays",
        "Reviews are incomplete, delayed, and selective. This chart is not bookings, demand, occupancy, or true seasonality.",
        tone="amber",
        mark="R",
    )
    metrics = st.columns(3)
    metrics[0].metric("Review events", f"{len(events):,}")
    metrics[1].metric("First event", f"{events['review_date'].min():%b %Y}")
    metrics[2].metric("Latest event", f"{events['review_date'].max():%b %Y}")
    _section_intro(
        "Timeline",
        "Monthly review activity proxy",
        "Counts reflect submitted source reviews, not a complete record of stays.",
    )
    _plot(review_activity(events))


def quality_page(listings: pd.DataFrame, quality: dict) -> None:
    _page_heading(
        "Trust layer",
        "Data quality",
        "Audit the source coverage, missingness, anomaly flags, and deterministic rules.",
        len(listings),
    )
    metrics = st.columns(4)
    metrics[0].metric(
        "Source documents",
        f"{quality.get('source_document_count', len(listings)):,}",
    )
    metrics[1].metric(
        "Duplicate IDs", f"{quality.get('duplicate_listing_count', 0):,}"
    )
    metrics[2].metric(
        "Invalid coordinates", f"{quality.get('invalid_coordinate_count', 0):,}"
    )
    metrics[3].metric(
        "Extreme prices flagged", f"{quality.get('price_extreme_count', 0):,}"
    )
    _section_intro(
        "Completeness",
        "Missingness profile",
        "Nulls remain null; the pipeline does not silently replace unknown values.",
    )
    _plot(missingness_chart(listings))
    left, right = st.columns(2, gap="large")
    with left, st.container(border=True):
        st.markdown("#### Deterministic rules")
        st.markdown(
            "- Keep the first occurrence of a duplicate listing ID.\n"
            "- Exclude only source rows without a listing ID.\n"
            "- Keep missing numeric values null.\n"
            "- Retain and flag anomalous prices.\n"
            "- Validate longitude before latitude."
        )
    with right, st.container(border=True):
        st.markdown("#### Interpretation safeguards")
        st.markdown(
            "- Compare prices only inside one market.\n"
            "- Treat availability as a snapshot.\n"
            "- Label review counts as a proxy.\n"
            "- Exclude missing ratings from summaries.\n"
            "- Preserve source provenance in exports."
        )
    with st.expander("Verified schema discrepancies from the project brief"):
        for item in quality.get("schema_discrepancies_from_brief", []):
            st.write(f"- {item}")


def main() -> None:
    settings = Settings.from_env()
    st.sidebar.markdown(
        """
        <div class="brand">
          <div class="brand-mark">A</div>
          <div class="brand-copy"><strong>Airbnb Atlas</strong><span>MARKET EXPLORER</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        '<div class="sidebar-label">DATA CONNECTION</div>', unsafe_allow_html=True
    )
    source_options = ["Local processed files"]
    if settings.mongodb_uri:
        source_options.append("MongoDB Atlas")
    source_mode = st.sidebar.selectbox("Data source", source_options)

    try:
        if source_mode == "MongoDB Atlas":
            listings, reviews, quality = load_atlas_data(
                settings.mongodb_uri or "",
                settings.mongodb_database,
                settings.mongodb_collection,
            )
        else:
            listings, reviews, quality = load_local_data(
                str(settings.processed_dir)
            )
    except Exception as exc:  # Streamlit must show a useful empty state.
        st.error(str(exc))
        st.code("airbnb-analysis all --json data/raw/sample_airbnb.json")
        st.stop()

    st.sidebar.markdown(
        '<div class="sidebar-label">WORKSPACE</div>', unsafe_allow_html=True
    )
    page = st.sidebar.radio(
        "Explore",
        ["Overview", "Map", "Prices", "Availability", "Reviews", "Data Quality"],
        label_visibility="collapsed",
    )
    filtered, market = apply_filters(listings)
    st.sidebar.markdown(
        f"""
        <div class="selection-card">
          <span>VISIBLE SAMPLE</span>
          <strong>{len(filtered):,}</strong> <small>of {len(listings):,} listings</small>
        </div>
        <div class="status-line"><i class="status-dot"></i> Analytical model ready</div>
        """,
        unsafe_allow_html=True,
    )

    freshness = listings["last_scraped"].max()
    source_label = (
        "MongoDB Atlas" if source_mode == "MongoDB Atlas" else "Local analytical model"
    )
    _hero(filtered, len(listings), market, source_label, freshness)

    if page == "Overview":
        overview_page(filtered, market)
    elif page == "Map":
        map_page(filtered, market)
    elif page == "Prices":
        prices_page(filtered, market)
    elif page == "Availability":
        availability_page(filtered)
    elif page == "Reviews":
        reviews_page(filtered, reviews)
    else:
        quality_page(listings, quality)

    st.divider()
    st.markdown(
        """
        <div class="footer-note">
          <span>Airbnb Atlas · analytical capstone interface</span>
          <span>Source price units · no inferred occupancy · no global price ranking</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
