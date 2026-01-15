import re
from datetime import datetime
from typing import Any, Dict, Iterable

def safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default

def normalize_columns(cols: Iterable[str]) -> list[str]:
    return [str(c).strip() for c in cols]

def fmt_currency(value: float) -> str:
    return f"${value:,.2f}"

def fmt_pct(value: float) -> str:
    return f"{value:.1f}%"

def choose_latest_two_month_files(files: list) -> tuple:
    # files expected sorted by name or mtime externally; return (prev, curr)
    if len(files) < 2:
        return (None, None)
    return (files[-2], files[-1])


_MONTH_MAP = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}


def parse_month_sheet_name(sheet_name: str) -> datetime | None:
    """
    Supports: mar_24, jul_25, nov_2025, etc.
    Returns datetime(YYYY, MM, 1) for ordering.
    """
    s = str(sheet_name).strip().lower()

    # Format: mon_yy or mon_yyyy (e.g., mar_24, jul_25, nov_2025)
    m = re.match(r"^([a-z]{3,9})[ _\-]+(\d{2}|\d{4})$", s)
    if not m:
        return None

    mon_txt, year_txt = m.group(1), m.group(2)
    mon = _MONTH_MAP.get(mon_txt)
    if not mon:
        return None

    year = int(year_txt)
    if year < 100:
        year += 2000

    return datetime(year, mon, 1)


def sort_month_sheets(sheet_names: list[str]) -> list[str]:
    """
    Sort month sheet names chronologically using parse_month_sheet_name.
    Filters out non-month names (returns only valid month sheets).
    """
    parsed = []
    for name in sheet_names:
        dt = parse_month_sheet_name(name)
        if dt:
            parsed.append((dt, name))
    parsed.sort(key=lambda x: x[0])
    return [name for _, name in parsed]
