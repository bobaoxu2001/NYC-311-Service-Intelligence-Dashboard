# Tableau Build Guide

Step-by-step instructions to build the dashboard in **Tableau Public (free)**
from the files in `data/tableau/`. Estimated build time: 3–5 hours.

## 0. Setup

1. Download **Tableau Public** (free): https://public.tableau.com/en-us/s/download
2. Open Tableau Public → **Connect → Text file** → select
   `data/tableau/311_requests_clean_sample.csv`.
3. Add the remaining CSVs as **separate data sources** (Data → New Data Source):
   `kpi_summary.csv`, `borough_summary.csv`, `zip_summary.csv`,
   `complaint_type_summary.csv`, `agency_summary.csv`, `monthly_trends.csv`,
   `hourly_weekday_patterns.csv`, `borough_complaint_heatmap.csv`.

   > Keep them separate — do NOT join them. Each sheet connects to the source
   > that already has its numbers pre-aggregated on the full 3.89M rows.

4. Data-type checks (click the field-type icons):
   - `incident_zip` → **String → Geographic role → ZIP Code/Postcode**
   - `created_date`, `closed_date` → Date & Time
   - `latitude_center`/`longitude_center` → Number (decimal), assign
     geographic roles Latitude/Longitude
   - `created_month` (in `monthly_trends.csv`) → **Date**
   - rates (`open_rate`, `pct_*`) → Number (decimal); format as % later

## 1. Sheets for Page 1 — Executive Overview

**KPI cards** (source: `kpi_summary.csv`) — one sheet each:
1. Sheet "KPI Total": drag `total_requests` to Text; format → number, custom
   units (M). Title off; add caption text "TOTAL REQUESTS".
2. Repeat for `median_resolution_days` ("X.X days"), `open_rate` (%),
   `pct_closed_within_3_days` (%).
3. Sheet "KPI Pressure Borough" (source: `borough_summary.csv`): filter to
   Top 1 by `service_pressure_score`, drag `borough` to Text.

**Monthly volume line** (source: `monthly_trends.csv`):
- Columns: `created_month` (continuous month) · Rows: `request_count`
- Annotate the max point (right-click point → Annotate → Point).

**Top 10 complaint bar** (source: `complaint_type_summary.csv`):
- Rows: `complaint_type` sorted desc by `request_count`; Columns: `request_count`
- Filter: Top 10 by `request_count`. Color: gray, accent the top bar.

## 2. Sheets for Page 2 — Service Pressure Map

**ZIP pressure map** (source: `zip_summary.csv`):
1. Double-click `incident_zip` (with ZIP geographic role) → filled map; **or**
   for a symbol map drag `longitude_center` → Columns, `latitude_center` → Rows.
2. Color: `service_pressure_score` (orange-red sequential, 3 steps ok).
3. Size (symbol map): `request_count`.
4. Tooltip: request_count, median_resolution_days, open_rate,
   top_complaint_type — write it as a sentence.
5. Filters: `borough` (show filter as dropdown).

**Ranking table**: Rows `incident_zip` + `borough`; Text: score, requests,
median days. Filter Top 10 by `service_pressure_score`.

## 3. Sheets for Page 3 — Complaint Diagnostic

**Scatter** (source: `complaint_type_summary.csv`):
- Columns: `request_count` (axis → logarithmic) · Rows: `median_resolution_days`
- Detail/Label: `complaint_type` (label only min/max/interesting marks)
- Add reference lines: median of each axis (Analytics pane → Reference Line →
  per pane → Median).
- Color: `Complaint Priority Segment` calculated field
  (see `calculated_fields.md`).

**Heatmap** (source: `borough_complaint_heatmap.csv`):
- Columns: `borough` · Rows: `complaint_type` (filter Top 15 by request_count)
- Color: `service_pressure_score`; Marks: Square; Label: score.

**SPS bar** (source: `complaint_type_summary.csv`): Top 10 by
`service_pressure_score`.

## 4. Sheets for Page 4 — Agency Performance

(source: `agency_summary.csv`, filter Top 12 agencies by request_count)
1. Volume bar: `agency` desc by `request_count`.
2. Dot plot: same row order; Columns `median_resolution_days`; Marks: Circle.
   **Tip:** sort both by request_count so rows align across the two charts.
3. Table: `agency`, `request_count`, `open_rate`, `pct_closed_within_3_days`,
   `top_complaint_type`. Use Marks → Square on `open_rate` for cell shading.

## 5. Sheets for Page 5 — Time Patterns

**Trend line**: reuse the Page 1 monthly line (duplicate sheet).

**Weekday × hour heatmap** (source: `hourly_weekday_patterns.csv`):
- Columns: `created_hour` · Rows: `created_day_of_week`
  (sort by the `day_number` field: Rows → Sort → by field `day_number` asc)
- Color: `request_count`; Marks: Square.
- Optional second version colored by `median_resolution_days`.

## 6. Assemble dashboards

1. New Dashboard → Size: **Fixed 1200 × 800**.
2. Build the six pages following `dashboard_wireframe.md` layouts.
3. Add text objects for titles (questions!), insight boxes, and the footer:
   *"Source: NYC Open Data — 311 Service Requests (erm2-nwe9), Jul 2025–Jun 2026.
   Medians used throughout; see methodology."*
4. Dashboard → Actions: add a **Filter action** from the map to the ranking
   table (hover) if desired.
5. Right-click each sheet title → hide; use dashboard text objects instead
   (more control).

## 7. Publish

1. File → Save to Tableau Public As… → title:
   **"How Fast Does NYC Respond? 311 Service Pressure Across New York City"**
2. In the published view settings: enable tabs, set the Executive Overview
   as the default tab.
3. Copy the public URL into `README.md` (placeholder is waiting) and into
   your Data School application.

## Gotchas

- If ZIP filled maps show gaps, switch to the symbol map (lat/lon centers
  ship in `zip_summary.csv` for exactly this reason).
- Tableau Public requires all data extracted — CSVs handle this automatically.
- Keep total workbook size under ~15 MB for snappy loading; the shipped CSVs
  are sized for this.
- If `created_month` parses as string, split it (Custom Split on "-") or set
  the date parse format to `yyyy-MM`.
