import pandas as pd
import altair as alt
from typing import Dict, List


def _build_month_labels(month_cols: List[str]) -> Dict[str, str]:
    """
    Sheet22 has repeated month names (MAR, APR, ... MAR.1, APR.1, ...)
    Build stable labels that preserve column order and disambiguate duplicates.
    Example: MAR -> MAR, APR -> APR, ... MAR.1 -> MAR_2
    """
    labels: Dict[str, str] = {}
    seen: Dict[str, int] = {}
    for col in month_cols:
        base = str(col).replace(".", "_").strip()
        count = seen.get(base, 0) + 1
        seen[base] = count
        labels[col] = f"{base}_{count}" if count > 1 else base
    return labels


def build_location_trend_frame(sheet22: pd.DataFrame) -> pd.DataFrame:
    """
    Transform Sheet22 (wide, month columns) into a long DataFrame for sparklines.
    Returns columns: Month, Location, Total
    """
    if sheet22 is None or sheet22.empty or "Location" not in sheet22.columns:
        return pd.DataFrame(columns=["Month", "Location", "Total"])

    df = sheet22.copy()
    df["Location"] = df["Location"].astype(str).str.strip()
    month_cols = [c for c in df.columns if str(c).strip().lower() != "location"]
    if not month_cols:
        return pd.DataFrame(columns=["Month", "Location", "Total"])

    label_map = _build_month_labels(month_cols)
    ordered_labels = [label_map[c] for c in month_cols]

    records = []
    for _, row in df.iterrows():
        loc = row["Location"]
        for col in month_cols:
            val = pd.to_numeric(row[col], errors="coerce")
            if pd.isna(val):
                continue
            records.append({"Month": label_map[col], "Location": loc, "Total": float(val)})

    trend_df = pd.DataFrame.from_records(records)
    trend_df["Month"] = pd.Categorical(trend_df["Month"], categories=ordered_labels, ordered=True)
    return trend_df


def sparkline_chart(trend_df: pd.DataFrame, location: str, width: int = 160, height: int = 60) -> alt.Chart:
    """
    Build a single-location sparkline (line + points) for embedding in tables/cards.
    Expects trend_df from build_location_trend_frame.
    """
    filtered = trend_df[trend_df["Location"] == location]
    if filtered.empty:
        filtered = pd.DataFrame({"Month": [], "Total": []})

    month_order = list(trend_df["Month"].cat.categories) if "Month" in trend_df and hasattr(trend_df["Month"], "cat") else "ascending"

    base = (
        alt.Chart(filtered)
        .mark_line(point=True)
        .encode(
            x=alt.X("Month:N", sort=month_order, axis=None, title=None),
            y=alt.Y("Total:Q", axis=None, title=None),
            tooltip=[
                alt.Tooltip("Month:N"),
                alt.Tooltip("Total:Q", format="$,.2f"),
            ],
        )
        .properties(width=width, height=height)
    )
    return base


def demo_sparklines(trend_df: pd.DataFrame) -> alt.Chart:
    """
    Convenience helper to preview sparklines for the top 10 revenue locations.
    Returns an Altair facet chart (not used in app yet).
    """
    if trend_df is None or trend_df.empty:
        return alt.Chart(pd.DataFrame({"Month": [], "Total": []})).mark_line()

    totals = (
        trend_df.groupby("Location")["Total"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .index.tolist()
    )

    top_df = trend_df[trend_df["Location"].isin(totals)]
    month_order = list(trend_df["Month"].cat.categories)
    return (
        alt.Chart(top_df)
        .mark_line(point=True)
        .encode(
            x=alt.X("Month:N", sort=month_order, axis=None),
            y=alt.Y("Total:Q", axis=None),
            facet=alt.Facet("Location:N", columns=2),
            tooltip=[alt.Tooltip("Month:N"), alt.Tooltip("Total:Q", format="$,.2f")],
        )
        .properties(width=180, height=70)
    )


def multi_location_chart(
    trend_df: pd.DataFrame,
    locations: list[str] | None = None,
    width: int = 1400,
    height: int = 350,
) -> alt.Chart:
    """
    Plot month on x-axis, revenue on y-axis, with separate lines per location.
    If locations is None, show all.
    """
    if trend_df is None or trend_df.empty:
        return alt.Chart(pd.DataFrame({"Month": [], "Total": []})).mark_line()

    if locations:
        data = trend_df[trend_df["Location"].isin(locations)]
    else:
        data = trend_df

    month_order = list(trend_df["Month"].cat.categories)

    loc_count = data["Location"].nunique()
    loc_order = sorted(data["Location"].unique())

    base = (
        alt.Chart(data)
        .mark_line(point=True)
        .encode(
            x=alt.X("Month:N", sort=month_order, title="Month"),
            y=alt.Y("Total:Q", title="Revenue"),
            tooltip=[
                alt.Tooltip("Location:N"),
                alt.Tooltip("Month:N"),
                alt.Tooltip("Total:Q", format="$,.2f"),
            ],
        )
        .properties(width=width, height=height)
    )

    # If many locations are plotted, facet them to avoid overlapping lines
    if loc_count > 6:
        facet_base = base.encode()
        # Set per-facet height smaller for compact stacking
        facet_base = facet_base.properties(height=80)
        return facet_base.facet(
            row=alt.Row("Location:N", sort=loc_order, title=None),
            spacing=8,
        ).resolve_scale(y="independent")

    # Few locations: show combined lines with color legend
    return (
        base.encode(color=alt.Color("Location:N", sort=loc_order, title="Location"))
    )
