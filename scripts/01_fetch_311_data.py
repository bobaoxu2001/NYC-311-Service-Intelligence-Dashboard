"""
01_fetch_311_data.py
--------------------
Fetch NYC 311 Service Requests from the Socrata Open Data API (dataset erm2-nwe9)
for a 12-month analysis window, using month-by-month chunking with offset
pagination inside each month. Only the columns needed for the analysis are
selected to keep the download manageable.

Output: data/raw/311_raw_YYYY_MM.csv (one file per month)

No API key is required. An app token is optional (set SOCRATA_APP_TOKEN env var
to reduce throttling), but the script works without one.
"""

import os
import sys
import time
from datetime import date
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_URL = "https://data.cityofnewyork.us/resource/erm2-nwe9.csv"

# Analysis window: latest 12 complete months at time of build.
# The full 2020-present dataset is ~40M rows, far too large for Tableau Public,
# so we use a strong representative window (documented in docs/methodology.md).
START_DATE = "2025-07-01T00:00:00"
END_DATE = "2026-06-30T23:59:59"

# Columns confirmed available on the dataset (inspected via the API).
# `intersection_street_1/2` and `incident_address` are intentionally excluded
# to avoid pulling address-level detail we don't need for the dashboard.
COLUMNS = [
    "unique_key",
    "created_date",
    "closed_date",
    "agency",
    "agency_name",
    "complaint_type",
    "descriptor",
    "incident_zip",
    "city",
    "borough",
    "latitude",
    "longitude",
    "status",
    "location_type",
    "community_board",
    "council_district",
    "police_precinct",
    "open_data_channel_type",
]

PAGE_SIZE = 100_000          # rows per request
MAX_RETRIES = 5              # per-request retries with exponential backoff
REQUEST_TIMEOUT = 300        # seconds

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


def month_windows(start: str, end: str):
    """Yield (label, window_start, window_end) for each month in the range."""
    y, m = int(start[:4]), int(start[5:7])
    end_y, end_m = int(end[:4]), int(end[5:7])
    while (y, m) <= (end_y, end_m):
        first = date(y, m, 1)
        if m == 12:
            next_first = date(y + 1, 1, 1)
        else:
            next_first = date(y, m + 1, 1)
        label = f"{y}_{m:02d}"
        yield (
            label,
            f"{first.isoformat()}T00:00:00",
            f"{next_first.isoformat()}T00:00:00",
        )
        y, m = next_first.year, next_first.month


def fetch_page(session: requests.Session, where: str, offset: int) -> str:
    """Fetch one CSV page with retries; returns the response text."""
    params = {
        "$select": ",".join(COLUMNS),
        "$where": where,
        "$order": "unique_key",
        "$limit": PAGE_SIZE,
        "$offset": offset,
    }
    token = os.environ.get("SOCRATA_APP_TOKEN")
    headers = {"X-App-Token": token} if token else {}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = session.get(
                BASE_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT
            )
            if resp.status_code == 200:
                return resp.text
            # 429 = throttled; 5xx = transient server error -> retry
            print(f"    HTTP {resp.status_code}, retry {attempt}/{MAX_RETRIES}")
        except requests.RequestException as exc:
            print(f"    Request error ({exc}), retry {attempt}/{MAX_RETRIES}")
        time.sleep(2 ** attempt)  # 2, 4, 8, 16, 32s backoff
    raise RuntimeError(f"Failed after {MAX_RETRIES} retries (offset={offset})")


def fetch_month(session: requests.Session, label: str, win_start: str, win_end: str):
    """Download all pages for one month into a single CSV file."""
    out_path = RAW_DIR / f"311_raw_{label}.csv"
    if out_path.exists() and out_path.stat().st_size > 1000:
        print(f"  {label}: already downloaded, skipping")
        return

    where = f"created_date >= '{win_start}' AND created_date < '{win_end}'"
    offset = 0
    header_written = False
    tmp_path = out_path.with_suffix(".csv.part")

    with open(tmp_path, "w", encoding="utf-8") as f:
        while True:
            text = fetch_page(session, where, offset)
            lines = text.splitlines(keepends=True)
            if not lines:
                break
            body = lines[1:]  # strip per-page header
            if not header_written:
                f.write(lines[0])
                header_written = True
            f.writelines(body)
            n_rows = len(body)
            print(f"  {label}: offset {offset:>9,} -> {n_rows:,} rows")
            offset += PAGE_SIZE
            if n_rows < PAGE_SIZE:
                break

    tmp_path.rename(out_path)
    print(f"  {label}: done -> {out_path.name}")


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Fetching NYC 311 data: {START_DATE[:10]} to {END_DATE[:10]}")
    print(f"Columns: {len(COLUMNS)} | Page size: {PAGE_SIZE:,}\n")

    session = requests.Session()
    for label, win_start, win_end in month_windows(START_DATE, END_DATE):
        print(f"Month {label}")
        fetch_month(session, label, win_start, win_end)

    total_bytes = sum(p.stat().st_size for p in RAW_DIR.glob("311_raw_*.csv"))
    print(f"\nAll months complete. Raw size: {total_bytes / 1e6:,.0f} MB")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("Interrupted.")
