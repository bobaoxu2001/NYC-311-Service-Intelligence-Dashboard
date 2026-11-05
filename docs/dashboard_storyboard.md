# Dashboard Storyboard

**Title:** How Fast Does NYC Respond? 311 Service Pressure Across New York City

**Audience:** A city operations executive (or consulting client) who has
10 seconds for the headline, 2 minutes for the "where and what," and wants
recommendations they could act on Monday morning.

**Narrative arc:** *What is happening → Where is it worst → Why (which
complaints, which agencies) → When (patterns) → What to do about it.*

---

## Page 1 — Executive Overview
*"What is the state of 311 service right now?"*

| Element | Content |
|---|---|
| KPI cards (top band) | Total requests · Median resolution days · Open rate · % closed ≤ 3 days · Highest-pressure borough |
| Line chart | Monthly request volume (12 months) — annotate the peak month |
| Bar chart | Top 10 complaint types by volume |
| Insight box | 2–3 sentences, e.g. volume concentration, the summer/winter demand swing, and the headline pressure finding |

Design intent: everything answerable in 10 seconds; no filters on this page
except a global date range.

## Page 2 — Service Pressure Map
*"Where should the city look first?"*

- Filled/symbol map of ZIP codes colored by **Service Pressure Score**
- Tooltip: request count, median resolution days, open rate, top complaint type
- Side ranking table: top 10 highest-pressure ZIPs with borough labels
- Filters: borough, complaint type, agency, date range

Design intent: the map is the hero; ranking table makes it screenshot-able
for a report.

## Page 3 — Complaint Type Diagnostic
*"Is this a volume problem or a speed problem?"*

- **Scatter:** request count (x, log scale advisable) vs median resolution
  days (y) by complaint type; reference lines at the medians create four
  quadrants:
  - High volume / slow → **priority issues**
  - High volume / fast → efficient high-throughput
  - Low volume / slow → complex niche issues
  - Low volume / fast → lower priority
- **Heatmap:** borough × complaint type (color = Service Pressure Score)
- **Bar:** top complaint types by Service Pressure Score

Design intent: this page carries the analytical signature of the project —
separating demand management problems from process problems.

## Page 4 — Agency Performance
*"Who handles the load, and how fast?"*

- Bar: agencies by request volume
- Dot plot: median resolution days by agency (same agency order as the bar
  chart so the eye can compare)
- Table: agency · request count · open rate · % closed ≤ 3 days · top complaint type

Design intent: pair volume with speed side by side; call out the caveat that
complaint mix differs by agency.

## Page 5 — Time Patterns
*"When does demand arrive?"*

- Monthly trend line (seasonality)
- Weekday × hour heatmap (operational staffing view)
- Filter: complaint type (so e.g. heating vs noise seasonality can be compared)
- Callout annotations on the biggest spikes

Design intent: connects analysis to staffing/rostering decisions.

## Page 6 — Recommendations
*"What should the city do?"*

Text-forward consulting page with 5 numbered recommendations (see
`docs/insights_and_recommendations.md`), each tagged with the page that
supports it, plus a short "how to operationalize" line: adopt the Service
Pressure Score as a monthly review metric.

---

## Cross-dashboard design standards

- One accent color for "pressure" (deep red-orange), neutral grays elsewhere;
  colorblind-safe sequential palette on maps/heatmaps.
- Medians labeled as medians everywhere — never let a reader mistake them for means.
- Every page: data source + window footer ("NYC Open Data 311, Jul 2025–Jun 2026").
- Tooltips written as sentences, not field dumps.
- Global date-range filter applied consistently; page-level filters only where listed.
