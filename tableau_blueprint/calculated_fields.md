# Tableau Calculated Fields

Exact formulas to paste into Tableau. Fields marked **(row-level)** are built
on `311_requests_clean_sample.csv`; fields marked **(pre-computed)** already
exist in the summary CSVs and only need formatting.

> Note: most summary metrics (median resolution days, open rate, SPS) are
> **pre-computed in Python on the full 3.89M rows**, which is more accurate
> than recomputing them in Tableau on the 150k-row sample. Use the calculated
> fields below when working from the row-level file (maps, drill-downs), and
> the pre-computed columns for KPI cards and rankings.

---

## Resolution Days (row-level)

```
// Resolution Days
DATEDIFF('hour', [Created Date], [Closed Date]) / 24
```

The CSV already ships a `Resolution Days` column; use this formula only if you
connect to a raw extract instead.

## Is Closed (row-level)

```
// Is Closed
UPPER([Status]) = "CLOSED"
```

## Closed Within 3 Days (row-level)

```
// Closed Within 3 Days
[Is Closed] AND [Resolution Days] <= 3
```

(Variants: replace `3` with `1` or `7`.)

## % Closed Within 3 Days (aggregate, row-level source)

```
// Pct Closed Within 3 Days
SUM(IIF([Closed Within 3 Days], 1, 0)) / COUNT([Unique Key])
```

Format as percentage. Denominator is **all** requests, not just closed ones —
this is deliberate (see docs/methodology.md).

## Open Rate (aggregate, row-level source)

```
// Open Rate
1 - SUM(IIF([Is Closed], 1, 0)) / COUNT([Unique Key])
```

## Median Resolution Days (aggregate, row-level source)

```
// Median Resolution Days (closed only)
MEDIAN(IIF([Is Closed], [Resolution Days], NULL))
```

## Month (row-level)

```
// Month
DATETRUNC('month', [Created Date])
```

## Day of Week (row-level)

```
// Day of Week
DATENAME('weekday', [Created Date])
```

Sort manually Monday→Sunday, or use the shipped `Created Day Of Week` +
`Day Number` columns from `hourly_weekday_patterns.csv`.

## Weekend Flag (row-level)

```
// Weekend Flag
DATEPART('weekday', [Created Date]) = 1 OR DATEPART('weekday', [Created Date]) = 7
```

(Assumes default Sunday=1 week start; the CSV also ships `Is Weekend`.)

## Service Pressure Score (pre-computed — recommended)

Use the `service_pressure_score` column shipped in `borough_summary.csv`,
`zip_summary.csv`, `complaint_type_summary.csv`, and
`borough_complaint_heatmap.csv`. It was computed on the full dataset as:

```
0.4 * norm(request_count) + 0.4 * norm(median_resolution_days) + 0.2 * norm(open_rate)
```

If you must recompute it in Tableau (e.g. to make it respond to filters), use
table calculations — note results will shift with every filter change:

```
// Norm Volume (table calc, compute using the geographic dimension)
100 * (SUM([Request Count]) - WINDOW_MIN(SUM([Request Count])))
    / (WINDOW_MAX(SUM([Request Count])) - WINDOW_MIN(SUM([Request Count])))
```

Repeat for median resolution days and open rate, then:

```
// Service Pressure Score (table calc)
0.4 * [Norm Volume] + 0.4 * [Norm Median Resolution] + 0.2 * [Norm Open Rate]
```

## Complaint Priority Segment (quadrant labels for the scatter)

On `complaint_type_summary.csv`:

```
// Complaint Priority Segment
IF [Request Count] >= [P50 Volume] AND [Median Resolution Days] >= [P50 Resolution]
    THEN "Priority: high volume, slow"
ELSEIF [Request Count] >= [P50 Volume]
    THEN "High throughput: high volume, fast"
ELSEIF [Median Resolution Days] >= [P50 Resolution]
    THEN "Complex niche: low volume, slow"
ELSE "Lower priority: low volume, fast"
END
```

Where `P50 Volume` and `P50 Resolution` are parameters (or level-of-detail
medians):

```
// P50 Volume
{ MEDIAN([Request Count]) }

// P50 Resolution
{ MEDIAN([Median Resolution Days]) }
```

## KPI card labels (formatting helpers)

```
// Median Resolution Label
STR(ROUND(AVG([Median Resolution Days]), 1)) + " days"

// Open Rate Label
STR(ROUND(100 * AVG([Open Rate]), 1)) + "%"
```

(`AVG` over the one-row `kpi_summary.csv` just passes the value through.)
