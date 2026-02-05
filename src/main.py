import io
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from auth import authenticate, User
from config import APP_TITLE, EXPORT_DIR
from data_loader import load_all_months, load_sheet22
from kpi_service import calculate_kpis, calc_mom, build_trend_series, VOICE_COLS, SMS_COLS
from pdf_export import export_board_pdf
from sheet22_service import build_sheet22_context
from sparkline import build_location_trend_frame, multi_location_chart
from utils import fmt_currency, fmt_pct, sort_month_sheets


st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="collapsed")


# =========================
# Streamlit 1.40-safe styling
# =========================
def inject_board_css():
    st.markdown(
        """
        <style>
        :root {
            --app-bg: #0a0a0c;
            --panel-bg: #111218;
            --panel-border: #2a2c35;
            --text-primary: #f5f7ff;
            --text-muted: rgba(245, 247, 255, 0.65);
            --chip-bg: #1b1e27;
            --chip-border: #343846;
            --login-shell-bg: radial-gradient(circle at top, #0d4950 0%, #062b32 52%, #051c22 100%);
            --login-card-bg: linear-gradient(140deg, #0a3840 0%, #062a31 55%, #041a20 100%);
            --login-field-bg: rgba(255, 255, 255, 0.12);
            --login-field-border: rgba(255, 255, 255, 0.12);
            --login-field-border-focus: rgba(255, 255, 255, 0.32);
        }

        html, body, .stApp {
            background: var(--app-bg) !important;
            color: var(--text-primary) !important;
        }
        .block-container { padding-top: 1.4rem; padding-bottom: 2.5rem; }
        .stMarkdown, .stText, .stMetric, .stMarkdown p { color: var(--text-primary); }
        .stCaption { color: var(--text-muted) !important; }
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 { color: var(--text-primary); }

        section[data-testid="stSidebar"] > div {
            background: #0f1014;
            color: var(--text-primary);
        }

        /* Hide chart chrome / toolbar */
        div[data-testid="stToolbar"],
        div[data-testid="stHeader"],
        div[data-testid="stDecoration"],
        button[data-testid="stFullScreenButton"],
        button[aria-label="View fullscreen"],
        button[aria-label="Enlarge chart"],
          button[title="View fullscreen"],
          button[title="Enlarge chart"] {
              display: none !important;
              height: 0 !important;
          }
        div[data-testid="stAltairChart"] > div:first-child { display:none !important; }

        /* KPI metric cards: simple, no heavy shadows */
        div[data-testid="stMetric"] {
            background: var(--panel-bg);
            padding: 12px 14px;
            border-radius: 14px;
            border: 1px solid var(--panel-border);
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.45);
            transition: box-shadow 140ms ease, transform 140ms ease, border-color 140ms ease;
        }
        div[data-testid="stMetric"]:hover {
            border-color: #3a3f4f;
            box-shadow: 0 8px 22px rgba(0, 0, 0, 0.55);
            transform: translateY(-1px);
        }
        div[data-testid="stMetric"] label { color: var(--text-muted); font-weight: 650; }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: var(--text-primary); }
        div[data-testid="stMetric"] [data-testid="stMetricDelta"] { font-weight: 650; }

        /* Neutralize Streamlit's built-in bordered container */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: transparent !important;
            border: none !important;
            border-radius: 0 !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] > div {
            background: transparent !important;
            border: none !important;
            padding: 0 !important;
            margin: 0 !important;
            box-shadow: none !important;
        }

        /* Custom card surface */
        .card-surface {
            background: var(--panel-bg);
            border: 1px solid var(--panel-border);
            border-radius: 14px;
            padding: 14px 16px 16px 16px;
            box-shadow: 0 6px 18px rgba(0, 0, 0, 0.5);
            transition: box-shadow 140ms ease, transform 140ms ease, border-color 140ms ease;
            margin-bottom: 18px;
        }
        .card-surface:hover {
            border-color: #3a3f4f;
            box-shadow: 0 10px 26px rgba(0, 0, 0, 0.6);
            transform: translateY(-1px);
        }

        /* Card header */
        .card-title-row{
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap:12px;
            margin-bottom: 8px;
        }
        .card-title{
            margin:0;
            font-size:24px;
            font-weight:700;
            letter-spacing:-0.02em;
            color: var(--text-primary);
        }
        .card-subtitle{
            margin: -4px 0 10px 0;
            color: var(--text-muted);
            font-size: 13px;
        }
        .card-chip{
            display:inline-flex;
            align-items:center;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 600;
            color: var(--text-muted);
            background: var(--chip-bg);
            border: 1px solid var(--chip-border);
            white-space: nowrap;
        }

        /* Flatten chart/table wrappers inside cards */
        div[data-testid="stAltairChart"],
        div[data-testid="stDataFrame"],
        div[data-testid="stTable"] {
            background: transparent !important;
            padding: 0 !important;
            margin: 0 !important;
            border: none !important;
            box-shadow: none !important;
        }
        div[data-testid="stDataFrame"] table,
        div[data-testid="stTable"] table {
            color: var(--text-primary);
            background: transparent !important;
        }

        .stButton > button {
            background: #1a1f2a;
            color: var(--text-primary);
            border: 1px solid #3a3f4f;
        }
        .stButton > button:hover {
            border-color: #4b5164;
            background: #202634;
        }

        /* Login layout */

        /* User menu (top-right) */
        .user-menu-wrap {
            display: flex;
            justify-content: flex-end;
            margin: 0.25rem 0 1rem;
        }
        button[data-testid="stPopoverButton"] {
            width: 42px !important;
            height: 42px !important;
            border-radius: 999px !important;
            background: #0f2a31 !important;
            border: 1px solid #1f3f49 !important;
            color: #f5fbff !important;
            font-size: 18px !important;
            box-shadow: 0 10px 24px rgba(0,0,0,0.3);
            transition: transform 120ms ease, box-shadow 120ms ease, border-color 120ms ease;
        }
        button[data-testid="stPopoverButton"]:hover {
            border-color: #2c5a69 !important;
            box-shadow: 0 14px 32px rgba(0,0,0,0.45);
            transform: translateY(-1px);
        }
        div[data-testid="stPopoverContent"] {
            background: #0f1f26 !important;
            border: 1px solid #2a3d47 !important;
            border-radius: 14px !important;
            padding: 0.5rem !important;
            box-shadow: 0 18px 40px rgba(0,0,0,0.45);
        }
        div[data-testid="stPopoverContent"] .stButton > button {
            width: 100% !important;
            background: transparent !important;
            border: 1px solid #2f4752 !important;
            color: #f5fbff !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def card(title: str, subtitle: str | None = None, chip: str | None = None):
    """
    Simple card wrapper using st.container(border=True) styled via CSS.
    Usage:
      with card("Title", "Subtitle", "Chip"):
          st.altair_chart(...)
    """
    chip_html = f'<div class="card-chip">{chip}</div>' if chip else ""
    subtitle_html = f'<div class="card-subtitle">{subtitle}</div>' if subtitle else ""
    container = st.container()
    container.markdown(
        f'<div class="card-surface"><div class="card-title-row"><div class="card-title">{title}</div>{chip_html}</div>{subtitle_html}',
        unsafe_allow_html=True,
    )
    body = container.container()
    container.markdown("</div>", unsafe_allow_html=True)
    return body


# -----------------------------
# Altair theme (safe dict theme)
# -----------------------------
def _enable_board_theme():
    def board_theme():
        return {
            "config": {
                "axis": {
                    "labelFontSize": 12,
                    "titleFontSize": 12,
                    "labelColor": "#E6E8F0",
                    "titleColor": "#E6E8F0",
                    "gridColor": "#1F2430",
                    "domainColor": "#3B4150",
                    "tickColor": "#3B4150",
                },
                "legend": {
                    "labelFontSize": 12,
                    "titleFontSize": 12,
                    "labelColor": "#E6E8F0",
                    "titleColor": "#E6E8F0",
                },
                "title": {"fontSize": 14, "fontWeight": 600, "color": "#E6E8F0"},
                "view": {"stroke": "transparent"},
                "background": "transparent",
            }
        }

    try:
        alt.themes.register("board_theme", board_theme)
    except Exception:
        pass
    try:
        alt.themes.enable("board_theme")
    except Exception:
        alt.themes.enable("default")


# -----------------------------
# Session helpers
# -----------------------------
def _get_user() -> User | None:
    return st.session_state.get("user")


def _set_user(user: User | None) -> None:
    st.session_state["user"] = user


# -----------------------------
# Data/model
# -----------------------------
def load_model():
    try:
        months_raw = load_all_months()  # dict: {sheet_name: df}
    except Exception as e:
        st.error(f"Failed to load monthly sheets: {e}")
        return None
    if not months_raw:
        st.error("No monthly sheets found in the primary Excel workbook.")
        return None

    month_names_sorted = sort_month_sheets(list(months_raw.keys()))
    if not month_names_sorted:
        month_names_sorted = sorted(months_raw.keys())

    months = {name: months_raw[name] for name in month_names_sorted}

    latest_name = month_names_sorted[-1]
    latest_df = months[latest_name]
    latest_kpis = calculate_kpis(latest_df)

    mom = None
    mom_label = None
    if len(month_names_sorted) >= 2:
        prev_name = month_names_sorted[-2]
        prev_df = months[prev_name]
        mom = calc_mom(latest_df, prev_df)
        mom_label = f"MoM compares {prev_name} -> {latest_name}"

    trend = build_trend_series(months)

    sheet22_df = load_sheet22()
    sheet22_ctx = build_sheet22_context(sheet22_df)
    location_trend_df = build_location_trend_frame(sheet22_df)

    return {
        "months": months,
        "latest_name": latest_name,
        "latest_df": latest_df,
        "latest_kpis": latest_kpis,
        "mom": mom,
        "mom_label": mom_label,
        "trend": trend,
        "sheet22_ctx": sheet22_ctx,
        "location_trend_df": location_trend_df,
    }


# -----------------------------
# Auth + sidebar
# -----------------------------
def render_login():
    st.title("USER LOGIN")
    st.caption("Sign in to access SINBIP reporting views")
    with st.form("login"):
        username = st.text_input("Username", placeholder="Username")
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Password",
        )
        submitted = st.form_submit_button("LOGIN", use_container_width=True)
        if submitted:
            user = authenticate(username or "", password or "")
            if not user:
                st.error("Invalid credentials")
            else:
                _set_user(user)
                st.success(f"Signed in as {user.role}")
                st.rerun()

def render_user_menu(user: User):
    col_spacer, col_menu = st.columns([8, 1])
    with col_menu:
        st.markdown('<div class="user-menu-wrap">', unsafe_allow_html=True)
        with st.popover("👤"):
            st.caption(f"Signed in as {user.username} ({user.role})")
            if st.button("Logout", key="logout_button"):
                _set_user(None)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# KPI / charts
# -----------------------------
def render_kpi_strip(kpis: dict):
    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)

    col1.metric("Total Revenue", fmt_currency(kpis["total_revenue"]))
    col2.metric("Avg Revenue per NBIP", fmt_currency(kpis["avg_revenue"]))
    col3.metric("Mobile Data Share", fmt_pct(kpis["data_share_pct"]))
    zero_count = kpis.get("zero_revenue_sites", 0)
    col4.metric("Zero-Revenue Sites", zero_count)
    col5.metric("Top Site", kpis["top_site"])
    col6.metric("Top 10 Concentration", f"{kpis['concentration_ratio']*100:.1f}%")


def render_mom(mom: dict | None, mom_label: str | None):
    if not mom:
        return
    st.subheader("Month-on-Month Revenue Movement")
    if mom_label:
        st.caption(mom_label)
    delta_value = float(mom.get("delta", 0.0))
    pct_change = float(mom.get("pct_change", 0.0))
    direction = "up" if delta_value > 0 else "down" if delta_value < 0 else "flat"
    arrow = "▲" if direction == "up" else "▼" if direction == "down" else "■"
    color = "#16a34a" if direction == "up" else "#dc2626" if direction == "down" else "#6b7280"

    delta_label = f"{arrow} {fmt_currency(delta_value)} ({pct_change:.1f}%)"
    st.markdown(
        f"<div style='font-size:1.1rem; font-weight:600; color:{color};'>{delta_label}</div>",
        unsafe_allow_html=True,
    )
    st.metric("MoM Revenue Change", fmt_currency(mom["current_total"]))


def render_bar_chart(df: pd.DataFrame):
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
        .encode(
            x=alt.X("Location:N", sort="-y", title="Location", axis=alt.Axis(labelAngle=270)),
            y=alt.Y("Total:Q", title="Total Revenue", axis=alt.Axis(format="$,.2f")),
            tooltip=[alt.Tooltip("Location:N"), alt.Tooltip("Total:Q", format="$,.2f")],
        )
        .properties(height=310)
    )
    st.altair_chart(chart, use_container_width=True)


def render_trend(trend: dict):
    trend_df = pd.DataFrame(
        {
            "Month": [str(x) for x in trend["months"]],
            "Total Revenue": [float(x) for x in trend["total_revenue"]],
        }
    )
    chart = (
        alt.Chart(trend_df)
        .mark_line(point=alt.OverlayMarkDef(size=55))
        .encode(
            x=alt.X("Month:N", title="Month"),
            y=alt.Y("Total Revenue:Q", title="Total Revenue", axis=alt.Axis(format="$,.2f")),
            tooltip=[alt.Tooltip("Month:N"), alt.Tooltip("Total Revenue:Q", format="$,.2f")],
        )
        .properties(height=360)
    )
    st.altair_chart(chart, use_container_width=True)


def render_revenue_mix(kpis: dict):
    mix = kpis["revenue_mix"]
    mix_df = pd.DataFrame(
        {"Category": ["Voice", "SMS", "Data"], "Value": [mix["voice"], mix["sms"], mix["data"]]}
    )
    chart = (
        alt.Chart(mix_df)
        .mark_arc(innerRadius=75)
        .encode(
            theta="Value:Q",
            color=alt.Color("Category:N", legend=alt.Legend(title="Category", orient="right")),
            tooltip=[alt.Tooltip("Category:N"), alt.Tooltip("Value:Q", format="$,.2f")],
        )
        .properties(height=320)
    )
    st.altair_chart(chart, use_container_width=True)


# -----------------------------
# Views
# -----------------------------
def render_board_view(model: dict):
    latest_name = model["latest_name"]
    kpis = model["latest_kpis"]
    mom = model["mom"]
    mom_label = model["mom_label"]
    sheet22_ctx = model["sheet22_ctx"]

    st.title(APP_TITLE)
    st.caption(f"Overview — Reporting Month: {latest_name}")

    render_kpi_strip(kpis)
    render_mom(mom, mom_label)

    top_10 = kpis["top_10_sites"].copy()
    bottom_10 = kpis["bottom_10_sites"].copy()

    # Row 1: three cards
    col_m1, col_m2, col_m3 = st.columns(3, gap="large")

    with col_m1:
        c = card("Revenue Mix", "Distribution of revenue across Voice, SMS and Mobile Data.", chip=f"Month: {latest_name}")
        with c:
            render_revenue_mix(kpis)

    with col_m2:
        c = card("Top 10 Locations", "Highest revenue NBIP sites for the reporting month.", chip="Top performers")
        with c:
            render_bar_chart(top_10)

    with col_m3:
        c = card("Bottom 10 Locations", "Lowest revenue NBIP sites for the reporting month.", chip="At risk")
        with c:
            render_bar_chart(bottom_10)

    # Row 2: trend + table
    col_t1, col_t2 = st.columns(2, gap="large")

    with col_t1:
        c = card("Revenue Generation", "Total revenue over time (all available months).", chip="Trend")
        with c:
            render_trend(model["trend"])

    with col_t2:
        c = card("Top 10 Locations", "Ranked table view for board scanning and export.")
        with c:
            top_display = top_10.copy()
            top_display["Total"] = top_display["Total"].map(fmt_currency)
            st.dataframe(top_display, use_container_width=True, height=385)

    # Bottom insights: full-width cards
    concentration_pct = kpis["concentration_ratio"] * 100.0
    c = card("Risk Indicator", "Revenue concentration in the top 10 sites (higher = more concentration risk).", chip=f"{concentration_pct:.1f}%")
    with c:
        st.write(f"Top 10 NBIP sites contribute **{concentration_pct:.1f}%** of total revenue.")
        st.progress(min(max(kpis["concentration_ratio"], 0.0), 1.0))

    zero_names_display = ", ".join(kpis.get("zero_revenue_locations") or [])
    c = card("Executive Observations & Recommended Actions", "Board-ready talking points derived from the latest month.", chip="Insights")
    with c:
        st.markdown(
            f"""
- **Top-performing site:** {kpis['top_site']} ({fmt_currency(kpis['top_site_value'])})
- **Underutilised assets:** {kpis['zero_revenue_sites']} sites recorded **zero revenue** in {latest_name}{(": " + zero_names_display) if zero_names_display else "."}
- **Concentration risk:** Top 10 sites contribute **{concentration_pct:.1f}%** of total revenue.
- **Recommended action:** Validate zero/low sites, investigate coverage/market constraints, and prioritise data-led uplift plans.
"""
        )

    if sheet22_ctx.get("target_total") is not None:
        target_total = float(sheet22_ctx["target_total"])
        achievement = (kpis["total_revenue"] / target_total * 100.0) if target_total else 0.0
        c = card("Target Achievement (Sheet22)", "Control/target sourced from Sheet22 (validation/control sheet).", chip=f"{achievement:.1f}%")
        with c:
            st.info(
                f"Target achievement is **{achievement:.1f}%** for {latest_name}. "
                "If this looks off, confirm Sheet22 target totals and month mapping."
            )

    if sheet22_ctx.get("notes"):
        c = card("Sheet22 Notes (Control / Validation)", "Control notes and validation messages from Sheet22.", chip="Control")
        with c:
            for n in sheet22_ctx["notes"]:
                st.write(f"- {n}")

    # Export card
    c = card("Board Pack Export", "Generate a one-page board PDF for sharing.", chip="PDF")
    with c:
        if st.button("Export Board PDF", use_container_width=True):
            filename = f"SINBIP_Board_Report_{latest_name}.pdf"
            out_path = EXPORT_DIR / filename
            export_board_pdf(
                output_path=out_path,
                title=APP_TITLE,
                kpis=kpis,
                mom=mom,
                sheet22_ctx=sheet22_ctx,
                trend=model.get("trend"),
                latest_name=latest_name,
            )
            with open(out_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                "Download Board PDF",
                data=pdf_bytes,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
            )


def render_management_view(model: dict):
    latest_name = model["latest_name"]
    months = model["months"]
    trend_df = model.get("location_trend_df")

    st.title("SINBIP Management Performance View")
    st.caption(f"Latest month: {latest_name} (management drill-down)")

    month_names = list(months.keys())
    selected_name = st.selectbox("Select Month", month_names, index=month_names.index(latest_name))

    df = months[selected_name].copy().sort_values("Total", ascending=False)

    df["Voice Revenue"] = df[VOICE_COLS].sum(axis=1)
    df["SMS Revenue"] = df[SMS_COLS].sum(axis=1)

    display_df = df[["Location", "Total", "Voice Revenue", "SMS Revenue", "Mobile Data Revenue"]].copy()
    display_df["Total"] = display_df["Total"].map(fmt_currency)
    display_df["Voice Revenue"] = display_df["Voice Revenue"].map(fmt_currency)
    display_df["SMS Revenue"] = display_df["SMS Revenue"].map(fmt_currency)
    display_df["Mobile Data Revenue"] = display_df["Mobile Data Revenue"].map(fmt_currency)

    c = card("Monthly Location Breakdown", "Revenue breakdown by location.", chip=f"Month: {selected_name}")
    with c:
        st.dataframe(display_df, use_container_width=True, height=460)

    c = card("Location Revenue Sparkline", "Multi-location trend view across months.", chip="Trend")
    with c:
        if trend_df is None or trend_df.empty:
            st.info("No sparkline data available.")
        else:
            locations = sorted(trend_df["Location"].unique())
            total_by_loc = trend_df.groupby("Location")["Total"].sum().sort_values(ascending=False)
            default_locs = [loc for loc in total_by_loc.index[:5] if loc in locations]
            selected_locs = st.multiselect(
                "Select locations to plot",
                options=locations,
                default=default_locs or locations[:5],
            )
            st.altair_chart(multi_location_chart(trend_df, selected_locs), use_container_width=True)


# -----------------------------
# App
# -----------------------------
def main():
    inject_board_css()
    _enable_board_theme()

    if "user" not in st.session_state:
        _set_user(None)

    user = _get_user()
    if not user:
        render_login()
        return

    render_user_menu(user)

    model = load_model()
    if model is None:
        return

    if user.role == "board":
        render_board_view(model)
    else:
        render_management_view(model)


if __name__ == "__main__":
    main()
