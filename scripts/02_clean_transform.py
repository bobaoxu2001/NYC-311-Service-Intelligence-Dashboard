"""
02_clean_transform.py
---------------------
Clean and transform the raw monthly 311 CSVs into a single analytical dataset.

Steps
1. Load all data/raw/311_raw_*.csv files.
2. Parse dates, derive calendar features (year, month, week, weekday, hour).
3. Compute resolution time (hours / days) and closure flags (1 / 3 / 7 days).
4. Normalize borough, complaint type, and agency values.
5. Validate coordinates against NYC bounding box and ZIP formats.
6. Remove impossible records (negative resolution time); flag — not delete —
   extreme resolution outliers (> 99th percentile), and add a capped column.
7. Write data/processed/311_clean.parquet and docs/data_quality_report.md.
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
DOCS_DIR = ROOT / "docs"

# NYC bounding box for coordinate validation
LAT_MIN, LAT_MAX = 40.4, 41.05
LON_MIN, LON_MAX = -74.3, -73.6

DTYPES = {
    "unique_key": "string",
    "agency": "string",
    "agency_name": "string",
    "complaint_type": "string",
    "descriptor": "string",
    "incident_zip": "string",
    "city": "string",
    "borough": "string",
    "status": "string",
    "location_type": "string",
    "community_board": "string",
    "council_district": "string",
    "police_precinct": "string",
    "open_data_channel_type": "string",
    "latitude": "float64",
    "longitude": "float64",
}


def load_raw() -> pd.DataFrame:
    files = sorted(RAW_DIR.glob("311_raw_*.csv"))
    if not files:
        raise FileNotFoundError("No raw files found. Run 01_fetch_311_data.py first.")
    print(f"Loading {len(files)} raw monthly files...")
    frames = [
        pd.read_csv(f, dtype=DTYPES, parse_dates=["created_date", "closed_date"])
        for f in files
    ]
    df = pd.concat(frames, ignore_index=True)
    print(f"  {len(df):,} rows loaded")
    return df


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    c = df["created_date"]
    df["created_year"] = c.dt.year
    df["created_month"] = c.dt.to_period("M").astype(str)          # e.g. 2025-07
    df["created_month_name"] = c.dt.month_name()
    df["created_week"] = c.dt.isocalendar().week.astype("Int64")
    df["created_day_of_week"] = c.dt.day_name()
    df["created_hour"] = c.dt.hour
    df["is_weekend"] = c.dt.dayofweek >= 5
    return df


def add_resolution_features(df: pd.DataFrame) -> pd.DataFrame:
    delta = df["closed_date"] - df["created_date"]
    df["resolution_hours"] = delta.dt.total_seconds() / 3600
    df["resolution_days"] = df["resolution_hours"] / 24
    df["is_closed"] = df["status"].str.upper().eq("CLOSED")
    df["closed_within_1_day"] = df["is_closed"] & (df["resolution_days"] <= 1)
    df["closed_within_3_days"] = df["is_closed"] & (df["resolution_days"] <= 3)
    df["closed_within_7_days"] = df["is_closed"] & (df["resolution_days"] <= 7)
    return df


def normalize_categories(df: pd.DataFrame) -> pd.DataFrame:
    # Borough: standardize case, map missing/unspecified to a single label
    borough = df["borough"].str.strip().str.upper()
    borough = borough.replace({"": pd.NA, "UNSPECIFIED": pd.NA})
    df["borough"] = borough.str.title().fillna("Unspecified")

    # Complaint type: collapse case/whitespace variants
    df["complaint_type"] = (
        df["complaint_type"].str.strip().str.title().fillna("Unknown")
    )

    # Agency: uppercase acronym, keep full name alongside
    df["agency"] = df["agency"].str.strip().str.upper().fillna("UNKNOWN")
    df["agency_name"] = df["agency_name"].str.strip().fillna("Unknown")

    # ZIP: keep only valid 5-digit NYC-plausible ZIPs (100xx-119xx)
    zips = df["incident_zip"].str.strip().str.slice(0, 5)
    valid_zip = zips.str.fullmatch(r"1[01]\d{3}", na=False)
    df["incident_zip"] = zips.where(valid_zip)

    df["open_data_channel_type"] = (
        df["open_data_channel_type"].str.strip().str.title().fillna("Unknown")
    )
    return df


def validate_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    in_box = (
        df["latitude"].between(LAT_MIN, LAT_MAX)
        & df["longitude"].between(LON_MIN, LON_MAX)
    )
    df["has_valid_location"] = in_box.fillna(False)
    # Null out coordinates that fall outside NYC so maps stay clean
    df.loc[~df["has_valid_location"], ["latitude", "longitude"]] = np.nan
    return df


def handle_outliers(df: pd.DataFrame, quality: dict) -> pd.DataFrame:
    # Impossible: closed before created -> drop (data entry errors)
    negative = df["resolution_hours"] < 0
    quality["negative_resolution_removed"] = int(negative.sum())
    df = df[~negative].copy()

    # Extreme-but-possible: flag and cap at the 99th percentile, keep the rows
    closed_days = df.loc[df["is_closed"], "resolution_days"].dropna()
    p99 = float(closed_days.quantile(0.99))
    quality["resolution_days_p99"] = round(p99, 2)
    df["is_resolution_outlier"] = df["resolution_days"] > p99
    quality["resolution_outliers_flagged"] = int(df["is_resolution_outlier"].sum())
    df["resolution_days_capped"] = df["resolution_days"].clip(upper=p99)
    return df


def write_quality_report(df: pd.DataFrame, quality: dict) -> None:
    n = len(df)
    lines = [
        "# Data Quality Report",
        "",
        f"Generated by `scripts/02_clean_transform.py` on {pd.Timestamp.now():%Y-%m-%d}.",
        "",
        f"- **Analysis window:** {df['created_date'].min():%Y-%m-%d} to {df['created_date'].max():%Y-%m-%d}",
        f"- **Rows fetched:** {quality['rows_raw']:,}",
        f"- **Rows removed (closed before created — impossible):** {quality['negative_resolution_removed']:,}",
        f"- **Rows in clean dataset:** {n:,}",
        "",
        "## Completeness",
        "",
        "| Check | Count | % of clean rows |",
        "|---|---:|---:|",
    ]

    def pct(x):
        return f"{100 * x / n:.2f}%"

    checks = {
        "Missing / invalid ZIP code": df["incident_zip"].isna().sum(),
        "Missing / out-of-NYC coordinates": (~df["has_valid_location"]).sum(),
        "Borough unspecified": (df["borough"] == "Unspecified").sum(),
        "Missing closed_date (incl. genuinely open)": df["closed_date"].isna().sum(),
        "Open requests (status != Closed)": (~df["is_closed"]).sum(),
        "Missing descriptor": df["descriptor"].isna().sum(),
    }
    for label, count in checks.items():
        lines.append(f"| {label} | {int(count):,} | {pct(int(count))} |")

    lines += [
        "",
        "## Resolution-time outliers",
        "",
        f"- 99th percentile of resolution time (closed requests): **{quality['resolution_days_p99']:.1f} days**",
        f"- Rows flagged as outliers (`is_resolution_outlier`): **{quality['resolution_outliers_flagged']:,}**",
        "- Outliers are **flagged and capped** in `resolution_days_capped`, not deleted.",
        "  Median-based metrics are unaffected; averages use the capped column.",
        "",
        "## Handling decisions",
        "",
        "- Negative resolution times (closed before created) are data-entry errors and were removed.",
        "- ZIPs outside the plausible NYC range (100xx–119xx) or malformed were nulled.",
        "- Coordinates outside the NYC bounding box (lat 40.4–41.05, lon −74.3 to −73.6) were nulled;",
        "  `has_valid_location` records which rows are mappable.",
        "- `Unspecified` borough is retained as its own category so citywide totals stay correct.",
        "- Medians are preferred over means throughout the dashboard because resolution",
        "  time is heavily right-skewed (see p99 above).",
    ]
    out = DOCS_DIR / "data_quality_report.md"
    out.write_text("\n".join(lines))
    print(f"  Quality report -> {out.relative_to(ROOT)}")


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_raw()
    quality = {"rows_raw": len(df)}

    print("Adding time features...")
    df = add_time_features(df)
    print("Adding resolution features...")
    df = add_resolution_features(df)
    print("Normalizing categories...")
    df = normalize_categories(df)
    print("Validating coordinates...")
    df = validate_coordinates(df)
    print("Handling outliers...")
    df = handle_outliers(df, quality)

    out = PROCESSED_DIR / "311_clean.parquet"
    df.to_parquet(out, index=False)
    print(f"  Clean dataset -> {out.relative_to(ROOT)} ({len(df):,} rows)")

    write_quality_report(df, quality)


if __name__ == "__main__":
    main()
