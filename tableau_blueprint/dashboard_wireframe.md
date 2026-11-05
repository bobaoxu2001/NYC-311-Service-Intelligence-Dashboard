# Dashboard Wireframes

ASCII wireframes for each page. Canvas: **1200 × 800 (fixed size)** — renders
predictably on Tableau Public. Margins 16px, inner padding 8px.

Color system
- Accent (pressure/bad): `#C8102E`-family red-orange
- Positive/fast: muted teal `#2A9D8F`
- Neutral text/bars: grays `#4A4A4A` / `#B0B0B0`
- Map/heatmap: sequential orange-red (colorblind-safe)

---

## Page 1 — Executive Overview

```
+----------------------------------------------------------------------+
|  HOW FAST DOES NYC RESPOND?                          [date footer]   |
|  311 Service Pressure Across New York City                           |
+------------+------------+------------+------------+-----------------+
| TOTAL      | MEDIAN     | OPEN RATE  | % CLOSED   | HIGHEST         |
| REQUESTS   | RESOLUTION |            | <= 3 DAYS  | PRESSURE        |
| 3.89M      | X.X days   | XX.X%      | XX%        | BOROUGH: ___    |
+------------+------------+------------+------------+-----------------+
|                                      |                              |
|   MONTHLY REQUEST VOLUME             |   TOP 10 COMPLAINT TYPES     |
|   (line, 12 months,                  |   (horizontal bars,          |
|    peak annotated)                   |    accent on #1)             |
|                                      |                              |
+--------------------------------------+------------------------------+
|  KEY FINDINGS: · finding 1  · finding 2  · finding 3                 |
+----------------------------------------------------------------------+
```

## Page 2 — Service Pressure Map

```
+----------------------------------------------------------------------+
|  WHERE IS SERVICE PRESSURE HIGHEST?           [Borough][Type][Agency]|
+--------------------------------------------------+-------------------+
|                                                  | TOP 10 ZIP CODES  |
|        ZIP-LEVEL MAP                             | BY PRESSURE       |
|        color = Service Pressure Score            | 1. 1XXXX  (Bronx) |
|        (symbol map on lat/lon centers,           | 2. ...            |
|         size = request count)                    | ...               |
|                                                  | 10. ...           |
|  tooltip: requests, median days,                 +-------------------+
|           open rate, top complaint               | SPS legend +      |
|                                                  | formula note      |
+--------------------------------------------------+-------------------+
```

## Page 3 — Complaint Type Diagnostic

```
+----------------------------------------------------------------------+
|  VOLUME PROBLEM OR SPEED PROBLEM?                                    |
+--------------------------------------+-------------------------------+
|  SCATTER: volume (x, log) vs         |  TOP COMPLAINT TYPES BY       |
|  median resolution days (y)          |  SERVICE PRESSURE SCORE       |
|                                      |  (bars)                       |
|   complex niche   |  PRIORITY        |                               |
|   ----------------+---------------   +-------------------------------+
|   lower priority  |  high-throughput |  BOROUGH x COMPLAINT HEATMAP  |
|                                      |  color = SPS                  |
+--------------------------------------+-------------------------------+
```

## Page 4 — Agency Performance

```
+----------------------------------------------------------------------+
|  WHO CARRIES THE WORKLOAD - AND HOW FAST?                            |
+--------------------------------------+-------------------------------+
|  REQUEST VOLUME BY AGENCY            |  MEDIAN RESOLUTION DAYS       |
|  (bars, desc)                        |  (dot plot, same agency order)|
+--------------------------------------+-------------------------------+
|  TABLE: agency | requests | open rate | % <=3 days | top complaint   |
|  (highlight cells: open rate > threshold in accent)                  |
|  caveat footer: complaint mix differs across agencies                |
+----------------------------------------------------------------------+
```

## Page 5 — Time Patterns

```
+----------------------------------------------------------------------+
|  WHEN DOES DEMAND ARRIVE?                        [Complaint filter]  |
+--------------------------------------+-------------------------------+
|  MONTHLY TREND (line, annotated      |  WEEKDAY x HOUR HEATMAP       |
|  seasonal peaks)                     |  rows = Mon..Sun              |
|                                      |  cols = 0..23                 |
|                                      |  color = request count        |
+--------------------------------------+-------------------------------+
|  CALLOUTS: · seasonal spike  · weekday vs weekend  · peak hours      |
+----------------------------------------------------------------------+
```

## Page 6 — Recommendations

```
+----------------------------------------------------------------------+
|  WHAT SHOULD THE CITY DO?                                            |
+----------------------------------------------------------------------+
|  1. Prioritize high-pressure ZIPs ............ (evidence: Page 2)    |
|  2. Split volume problems from speed problems . (evidence: Page 3)   |
|  3. Seasonal staffing for spiking types ....... (evidence: Page 5)   |
|  4. Watch agencies w/ high open rates ......... (evidence: Page 4)   |
|  5. Monthly 311 performance review w/ SPS ..... (method: docs)       |
+----------------------------------------------------------------------+
|  METHOD NOTE: SPS = 0.4·volume + 0.4·median days + 0.2·open rate     |
|  DATA: NYC Open Data 311 (erm2-nwe9), Jul 2025 - Jun 2026            |
+----------------------------------------------------------------------+
```

---

## Layout conventions

- Story points or tabbed dashboard — one dashboard per page, named exactly as
  the page titles above.
- KPI cards: single-value sheets, 20pt bold number, 9pt gray caption.
- All titles are questions — mirrors the consulting narrative.
- Fixed-size dashboards; test on Tableau Public preview before publishing.
