# NYC 311 Service Intelligence

A local Python pipeline for downloading NYC 311 requests, cleaning them and
preparing Tableau-friendly extracts. This is distinct from the Fabric-oriented
`nyc-311-service-intelligence-platform` project.

## Reproduce

Use Python 3.11 and `requirements.txt`, then run the numbered scripts in
`scripts/` in order. Read their date ranges and output paths before downloading.
Raw downloads and full processed datasets are intentionally ignored; the
repository keeps code, documentation and compact Tableau aggregates.

Source syntax has been checked. The full download/ETL pipeline and a native
Tableau workbook were not rerun or verified during the 2026-11-05 review.
