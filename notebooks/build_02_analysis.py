"""Build and execute notebooks/02_analysis.ipynb from the analysis package.

    python -m analysis.run                  # computes results (festival study ~2 min)
    python notebooks/build_02_analysis.py   # writes + executes the notebook

The notebook is generated rather than hand-edited so prose and code stay in one
reviewed place and the executed outputs always match the current data.
"""
from __future__ import annotations

from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient

HERE = Path(__file__).resolve().parent
OUT = HERE / "02_analysis.ipynb"

cells: list = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s.strip()))  # noqa: E731
code = lambda s: cells.append(nbf.v4.new_code_cell(s.strip()))  # noqa: E731

md("""
# PricePulse BD — Stage 2: what the prices say

Dhaka retail prices for 61 essential commodities, May 2020 → today, scraped from the
Trading Corporation of Bangladesh (TCB) daily sheets and cleaned in Stage 1
(see the README for the data audit). This notebook asks five questions:

1. **How much have prices risen, and for what?** — basket index, per-item change
2. **Can the scraped data be trusted?** — comparison with an independent WFP survey
3. **When do prices spike?** — robust anomaly detection, checked against known shocks
4. **Do festivals move prices?** — Ramadan / Eid event study with a placebo test
5. **Which prices move together?** — correlation structure and import→local lead-lag

Heavy results (the festival permutation tests) are precomputed by `python -m analysis.run`
and read from `outputs/`; everything else is computed live below.
""")

code("""
import sys, json
from pathlib import Path
ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(ROOT))

import pandas as pd, numpy as np
from IPython.display import display
from analysis import data, eda, spikes, validate_wfp, comovement, figures
pd.set_option("display.precision", 1)
%matplotlib inline

daily = data.daily_long()
print(f"{len(daily):,} daily observations · {daily.commodity_id.nunique()} commodities · "
      f"{daily.date.min():%d %b %Y} → {daily.date.max():%d %b %Y}")
daily.source.value_counts(normalize=True).mul(100).round(1).rename("% of rows by source")
""")

md("""
## 1. How much have prices risen — and for what?

A Jevons index (geometric mean of price relatives — the standard elementary CPI
formula, indifferent to whether an item is quoted per kg, litre or hali) over the
20-item core basket, base = Bangladesh fiscal year 2020-21.
""")

code("""
idx = eda.basket_index()
by_supply = eda.basket_by_supply()
inf = eda.item_inflation()
test = eda.import_vs_domestic(inf)
print(f"Core basket index, latest complete month: {idx.iloc[-2]:.1f} (FY2020-21 = 100)")
figures.basket(idx, by_supply);
""")

md("""
The two halves of the basket tell different stories. Import-dependent items (wheat
flour, edible oil, sugar, lentils, dates…) climbed steadily through 2022-23 — the
period of the taka's sharp depreciation and the global commodity shock — and **never
came back down**. Domestic items rose later and are much more volatile: they peaked
in late 2024 and fell back as harvests came in.

Is the gap real or an artefact of which items happened to be in each group? Unit =
commodity (pack-size duplicates collapsed), permutation test on mean log change:
""")

code("""
pd.Series(test).to_frame("value")
""")

code("""
figures.inflation_dots(inf, test);
""")

md("""
**Finding 1.** Import-dependent essentials rose a median **~71%** since FY2020-21 versus
**~39%** for domestically produced ones (permutation p ≈ 0.002). Rice — the single
most important item for household budgets — rose only 14-31% depending on grade.

*Caveat:* the import/domestic grouping is a judgement call documented in
`analysis/data.py`; a few items (lentils, turmeric) are mixed-origin. The result is
robust to the rank-based Mann-Whitney test as well.
""")

md("""
## 2. Can the scraped data be trusted?

The World Food Programme runs its own monthly price survey. If the scraper, parser or
backfill were wrong, TCB would drift away from it.
""")

code("""
wsum, wser = validate_wfp.compare()
display(wsum[["months", "level_corr", "change_corr", "median_ratio_tcb_to_wfp"]].round(2))
figures.wfp_validation(wsum, wser);
""")

md("""
**Finding 2.** Price *levels* agree closely (r = 0.85–0.97; median TCB/WFP ratio
0.97–1.03 for eight of nine items). Two honest exceptions: WFP's "wheat flour" sits
~16% above TCB's loose atta from 2023 (likely a different product mix), and
month-to-month *changes* in coarse rice don't correlate — rice barely moves, so its
monthly changes are mostly noise in both surveys.
""")

md("""
## 3. When do prices spike?

For each item and day: the 14-day log change, scored against the item's **own**
trailing year with a robust z-score (median / MAD, so past shocks don't inflate the
baseline). A spike needs z ≥ 3.5 **and** a rise of at least 10%; flagged days within
10 days merge into one episode.

**Validation.** Externally documented supply shocks with exact dates
(`data/reference/known_shocks.csv`) — was each one detected?
""")

code("""
up = spikes.detect("up")
known = spikes.evaluate_known()
print(f"{len(up)} upward spike episodes across {up.commodity_id.nunique()} commodities")
known
""")

md("""
All six evaluable shocks are detected within 0–5 days; the palm/soybean oil episodes
start 1–2 days *before* Indonesia's ban took effect — the market reacted to the
announcement. The September 2020 onion ban falls inside the detector's warm-up period
(it needs ~7 months of history) and is reported as not evaluable rather than counted.
""")

code("""
figures.spike_series("onion_local", up, pd.read_csv(data.REF / "known_shocks.csv"));
""")

code("""
figures.spike_timeline(up, data.core_ids());
""")

code("""
(up[up.commodity_id.isin(data.core_ids())]
   .nlargest(10, "change_14d_pct")
   [["name_en", "start", "end", "change_14d_pct", "price_before", "price_peak"]])
""")

md("""
**Finding 3.** Perishables (onion, garlic, potato, ginger) produce the biggest and most
frequent spikes; rice and bottled oil almost never spike — their prices move in
administered steps or slow drifts.

*Limitations:* (a) the detector is built for *sudden* moves — the autumn-2024 egg price
climb (+15% over 8 weeks, never +10% in 14 days) is not flagged, by design; (b) items
quoted as wide quality ranges (dates: ৳200–450) show step "spikes" when TCB re-bands
the range, which is a reporting change rather than a market move.
""")

md("""
## 4. Do festivals move prices?

For each festival occurrence, the **run-up** = mean log price in the 14 days before
minus the mean 31–60 days before. Prices drift up anyway, so the festival run-up is
compared with the same statistic at every non-festival Thursday (**placebo**), and
tested by permutation (10,000 draws of *k* placebo dates, *k* = festival years).
With ~60 items tested per festival, q-values control the false discovery rate
(Benjamini–Hochberg).
""")

code("""
fest = pd.read_csv(data.OUTPUTS / "festival_effects.csv")
sig = fest[fest.q_value < 0.10].sort_values(["festival", "abnormal_pct"])
sig[["festival", "name_en", "n_years", "runup_pct", "placebo_pct", "abnormal_pct",
     "years_above_placebo", "q_value"]].round(3)
""")

code("""
from analysis.run import EFFECT_ITEMS, RAMADAN_ITEMS
figures.festival_effects(fest, EFFECT_ITEMS);
""")

code("""
figures.festival_paths("ramadan_start", RAMADAN_ITEMS,
                       "Around Ramadan: meat steps up and stays; iftar staples barely move");
""")

md("""
**Finding 4.**

* **Meat, not iftar staples, carries the Ramadan premium.** Beef (+4.9%), goat (+3.4%)
  and chicken (broiler +9.5%, deshi +4.6%) rise beyond the placebo before Ramadan —
  and beef's step *does not reverse* afterwards. Sugar is flat, dates move ~2% and
  chickpea actually gets *cheaper* into and through Ramadan. One plausible explanation
  (not tested here) is that iftar staples are where government action concentrates —
  TCB's subsidised truck sales and pre-Ramadan import duty cuts.
* **Eid-ul-Adha flips chicken.** Broiler falls ~10% in the fortnight before the
  sacrificial Eid (demand shifts to cattle and goats) while deshi chicken and eggs rise.
* **Harvest season masquerades as a festival effect.** Local onion, garlic and potato
  fall sharply before Ramadan/Eid-ul-Fitr — because in 2022-26 those festivals fell in
  Feb–April, exactly the harvest. That is seasonality, not the festival; only a longer
  history (Ramadan cycles through the calendar in ~33 years) can separate the two.

*Also note:* Ramadan and Eid-ul-Fitr are ~30 days apart, so their windows overlap and
the two tests are not independent. Five to seven festival years per test is a small
sample; effects are reported with consistency counts (`years_above_placebo`) for that
reason.
""")

md("""
## 5. Which prices move together?

Correlation of weekly log price changes, ordered by hierarchical clustering.
""")

code("""
corr = comovement.correlation()
figures.correlation_heatmap(corr);
""")

code("""
comovement.lead_lag().round(3)
""")

md("""
**Finding 5.** Prices move in families — the three rice grades (r ≈ 0.5–0.65), edible
oils (0.4–0.6), and a looser "imported staples" group (atta, sugar, palm oil). Beyond
those, week-to-week moves are largely item-specific, which is why per-item spike
detection beats a single basket alarm.

Does the imported variety **lead** the local one? No evidence: imported and local
onion move in the *same* week (r ≈ 0.70), and Granger tests find no predictive power
from imported to local. If anything a few tests point the other way (local → imported,
p ≈ 0.005–0.02), but with ten tests run that is suggestive only.
""")

md("""
## Summary

| # | Question | Answer |
|---|---|---|
| 1 | What got expensive? | Import-dependent essentials: median +71% vs +39% domestic since FY2020-21 (p ≈ 0.002) |
| 2 | Is the data right? | Tracks WFP's independent survey, r = 0.85–0.97 |
| 3 | Spikes? | Detector catches 6/6 documented shocks within 0–5 days; perishables dominate |
| 4 | Festivals? | Ramadan premium is in meat, not iftar staples; Eid-ul-Adha cuts broiler prices |
| 5 | Co-movement? | Families (rice, oils, imported staples); imports don't lead local prices |

**Next (Stage 3):** short-horizon forecasts with honest uncertainty — seasonal-naive,
ETS and gradient-boosting models compared on rolling-origin backtests.
""")

nb = nbf.v4.new_notebook(cells=cells, metadata={
    "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
    "language_info": {"name": "python"},
})
NotebookClient(nb, timeout=900, kernel_name="python3",
               resources={"metadata": {"path": str(HERE)}}).execute()
nbf.write(nb, OUT)
print(f"wrote {OUT.relative_to(HERE.parent)}")
