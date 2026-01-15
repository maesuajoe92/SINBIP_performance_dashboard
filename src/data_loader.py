import re
import warnings
import pandas as pd
from pathlib import Path
from config import PRIMARY_EXCEL, SHEET22_NAME
from utils import normalize_columns

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

def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = normalize_columns(df.columns)
    for c in df.columns:
        if isinstance(c, str):
            df[c] = pd.to_numeric(df[c], errors="ignore")
    return df

def _read_month_sheet(xls: pd.ExcelFile, sheet_name: str) -> pd.DataFrame:
    # Try multiple header rows (handles title rows)
    for h in range(5):
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="Sparkline Group extension is not supported*",
                category=UserWarning,
            )
            df = pd.read_excel(xls, sheet_name=sheet_name, header=h)
        df.columns = normalize_columns(df.columns)
        if "Location" in df.columns and TOTAL_COL in df.columns:
            return df
    raise ValueError(f"Could not detect header row for sheet: {sheet_name}")

def load_all_months(path: Path = PRIMARY_EXCEL) -> dict:
    """
    Returns:
    {
      'march_2024': DataFrame,
      'april_2024': DataFrame,
      ...
    }
    """
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Sparkline Group extension is not supported*",
            category=UserWarning,
        )
        xls = pd.ExcelFile(path)
    months = {}

    for sheet in xls.sheet_names:
        if sheet.strip().lower() == SHEET22_NAME.lower():
            continue

        df = _read_month_sheet(xls, sheet)
        df = _clean_columns(df)

        # Enforce required structure
        required = ["Location", TOTAL_COL]
        for col in required:
            if col not in df.columns:
                raise ValueError(f"Missing {col} in sheet {sheet}")

        # Ensure numeric
        revenue_cols = VOICE_COLS + SMS_COLS + [DATA_COL, TOTAL_COL]
        for col in revenue_cols:
            if col not in df.columns:
                df[col] = 0
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        df["Location"] = df["Location"].astype(str).str.strip()
        # Drop sheet-level summary/total rows often present at the bottom of Excel sheets
        # These rows are typically labelled like 'Total', 'Totals' or 'Grand Total'
        total_mask = df["Location"].str.lower().str.contains(r"\btotal\b", na=False)
        if total_mask.any():
            df = df[~total_mask].copy()

        # Remove completely empty location rows (blank footers)
        df = df[df["Location"].str.strip() != ""].copy()
        months[sheet] = df

    return months

def load_sheet22(path: Path = PRIMARY_EXCEL) -> pd.DataFrame:
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="Sparkline Group extension is not supported*",
                category=UserWarning,
            )
            df = pd.read_excel(path, sheet_name=SHEET22_NAME)
        df.columns = normalize_columns(df.columns)
        return df
    except Exception:
        return pd.DataFrame()
