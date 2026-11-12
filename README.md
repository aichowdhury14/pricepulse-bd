# PricePulse BD

**Essential-commodity price intelligence for Bangladesh:** daily Dhaka retail prices for
61 commodities since 2020, with spike detection, Ramadan/Eid effects and short-term
forecasts with uncertainty bands.

> Status: **Stage 1 of 4 complete — data pipeline.** EDA, models and the website are next (see roadmap).

## Data

| Source | Coverage | Granularity | Notes |
|---|---|---|---|
| [TCB daily retail market price](https://tcb.gov.bd/pages/daily-rmps) | Dhaka, May 2020 – today | daily, min/max | Bangla Excel sheet per working day, scraped |
| [WFP food prices for Bangladesh](https://data.humdata.org/dataset/wfp-food-prices-for-bangladesh) (HDX, CC BY-IGO) | 124 markets, 2004 – 2026 | monthly | district-level view |

### Clean dataset — `data/processed/tcb_daily.csv`

| column | meaning |
|---|---|
| `date`, `commodity_id` | see `data/reference/commodities.csv` for English/Bangla names, unit, category |
| `price_min`, `price_max`, `price_mid` | Taka, per the unit in `commodities.csv` |
| `source` | `report` (that day's sheet) or `backfill_week/month/year` (see below) |

105k rows · 61 commodities · 2020-05-17 → today.

## What it took to get clean data

TCB's archive looks tidy but isn't. Findings from auditing all 1,435 published files:

1. **36 days link to the wrong file.** Every entry from 29 Jan – 8 Mar 2025 (the run-up to
   Ramadan) points to a 2022 comparison sheet; one more file is zero-filled at source.
2. **Gaps recovered from the sheets themselves.** Each report also lists prices 1 week,
   1 month and 1 year earlier. Those lagged values match the original report
   **99.6–99.8%** of the time, so they are used to backfill missing days (closest lag
   wins, every value keeps its `source`). This recovers the whole Ramadan-2025 gap,
   most of 2022 (only 64 reports archived) and adds a year of history (2020).
3. **One product, many labels.** e.g. local garlic appears under 8 spellings over 5 years
   (`রসুন(দেশী) নতুন/পুরাতন)`, …). Variants were verified never to co-occur on the
   same report, then mapped in `data/reference/tcb_item_map.csv`.
4. **Unicode.** `য়`/`ড়` arrive both precomposed and as base + nukta; text is NFC-normalized
   before matching.
5. **Layout drift.** The header row moves, and repeats mid-sheet right before sugar, eggs,
   dates and salt — a naive parser silently drops those (the first version did).
6. **Data-entry typos** (cumin ৳4000 instead of ৳400, rod ৳705,000 instead of ৳70,500,
   swapped min/max) are corrected by explicit rules and logged in
   `data/reference/cleaning_log.csv`. Genuine shocks (Sep 2020 onion export ban) are kept.

Full metrics: `data/reference/quality_report.json`.

## Pipeline

```
pipeline/
  scrape_tcb.py     crawl listing → manifest → download new Excel files (incremental)
  parse_tcb.py      Excel → tidy observations, partitioned by month (incremental)
  make_item_map.py  one-off bootstrap of the label → commodity mapping (CSV is the truth)
  build_dataset.py  map, validate, backfill, clean → tcb_daily.csv + quality report
  fetch_wfp.py      WFP district prices from HDX
  run_all.py        everything above, in order
```

```bash
pip install -r requirements.txt
python pipeline/run_all.py          # daily update (~1 request to TCB when nothing is new)
python pipeline/scrape_tcb.py --full && python pipeline/parse_tcb.py --full   # rebuild from scratch
```

`tcb.gov.bd` serves an incomplete TLS chain; instead of disabling verification the
pipeline ships Sectigo's public intermediate (`pipeline/certs/`).

## Roadmap

- [x] **1. Data** — scraper, parser, label mapping, validation, backfill, cleaning
- [ ] **2. Analysis** — EDA, spike detection, Ramadan/Eid event study, co-movement
- [ ] **3. Models** — seasonal-naive / ETS / gradient boosting, rolling-origin backtests, prediction intervals
- [ ] **4. Product** — static site on Vercel (Bangla/English), daily GitHub Action refresh, model card

---
Built by Atiqul Islam Chowdhury · Data: TCB (Government of Bangladesh), WFP via HDX
