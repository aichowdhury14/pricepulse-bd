# Model card — PricePulse BD price-range forecast

**What it does.** For each of 53 essential commodities in Dhaka retail markets, it gives
an **80% price range** for 1, 2, 3 and 4 weeks ahead. The central estimate is simply
today's price.

**Version / date.** v1 · trained on data to 12 Nov 2026 · backtest Feb 2023 – Nov 2026.

## Intended use

* Giving households, journalists and small traders a sense of how far a price may
  plausibly move in the coming month.
* **Not for:** trading or procurement decisions, policy evaluation, or any claim about
  *why* a price moved. It does not predict supply shocks.

## Data

Trading Corporation of Bangladesh (TCB) daily retail price sheets, Dhaka, May 2020 –
present: quoted minimum and maximum per item; the model uses the midpoint on Thursdays.
Gaps are back-filled from the sheets' own lagged columns (99.6–99.8% consistent with
the originals). See the README for the data audit.

## Model

| Part | Choice | Why |
|---|---|---|
| Central estimate | Today's price (naive) | No model beat it — see below |
| Range | Gradient-boosted quantile regression (10% / 90%), one pooled model per horizon, target scaled by each item's own volatility | Ranges that widen when an item has been volatile |
| Calibration | Conformalized quantile regression (Romano et al., 2019): range adjusted by the previous 52 weeks of out-of-sample misses | Raw ML ranges were too narrow (74–80% coverage) |

25 features, all known on the forecast day: past price changes (1–52 weeks), distance
from moving averages, recent volatility, weeks since the price last moved, width of
TCB's quoted range, category and basket trends, time of year, days to Ramadan / Eid.
`scikit-learn` `HistGradientBoostingRegressor`, default-ish settings, **not tuned**.

## Evaluation

Rolling-origin backtest: a forecast from every Thursday, models refit every 13 weeks on
data whose outcomes were already known. 39,652 scored forecasts, 57 commodities.

**Point forecasts — mean absolute error relative to naive (1.00 = same as naive)**

| Model | 1 wk | 2 wk | 3 wk | 4 wk |
|---|---|---|---|---|
| **Naive (shipped)** | **1.00** | **1.00** | **1.00** | **1.00** |
| Exponential smoothing | 1.04 | 1.02 | 1.01 | 1.01 |
| Gradient boosting, median | 1.01 | 1.01 | 1.02 | 1.03 |
| Naive + drift | 1.12 | 1.12 | 1.12 | 1.13 |
| Gradient boosting, mean | 1.29 | 1.27 | 1.22 | 1.24 |
| Seasonal naive | 1.83 | 1.73 | 1.67 | 1.63 |

Every alternative is significantly worse than naive (Diebold–Mariano p < 0.001).
Naive's own typical error: 1.5% at 1 week, 3.9% at 4 weeks.

**80% ranges**

| Method | Coverage 1 / 2 / 3 / 4 wk | Interval score at 4 wk (lower = better) |
|---|---|---|
| Item's own past changes | 85.5 / 83.4 / 82.0 / 81.7% | 25.4 |
| ML quantiles, raw | 80.1 / 78.3 / 76.3 / 74.5% | 24.8 |
| **ML + conformal, pooled (shipped)** | **79.6 / 80.8 / 80.1 / 80.6%** ¹ | **24.6** |
| ML + conformal, per item | 79.2 / 80.0 / 79.2 / 78.8% | 26.0 |

The shipped method beats the historical-quantile baseline on interval score at every
horizon (p < 0.05). The improvement is modest: 2–3%.

¹ First release, computed on Windows. The weekly GitHub Actions re-run on Linux gives
78.9 / 80.6 / 80.4 / 80.8% and p ≤ 0.032: same selection, same conclusions (see the
last limitation below).

Selection rules were written into `forecast/run.py` before results were inspected.

## Known limitations

* **Uneven across items.** Coverage is ~80% on average, but at 4 weeks individual
  items range from 65–70% (sugar is lowest in both runs) to 98%. Each item's own
  backtest coverage is published with its forecast.
* **Shocks escape.** Export bans, floods and policy changes cannot be anticipated from
  price history; after such events the actual price is often outside the range.
* **Short history, one city.** Six years of Dhaka data; seasonal patterns are observed
  only five or six times. Results may not transfer to other districts.
* **Quoted ranges, not transactions.** Midpoints of TCB's min–max quotes move in steps.
* **No external drivers.** Exchange rate, world prices, duties and weather are absent.
* **Separate models per horizon.** A 3-week range is not guaranteed to sit inside the
  4-week range.
* **New items** (under ~1 year of history, e.g. lemon, aromatic rice) get no forecast.

* **Not bit-reproducible across machines.** The gradient-boosted quantile models are
  multi-threaded, so floating-point sums happen in a different order on different
  hardware. Re-running on Linux instead of Windows left every point-forecast metric
  within 0.02% and every headline interval metric within 0.7 points, but individual
  items' ranges moved by a median of 0.05 and at most 12 percentage points (potato,
  3 weeks). Per-item ranges are therefore less precise than they look; the backtest
  coverage shown next to each item is the better guide.

## Safeguards

* Look-ahead test: `tests/test_no_leakage.py` rebuilds every feature, baseline and
  interval with the future deleted and requires identical values.
* Thursday point-in-time prices rather than weekly averages, to avoid the spurious
  predictability that averaging creates.

## Reproduce

```bash
python -m forecast.run          # ~8 min: backtest, selection, forecasts, figures
python tests/test_no_leakage.py
```
