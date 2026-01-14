import pandas as pd
from typing import Dict, Any, Tuple

VOICE_COLS = [
    "NBIP-NBIP Calls Revenue",
    "Fixed Calls Revenue",
    "Telekom Calls Revenue",
    "BMobile Calls Revenue",
    "International Calls Revenue",
]

SMS_COLS = [
    "A2P SMS Revenue",
    "Telekom SMS Revenue",
    "BMobile SMS Revenue",
    "International SMS Revenue",
]

DATA_COL = "Mobile Data Revenue"
TOTAL_COL = "Total"

def calculate_kpis(df: pd.DataFrame) -> dict:
    empty_sites = pd.DataFrame(columns=["Location", TOTAL_COL])
    if TOTAL_COL not in df.columns or df.empty:
        return {
            "total_revenue": 0.0,
            "avg_revenue": 0.0,
            "revenue_mix": {"voice": 0.0, "sms": 0.0, "data": 0.0},
            "data_share_pct": 0.0,
            "zero_revenue_sites": 0,
            "zero_revenue_locations": [],
            "top_site": "-",
            "top_site_value": 0.0,
            "top_10_sites": empty_sites.copy(),
            "bottom_10_sites": empty_sites.copy(),
            "concentration_ratio": 0.0,
        }

    work = df.copy()
    work["Location"] = work.get("Location", "").astype(str)
    work[TOTAL_COL] = pd.to_numeric(work[TOTAL_COL], errors="coerce").fillna(0)

    total_revenue = float(work[TOTAL_COL].sum())
    avg_revenue = float(work[TOTAL_COL].mean()) if len(work) else 0.0

    def _sum_cols(cols: list[str]) -> float:
        if not all(c in work.columns for c in cols):
            return 0.0
        sub = work[cols].apply(pd.to_numeric, errors="coerce").fillna(0)
        return float(sub.to_numpy().sum())

    voice_revenue = _sum_cols(VOICE_COLS)
    sms_revenue = _sum_cols(SMS_COLS)
    data_revenue = float(pd.to_numeric(work.get(DATA_COL, 0), errors="coerce").fillna(0).sum())

    zero_mask = work[TOTAL_COL] == 0
    zero_revenue_locations = work.loc[zero_mask, "Location"].astype(str).tolist()
    zero_revenue_sites = len(zero_revenue_locations)

    top_10 = work.sort_values(TOTAL_COL, ascending=False).head(10)[["Location", TOTAL_COL]].copy()
    bottom_10 = work.sort_values(TOTAL_COL, ascending=True).head(10)[["Location", TOTAL_COL]].copy()

    concentration_ratio = (float(top_10[TOTAL_COL].sum()) / total_revenue) if total_revenue else 0.0

    top_site_row = work.loc[work[TOTAL_COL].idxmax()] if len(work) else None
    top_site = str(top_site_row["Location"]) if top_site_row is not None else "-"
    top_site_value = float(top_site_row[TOTAL_COL]) if top_site_row is not None else 0.0

    return {
        "total_revenue": total_revenue,
        "avg_revenue": avg_revenue,
        "revenue_mix": {"voice": voice_revenue, "sms": sms_revenue, "data": data_revenue},
        "data_share_pct": (data_revenue / total_revenue * 100.0) if total_revenue else 0.0,
        "zero_revenue_sites": zero_revenue_sites,
        "zero_revenue_locations": zero_revenue_locations,
        "top_site": top_site,
        "top_site_value": top_site_value,
        "top_10_sites": top_10[["Location", TOTAL_COL]],
        "bottom_10_sites": bottom_10[["Location", TOTAL_COL]],
        "concentration_ratio": concentration_ratio,
    }

def calc_mom(current_df: pd.DataFrame, previous_df: pd.DataFrame) -> dict:
    current_total = float(current_df[TOTAL_COL].sum())
    previous_total = float(previous_df[TOTAL_COL].sum())
    delta = current_total - previous_total
    pct_change = (delta / previous_total * 100.0) if previous_total else 0.0
    direction = "up" if delta > 0 else "down" if delta < 0 else "flat"
    return {
        "current_total": current_total,
        "previous_total": previous_total,
        "delta": delta,
        "pct_change": pct_change,
        "direction": direction,
    }

def build_trend_series(month_dfs: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """
    Returns a trend object for board-level use:
    - months: list[str] (chronological)
    - total_revenue: list[float]
    - data_share_pct: list[float]
    - zero_sites: list[int]
    """
    months = list(month_dfs.keys())
    total = []
    data_share = []
    zero_sites = []

    for m in months:
        df = month_dfs[m]
        k = calculate_kpis(df)
        total.append(k["total_revenue"])
        data_share.append(k["data_share_pct"])
        zero_sites.append(k["zero_revenue_sites"])

    return {
        "months": months,
        "total_revenue": total,
        "data_share_pct": data_share,
        "zero_sites": zero_sites,
    }
