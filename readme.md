# SINBIP Streamlit Dashboard

## Overview
Board and management views for SINBIP monthly KPI reporting. The app reads the
primary Excel workbook from the data folder and renders KPIs, charts, and an
optional board PDF export.

## Requirements
- Python 3.11+

## Setup
1) Create and activate a virtual environment:
   - Windows:
     python -m venv .venv
     .venv\Scripts\activate

2) Install dependencies:
   pip install -r requirements.txt

3) Put your Excel file at:
   data/SINBIP_MONTHLY_REPORT.xlsx

4) Prepare monthly data as separate sheets inside the primary Excel file
   (e.g., mar_2024, apr_2024). The data/monthly folder is not ingested by the
   app yet.

5) Run:
   streamlit run app/main.py

## Configuration
Set these in .env if needed:
- SINBIP_PRIMARY_EXCEL (path to Excel workbook)
- SINBIP_SHEET22_NAME (default: Sheet22)
- SINBIP_BOARD_USER / SINBIP_BOARD_PASS
- SINBIP_MGMT_USER / SINBIP_MGMT_PASS
- SINBIP_APP_TITLE

## Login (defaults)
- Board:
  username: board
  password: b0@rd!#$
- Management:
  username: manager
  password: m@nag3r!#$

Change passwords via env vars for real deployment.

## Notes
- The app reads all monthly sheets except Sheet22.
- PDF exports are written to the exports/ directory.
