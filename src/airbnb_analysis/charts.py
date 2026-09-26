"""Plotly chart builders shared by the Streamlit application."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

ACCENT = "#FF5A5F"
NAVY = "#16324F"
TEAL = "#00A699"
GOLD = "#E59F25"
PALETTE = [TEAL, ACCENT, NAVY, GOLD, "#7C6FF0", "#6B7C8F"]


def _finish(figure: go.Figure, height: int = 430) -> go.Figure:
    figure.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=28, r=28, t=66, b=34),
        font=dict(family="Inter, Arial, sans-serif", color="#243447"),
        title=dict(font=dict(size=18, color=NAVY), x=0.02, xanchor="left"),
        legend_title_text="",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="#D8E1EA",
            font_size=12,
            font_family="Inter, Arial, sans-serif",
        ),
        hovermode="closest",
    )
    figure.update_xaxes(
        showgrid=True,
        gridcolor="#EDF1F5",
        zeroline=False,
        linecolor="#DCE3EA",
        title_standoff=12,
        tickfont=dict(color="#66788A"),
    )
    figure.update_yaxes(
        showgrid=False,
        zeroline=False,
        linecolor="#DCE3EA",
        title_standoff=12,
        tickfont=dict(color="#66788A"),
    )
    return figure


def count_bar(
    frame: pd.DataFrame, category: str, title: str, limit: int = 12
) -> go.Figure:
    counts = (
        frame[category]
        .fillna("Unknown")
        .replace("", "Unknown")
        .value_counts()
        .head(limit)
        .sort_values()
        .rename_axis(category)
        .reset_index(name="listings")
    )
    figure = px.bar(
        counts,
        x="listings",
        y=category,
        orientation="h",
        title=title,
        color_discrete_sequence=[TEAL],
        labels={category: "", "listings": "Listings"},
        text_auto=",.0f",
    )
    figure.update_traces(
        textposition="outside",
        cliponaxis=False,
        marker_line_width=0,
        hovertemplate="%{y}<br>%{x:,.0f} listings<extra></extra>",
    )
    return _finish(figure)


def listing_map(frame: pd.DataFrame, single_market: bool) -> go.Figure:
    hover = {
        "name": True,
        "market": True,
        "government_area": True,
        "room_type": True,
        "price": ":,.1f",
        "review_score_rating": ":.0f",
        "latitude": False,
        "longitude": False,
    }
    if single_market:
        figure = px.scatter_map(
            frame,
            lat="latitude",
            lon="longitude",
            color="price",
            size="map_size",
            size_max=13,
            color_continuous_scale=["#FFE5E6", ACCENT, "#8C1D40"],
            hover_data=hover,
            title="Listings colored by price within the selected market",
            labels={"price": "Source price units"},
            zoom=9,
            map_style="open-street-map",
        )
    else:
        figure = px.scatter_map(
            frame,
            lat="latitude",
            lon="longitude",
            color="room_type",
            size="map_size",
            size_max=11,
            color_discrete_sequence=PALETTE,
            hover_data=hover,
            title="Listing locations colored by room type",
            zoom=1,
            map_style="open-street-map",
        )
    figure.update_layout(
        map=dict(bearing=0, pitch=0),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="left",
            x=0,
        ),
    )
    return _finish(figure, height=610)


def price_histogram(frame: pd.DataFrame, market: str) -> go.Figure:
    figure = px.histogram(
        frame,
        x="price",
        color="room_type",
        marginal="box",
        nbins=60,
        opacity=0.82,
        color_discrete_sequence=PALETTE,
        title=f"Price distribution in {market}",
        labels={"price": "Source price units", "count": "Listings"},
    )
    figure.update_layout(
        bargap=0.04,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="right",
            x=1,
        ),
    )
    figure.update_traces(marker_line_width=0)
    return _finish(figure, height=520)


def neighborhood_price(frame: pd.DataFrame, market: str) -> go.Figure:
    display = frame.sort_values("median_price").tail(20)
    figure = px.scatter(
        display,
        x="median_price",
        y="government_area",
        size="listing_count",
        color="listing_count",
        color_continuous_scale=["#D9F3EF", TEAL, NAVY],
        title=f"Neighborhood medians in {market}",
        labels={
            "median_price": "Median source price units",
            "government_area": "",
            "listing_count": "Listings",
        },
        hover_data={"price_q1": ":,.1f", "price_q3": ":,.1f", "median_rating": ":.1f"},
    )
    figure.update_traces(marker_line_color="white", marker_line_width=1.25)
    return _finish(figure, height=max(440, 24 * len(display) + 160))


def availability_distribution(frame: pd.DataFrame, horizon: int) -> go.Figure:
    column = f"availability_{horizon}"
    figure = px.box(
        frame,
        x="room_type",
        y=column,
        color="room_type",
        points=False,
        color_discrete_sequence=PALETTE,
        title=f"Available-day snapshot for the next {horizon} days",
        labels={"room_type": "Room type", column: "Available days"},
    )
    figure.update_layout(showlegend=False)
    figure.update_traces(line=dict(width=1.4), fillcolor="rgba(0,166,153,.18)")
    return _finish(figure)


def review_activity(reviews: pd.DataFrame) -> go.Figure:
    monthly = (
        reviews.set_index("review_date")
        .resample("MS")
        .size()
        .rename("reviews")
        .reset_index()
    )
    figure = px.line(
        monthly,
        x="review_date",
        y="reviews",
        title="Monthly review activity proxy",
        labels={"review_date": "Review month", "reviews": "Reviews"},
        color_discrete_sequence=[ACCENT],
    )
    figure.update_traces(
        line_width=2.8,
        fill="tozeroy",
        fillcolor="rgba(255,90,95,.10)",
        hovertemplate="%{x|%b %Y}<br>%{y:,.0f} reviews<extra></extra>",
    )
    return _finish(figure)


def missingness_chart(frame: pd.DataFrame) -> go.Figure:
    focus_fields = [
        "security_deposit",
        "cleaning_fee",
        "review_score_rating",
        "first_review",
        "last_review",
        "beds",
        "bathrooms",
        "bedrooms",
        "price",
        "longitude",
        "latitude",
    ]
    available_fields = [field for field in focus_fields if field in frame]
    missing = (
        frame[available_fields]
        .isna()
        .mean()
        .mul(100)
        .loc[lambda values: values.gt(0)]
        .sort_values(ascending=False)
        .head(15)
        .rename("missing_percent")
        .rename_axis("field")
        .reset_index(name="missing_percent")
        .sort_values("missing_percent")
    )
    figure = px.bar(
        missing,
        x="missing_percent",
        y="field",
        orientation="h",
        title="Fields with the most missing values",
        color_discrete_sequence=[GOLD],
        labels={"missing_percent": "Missing (%)", "field": ""},
        text_auto=".1f",
    )
    figure.update_traces(
        marker_line_width=0,
        texttemplate="%{x:.1f}%",
        textposition="outside",
        cliponaxis=False,
    )
    return _finish(figure)

