from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MONTHLY_DIR = DATA_DIR / "monthly"
EXPORT_DIR = BASE_DIR / "exports"

EXPORT_DIR.mkdir(exist_ok=True, parents=True)

# Primary monthly Excel file (single snapshot)
PRIMARY_EXCEL = Path(os.getenv("SINBIP_PRIMARY_EXCEL", str(DATA_DIR / "SINBIP_MONTHLY_REPORT_UPDATED.xlsx")))

# Main revenue sheet: by default first sheet (0). You can override if needed.
MAIN_SHEET_NAME = os.getenv("SINBIP_MAIN_SHEET_NAME", "").strip() or None  # None => first sheet

# Sheet22 fixed name in the user's dataset
SHEET22_NAME = os.getenv("SINBIP_SHEET22_NAME", "Sheet22")

# Auth settings (replace in production)
BOARD_USER = os.getenv("SINBIP_BOARD_USER", "board")
BOARD_PASS = os.getenv("SINBIP_BOARD_PASS", "b0@rd!#$")
MGMT_USER = os.getenv("SINBIP_MGMT_USER", "manager")
MGMT_PASS = os.getenv("SINBIP_MGMT_PASS", "m@nag3r!#$")

APP_TITLE = os.getenv("SINBIP_APP_TITLE", "SINBIP Monthly KPI Performance Dashboard")
