# Methodology

## Data source

- **Dataset:** NYC 311 Service Requests from 2010 to Present (NYC Open Data)
- **Socrata dataset ID:** `erm2-nwe9`
- **API:** `https://data.cityofnewyork.us/resource/erm2-nwe9.json` (SODA / Socrata Open Data API)
- **License:** NYC Open Data terms of use; no API key required

## Analysis window

**2025-07-01 to 2026-06-30** — the latest 12 complete months at build time
(≈ 3.89 million requests).

The full 2020-present extract exceeds 20 million rows, which is both slow to
download through the public API and too large for Tableau Public. A rolling
12-month window keeps every season represented, reflects *current* agency
performance (the question a consultant would actually be asked), and keeps
extracts small enough to publish.

## Pipeline

| Step | Script | What it does |
|---|---|---|
| 1. Fetch | `scripts/01_fetch_311_data.py` | Month-by-month download via the Socrata API with `$select` column pruning, `$limit`/`$offset` pagination (100k rows/page), retry with exponential backoff, resumable per-month files |
| 2. Clean | `scripts/02_clean_transform.py` | Date parsing, calendar features, resolution time, closure flags, category normalization, coordinate/ZIP validation, outlier flagging, data quality report |
| 3. Extract | `scripts/03_create_tableau_extracts.py` | 9 Tableau-ready CSVs including the Service Pressure Score at five levels |
| 4. Document | `scripts/04_generate_data_dictionary.py` | Auto-generated data dictionary from the clean dataset |

## Key measurement decisions

### Median over mean for resolution time

Resolution time is heavily right-skewed: a small share of requests stays open
for months and drags the mean far above typical experience. The dashboard
therefore leads with **median resolution days**. The mean is retained for
reference but computed on `resolution_days_capped` (winsorized at the 99th
percentile) so a handful of year-long cases cannot dominate it.

### Closure flags measured against total requests

`% closed within 1/3/7 days` uses **all requests** in the denominator, not just
closed ones. A group that closes 50% of its requests instantly and leaves 50%
open should not look faster than a group that closes 100% within two days.

### Outliers: flag and cap, never silently delete

- Requests closed *before* they were created (negative resolution time) are
  impossible records and are removed; the count is reported in the data
  quality report.
- Requests above the 99th percentile of resolution time are **kept**, flagged
  (`is_resolution_outlier`), and capped in a separate column. Long-running
  cases are real workload, not noise.

### Geographic validation

- Coordinates outside a NYC bounding box (lat 40.4–41.05, lon −74.3 to −73.6)
  are nulled; `has_valid_location` marks mappable rows.
- ZIP codes are kept only if they are valid 5-digit codes in the plausible
  NYC range (100xx–119xx).
- ZIP-level summaries require ≥ 200 requests so scores are not driven by
  tiny-sample noise.

## Service Pressure Score (SPS)

A single 0–100 composite that answers "where should the city look first?"
by combining **how much** demand a unit faces, **how slowly** it resolves it,
and **how much backlog** it carries:

```
SPS = 0.4 × norm(request_volume)
    + 0.4 × norm(median_resolution_days)
    + 0.2 × norm(open_rate)
```

`norm(x)` is min-max normalization to 0–100 *within the level being scored*
(borough, ZIP, complaint type, agency, borough × complaint type).

Weighting rationale: volume and speed are equally important, direct measures
of service pressure; open rate partially overlaps with slow resolution, so it
receives a smaller weight as a backlog signal. The weights are transparent
inputs a stakeholder can challenge and re-run — deliberately simple rather
than a black box.

**Caveat:** because normalization is within-level, scores are comparable
*inside* one table (ZIP vs ZIP) but not *across* tables (a ZIP score vs an
agency score).

## Sampling for the row-level extract

Tableau Public handles aggregate tables easily but slows down on multi-million
row extracts. `311_requests_clean_sample.csv` is a **stratified random sample
(~150k rows, seed 42) proportional to borough × month**, so geographic and
seasonal composition matches the full dataset. All aggregate CSVs are computed
on the **full 3.89M rows**, not the sample — the sample exists only for
row-level drill-down and map dots.

## Limitations

See `docs/insights_and_recommendations.md` for the full list. Headlines:
311 measures *reported* demand, not underlying conditions; closure is not the
same as resolution quality; and agency comparisons partially reflect different
complaint mixes rather than pure performance.
