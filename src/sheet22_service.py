import pandas as pd
from typing import Optional, Dict, Any
from .utils import safe_float

def detect_target_total(sheet22: pd.DataFrame) -> Optional[float]:
    """
    Best-effort detection of a target or budget total from Sheet22.
    Looks for columns/rows containing keywords like target/budget/plan.
    Returns a single numeric target total if confidently found.
    """
    if sheet22 is None or sheet22.empty:
        return None

    # Common keyword search
    keywords = {"target", "budget", "plan", "expected"}
    cols = [c for c in sheet22.columns if isinstance(c, str)]
    hit_cols = [c for c in cols if any(k in c.lower() for k in keywords)]

    # If any target-like columns exist, attempt to sum numeric values
    for c in hit_cols:
        series = pd.to_numeric(sheet22[c], errors="coerce").dropna()
        if len(series) == 1:
            return float(series.iloc[0])
        if len(series) > 1:
            # Sometimes the target is a total row; take max as a reasonable heuristic
            return float(series.max())

    # Row-wise scan: any cell containing keyword, then numeric neighbor
    for r in range(min(len(sheet22), 200)):
        for c_idx, c in enumerate(sheet22.columns[: min(len(sheet22.columns), 30)]):
            val = sheet22.iloc[r, c_idx]
            if isinstance(val, str) and any(k in val.lower() for k in keywords):
                # try right neighbor numeric
                if c_idx + 1 < len(sheet22.columns):
                    neighbor = sheet22.iloc[r, c_idx + 1]
                    num = pd.to_numeric(neighbor, errors="coerce")
                    if pd.notna(num):
                        return float(num)

    return None

def detect_control_total(sheet22: pd.DataFrame) -> Optional[float]:
    """
    Best-effort detection of a control/reconciled total from Sheet22.
    Looks for 'total', 'reconcile', 'control'.
    """
    if sheet22 is None or sheet22.empty:
        return None

    keywords = {"total", "reconcile", "control"}
    cols = [c for c in sheet22.columns if isinstance(c, str)]
    hit_cols = [c for c in cols if any(k in c.lower() for k in keywords)]

    for c in hit_cols:
        series = pd.to_numeric(sheet22[c], errors="coerce").dropna()
        if len(series) == 1:
            return float(series.iloc[0])
        if len(series) > 1:
            return float(series.max())

    return None

def build_sheet22_context(sheet22: pd.DataFrame) -> Dict[str, Any]:
    """
    Provide board-safe context derived from Sheet22:
    - target_total (if found)
    - control_total (if found)
    - any obvious counts (sites/active/inactive) if found
    """
    context: Dict[str, Any] = {
        "target_total": None,
        "control_total": None,
        "notes": [],
    }

    if sheet22 is None or sheet22.empty:
        context["notes"].append("Sheet22 not available; proceeding with main sheet only.")
        return context

    target_total = detect_target_total(sheet22)
    control_total = detect_control_total(sheet22)

    context["target_total"] = target_total
    context["control_total"] = control_total

    # Basic count detection
    # Search for cells like "active sites", "inactive sites", "sites"
    keywords = {
        "active": ["active", "in service"],
        "inactive": ["inactive", "down", "not active"],
        "sites": ["sites", "nbip"],
    }

    max_rows = min(len(sheet22), 200)
    max_cols = min(len(sheet22.columns), 30)

    for r in range(max_rows):
        for c in range(max_cols - 1):
            cell = sheet22.iloc[r, c]
            if isinstance(cell, str):
                lower = cell.lower()
                for label, keys in keywords.items():
                    if any(k in lower for k in keys):
                        neighbor = sheet22.iloc[r, c + 1]
                        num = pd.to_numeric(neighbor, errors="coerce")
                        if pd.notna(num):
                            context[label] = safe_float(num)
    return context
