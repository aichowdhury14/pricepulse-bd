# PricePulse BD

**Essential-commodity price intelligence for Bangladesh:** daily Dhaka retail prices for
61 commodities since 2020, with spike detection, Ramadan/Eid effects and short-term
forecasts with uncertainty bands.

> Status: **Stage 2 of 4 complete — data pipeline + analysis.** Forecasting models and the website are next (see roadmap).

## Key findings (May 2020 – Nov 2026)

![Import-dependent vs domestic basket index](reports/figures/01_basket_index.png)

| # | Question | Answer | Method |
|---|---|---|---|
| 1 | What got expensive? | Import-dependent essentials rose a median **+71%** since FY2020-21 vs **+39%** for domestic ones; rice only +14–31% | Jevons index; permutation test p ≈ 0.002 |
| 2 | Is the scraped data right? | Tracks WFP's independent survey, level r = **0.85–0.97** | 9 overlapping commodities |
| 3 | When do prices spike? | Detector catches **6/6** documented shocks (India wheat & onion bans, Indonesia palm ban) within 0–5 days | robust z of 14-day change vs own past year |
| 4 | Do festivals move prices? | Ramadan premium sits in **meat** (beef +4.9%, broiler +9.5%), not iftar staples (sugar flat, chickpea cheaper); broiler **falls ~10%** before Eid-ul-Adha | event study vs placebo dates, BH-FDR |
| 5 | Which prices move together? | Families: rice grades, edible oils, imported staples; imported onion does **not** lead local | clustered correlation, Granger tests |

Full walk-through with caveats: [`notebooks/02_analysis.ipynb`](notebooks/02_analysis.ipynb).

<p>
<img src="reports/figures/07_festival_effects.png" width="49%">
<img src="reports/figures/04_spikes_onion.png" width="49%">
</p>

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

## Analysis

```
analysis/
  data.py          loaders, daily/weekly/monthly panels, import vs domestic grouping
  eda.py           Jevons basket index, per-item inflation, import-vs-domestic test
  validate_wfp.py  TCB vs WFP (independent survey) agreement
  spikes.py        robust spike detector + recall check on known_shocks.csv
  events.py        Ramadan / Eid event study, placebo permutation test, BH-FDR
  comovement.py    clustered correlation, imported -> local lead-lag (Granger)
  figures.py       all charts (validated colour-blind-safe palette)
  run.py           everything -> outputs/*.csv|json (site payloads) + reports/figures
```

```bash
python -m analysis.run                   # ~2 min (festival permutation tests)
python notebooks/build_02_analysis.py    # regenerate + execute the notebook
```

Festival dates (`data/reference/festivals.csv`) are Bangladesh's moon-sighting dates,
which often differ by a day from Saudi Arabia's.

## Roadmap

- [x] **1. Data** — scraper, parser, label mapping, validation, backfill, cleaning
- [x] **2. Analysis** — EDA, spike detection, Ramadan/Eid event study, co-movement
- [ ] **3. Models** — seasonal-naive / ETS / gradient boosting, rolling-origin backtests, prediction intervals
- [ ] **4. Product** — static site on Vercel (Bangla/English), daily GitHub Action refresh, model card

---
Built by Atiqul Islam Chowdhury · Data: TCB (Government of Bangladesh), WFP via HDX
