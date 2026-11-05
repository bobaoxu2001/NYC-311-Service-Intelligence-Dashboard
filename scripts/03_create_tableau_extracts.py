"""
03_create_tableau_extracts.py
-----------------------------
Build the Tableau-ready CSVs from the clean dataset, including the composite
Service Pressure Score (SPS) at multiple geographic / categorical levels.

Service Pressure Score
    Each component is min-max normalized to 0-100 within its level, then:
    SPS = 0.4 * norm(request_volume)
        + 0.4 * norm(median_resolution_days)
        + 0.2 * norm(open_rate)

Outputs (data/tableau/):
    311_requests_clean_sample.csv   row-level stratified sample for Tableau Public
    kpi_summary.csv                 headline KPIs (one row)
    borough_summary.csv             per borough + SPS
    zip_summary.csv                 per ZIP + SPS + map centroids
    complaint_type_summary.csv      per complaint type + SPS
    agency_summary.csv              per agency
    monthly_trends.csv              per month
    hourly_weekday_patterns.csv     weekday x hour grid
    borough_complaint_heatmap.csv   borough x complaint type + SPS
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN_PATH = ROOT / "data" / "processed" / "311_clean.parquet"
OUT_DIR = ROOT / "data" / "tableau"

SAMPLE_TARGET = 150_000          # row-level sample size for Tableau Public
MIN_GROUP_SIZE = 200             # ignore tiny groups when scoring pressure
RNG_SEED = 42


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def normalize_0_100(s: pd.Series) -> pd.Series:
    """Min-max normalize a series to 0-100. Constant series -> 0."""
    lo, hi = s.min(), s.max()
    if pd.isna(lo) or hi == lo:
        return pd.Series(0.0, index=s.index)
    return 100 * (s - lo) / (hi - lo)


def add_pressure_score(summary: pd.DataFrame) -> pd.DataFrame:
    """Attach the composite Service Pressure Score to a summary table."""
    summary = summary.copy()
    summary["service_pressure_score"] = (
        0.4 * normalize_0_100(summary["request_count"])
        + 0.4 * normalize_0_100(summary["median_resolution_days"])
        + 0.2 * normalize_0_100(summary["open_rate"])
    ).round(1)
    return summary


def group_summary(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Core aggregation used by every summary table."""
    closed = df[df["is_closed"]]
    g = df.groupby(keys, observed=True)
    out = pd.DataFrame(
        {
            "request_count": g.size(),
            "closed_count": g["is_closed"].sum(),
            "closed_within_1_day": g["closed_within_1_day"].sum(),
            "closed_within_3_days": g["closed_within_3_days"].sum(),
            "closed_within_7_days": g["closed_within_7_days"].sum(),
        }
    )
    out["open_count"] = out["request_count"] - out["closed_count"]
    out["open_rate"] = (out["open_count"] / out["request_count"]).round(4)

    res = closed.groupby(keys, observed=True)["resolution_days"].median()
    avg = closed.groupby(keys, observed=True)["resolution_days_capped"].mean()
    out["median_resolution_days"] = res.round(2)
    out["avg_resolution_days"] = avg.round(2)

    for col in ("closed_within_1_day", "closed_within_3_days", "closed_within_7_days"):
        out[f"pct_{col}"] = (out[col] / out["request_count"]).round(4)

    return out.reset_index()


def top_value(df: pd.DataFrame, keys: list[str], col: str, name: str) -> pd.DataFrame:
    """Most frequent value of `col` within each group (e.g. top complaint type)."""
    counts = df.groupby(keys + [col], observed=True).size().reset_index(name="n")
    idx = counts.groupby(keys, observed=True)["n"].idxmax()
    return counts.loc[idx, keys + [col]].rename(columns={col: name})


def save(df: pd.DataFrame, filename: str) -> None:
    path = OUT_DIR / filename
    df.to_csv(path, index=False)
    print(f"  {filename}: {len(df):,} rows ({path.stat().st_size / 1e6:.1f} MB)")


# ---------------------------------------------------------------------------
# Extract builders
# ---------------------------------------------------------------------------
def build_row_level_sample(df: pd.DataFrame) -> pd.DataFrame:
    """Stratified sample by borough x month so proportions survive sampling."""
    frac = min(1.0, SAMPLE_TARGET / len(df))
    sample = (
        df.groupby(["borough", "created_month"], observed=True, group_keys=False)
        .apply(lambda g: g.sample(frac=frac, random_state=RNG_SEED))
        .reset_index(drop=True)
    )
    cols = [
        "unique_key", "created_date", "closed_date", "created_month",
        "created_month_name", "created_day_of_week", "created_hour", "is_weekend",
        "borough", "incident_zip", "community_board", "council_district",
        "complaint_type", "descriptor", "agency", "agency_name", "status",
        "is_closed", "resolution_days", "resolution_days_capped",
        "is_resolution_outlier", "closed_within_1_day", "closed_within_3_days",
        "closed_within_7_days", "latitude", "longitude", "has_valid_location",
        "open_data_channel_type",
    ]
    return sample[cols]


def build_kpi_summary(df: pd.DataFrame) -> pd.DataFrame:
    closed = df[df["is_closed"]]
    n = len(df)
    return pd.DataFrame(
        [
            {
                "total_requests": n,
                "closed_requests": len(closed),
                "open_requests": n - len(closed),
                "open_rate": round((n - len(closed)) / n, 4),
                "median_resolution_days": round(closed["resolution_days"].median(), 2),
                "avg_resolution_days": round(closed["resolution_days_capped"].mean(), 2),
                "pct_closed_within_1_day": round(df["closed_within_1_day"].sum() / n, 4),
                "pct_closed_within_3_days": round(df["closed_within_3_days"].sum() / n, 4),
                "pct_closed_within_7_days": round(df["closed_within_7_days"].sum() / n, 4),
                "date_range_start": df["created_date"].min().date(),
                "date_range_end": df["created_date"].max().date(),
            }
        ]
    )


def build_borough_summary(df: pd.DataFrame) -> pd.DataFrame:
    out = group_summary(df, ["borough"])
    out = out.merge(
        top_value(df, ["borough"], "complaint_type", "top_complaint_type"),
        on="borough",
    )
    return add_pressure_score(out).sort_values(
        "service_pressure_score", ascending=False
    )


def build_zip_summary(df: pd.DataFrame) -> pd.DataFrame:
    zdf = df[df["incident_zip"].notna()]
    out = group_summary(zdf, ["incident_zip"])
    out = out[out["request_count"] >= MIN_GROUP_SIZE]

    centers = (
        zdf.groupby("incident_zip", observed=True)[["latitude", "longitude"]]
        .median()
        .round(5)
        .rename(columns={"latitude": "latitude_center", "longitude": "longitude_center"})
        .reset_index()
    )
    borough = top_value(zdf, ["incident_zip"], "borough", "borough")
    out = out.merge(centers, on="incident_zip").merge(borough, on="incident_zip")
    out = out.merge(
        top_value(zdf, ["incident_zip"], "complaint_type", "top_complaint_type"),
        on="incident_zip",
    )
    return add_pressure_score(out).sort_values(
        "service_pressure_score", ascending=False
    )


def build_complaint_summary(df: pd.DataFrame) -> pd.DataFrame:
    out = group_summary(df, ["complaint_type"])
    out = out[out["request_count"] >= MIN_GROUP_SIZE]
    out = out.merge(
        top_value(df, ["complaint_type"], "agency", "top_agency"),
        on="complaint_type",
    )
    return add_pressure_score(out).sort_values(
        "service_pressure_score", ascending=False
    )


def build_agency_summary(df: pd.DataFrame) -> pd.DataFrame:
    out = group_summary(df, ["agency", "agency_name"])
    out = out[out["request_count"] >= MIN_GROUP_SIZE]
    out = out.merge(
        top_value(df, ["agency"], "complaint_type", "top_complaint_type"),
        on="agency",
    )
    return add_pressure_score(out).sort_values("request_count", ascending=False)


def build_monthly_trends(df: pd.DataFrame) -> pd.DataFrame:
    out = group_summary(df, ["created_month"])
    out = out.merge(
        top_value(df, ["created_month"], "complaint_type", "top_complaint_type"),
        on="created_month",
    )
    return out.sort_values("created_month")


def build_hourly_weekday(df: pd.DataFrame) -> pd.DataFrame:
    out = group_summary(df, ["created_day_of_week", "created_hour"])
    day_order = [
        "Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday",
    ]
    out["day_number"] = out["created_day_of_week"].map(
        {d: i for i, d in enumerate(day_order, start=1)}
    )
    return out.sort_values(["day_number", "created_hour"])


def build_borough_complaint_heatmap(df: pd.DataFrame) -> pd.DataFrame:
    out = group_summary(df, ["borough", "complaint_type"])
    out = out[out["request_count"] >= MIN_GROUP_SIZE]
    return add_pressure_score(out).sort_values(
        "service_pressure_score", ascending=False
    )


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Loading clean dataset...")
    df = pd.read_parquet(CLEAN_PATH)
    print(f"  {len(df):,} rows\n\nBuilding Tableau extracts:")

    save(build_row_level_sample(df), "311_requests_clean_sample.csv")
    save(build_kpi_summary(df), "kpi_summary.csv")
    save(build_borough_summary(df), "borough_summary.csv")
    save(build_zip_summary(df), "zip_summary.csv")
    save(build_complaint_summary(df), "complaint_type_summary.csv")
    save(build_agency_summary(df), "agency_summary.csv")
    save(build_monthly_trends(df), "monthly_trends.csv")
    save(build_hourly_weekday(df), "hourly_weekday_patterns.csv")
    save(build_borough_complaint_heatmap(df), "borough_complaint_heatmap.csv")

    print("\nAll Tableau extracts written to data/tableau/")


if __name__ == "__main__":
    main()
