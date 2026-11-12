"""Build the clean daily commodity panel from parsed TCB observations.

Steps
  1. map raw Bangla labels to canonical commodity ids (data/reference/tcb_item_map.csv)
  2. primary series = each report's "today" prices
  3. validate: compare each report's 1-week/1-month/1-year-ago snapshot with the
     original report for that date (how consistent is TCB with itself?)
  4. backfill dates with no report from the lagged snapshots of later reports,
     preferring the closest lag (week > month > year); every value keeps a `source`

Outputs
  data/processed/tcb_daily.csv          date, commodity_id, price_min/max/mid, source
  data/reference/quality_report.json    coverage + self-consistency metrics
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

from parse_tcb import load_observations

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
REF = ROOT / "data" / "reference"

LAG_OFFSET = {"week": pd.DateOffset(days=7), "month": pd.DateOffset(months=1),
              "year": pd.DateOffset(years=1)}
LAG_PRIORITY = {"today": 0, "week": 1, "month": 2, "year": 3}


def load() -> pd.DataFrame:
    obs = load_observations()
    obs["report_date"] = pd.to_datetime(obs["report_date"])
    obs["obs_date"] = pd.to_datetime(obs["obs_date"], errors="coerce")
    m = pd.read_csv(REF / "tcb_item_map.csv").fillna("")
    obs[["item_raw", "unit_raw"]] = obs[["item_raw", "unit_raw"]].fillna("")
    obs = obs.merge(m, on=["item_raw", "unit_raw"], how="left")
    unmapped = obs[obs["commodity_id"].isna()][["item_raw", "unit_raw"]].drop_duplicates()
    if len(unmapped):
        print(f"WARNING: {len(unmapped)} unmapped labels; add them to tcb_item_map.csv:")
        print(unmapped.to_string(index=False))
    obs = obs[obs["commodity_id"].fillna("") != ""].copy()

    # obs_date missing in the header -> derive from report date and lag
    for lag, off in LAG_OFFSET.items():
        sel = (obs["lag"] == lag) & obs["obs_date"].isna()
        obs.loc[sel, "obs_date"] = obs.loc[sel, "report_date"] - off
    sel = (obs["lag"] == "today") & obs["obs_date"].isna()
    obs.loc[sel, "obs_date"] = obs.loc[sel, "report_date"]
    obs["price_mid"] = (obs["price_min"] + obs["price_max"]) / 2
    return obs


def self_consistency(obs: pd.DataFrame, primary: pd.DataFrame) -> dict:
    out = {}
    base = primary.rename(columns={"price_min": "p_min", "price_max": "p_max"})
    for lag in ("week", "month", "year"):
        lagged = obs[obs["lag"] == lag]
        j = lagged.merge(base, left_on=["commodity_id", "obs_date"],
                         right_on=["commodity_id", "date"], how="inner")
        if j.empty:
            continue
        exact = ((j["price_min"] == j["p_min"]) & (j["price_max"] == j["p_max"])).mean()
        mid_err = ((j["price_mid"] - (j["p_min"] + j["p_max"]) / 2).abs()
                   / ((j["p_min"] + j["p_max"]) / 2))
        out[lag] = {"pairs": int(len(j)), "exact_match_rate": round(float(exact), 4),
                    "median_abs_pct_err": round(float(mid_err.median() * 100), 3),
                    "p90_abs_pct_err": round(float(mid_err.quantile(0.9) * 100), 3)}
    return out


def clean(daily: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fix or drop data-entry errors found in TCB's own sheets. Every change is logged.

    1. digit typo   one bound is ~10x the other (cumin max 4000 vs min 320 -> 400)
    2. swapped      price_min > price_max
    3. spike        a single value >45% away from both the 3 obs before and the 3 after,
                    while those neighbours agree within 20% (spike-and-revert = typo;
                    genuine shocks such as the Sep 2020 onion ban persist and are kept)
    """
    d = daily.copy()
    log = []

    lo, hi = d["price_min"], d["price_max"]
    for col, other, fac in (("price_max", "price_min", 0.1), ("price_min", "price_max", 10),
                            ("price_max", "price_min", 10), ("price_min", "price_max", 0.1)):
        fixed = d[col] * fac
        ratio_before = d[[col, other]].max(axis=1) / d[[col, other]].min(axis=1)
        ratio_after = (pd.concat([fixed, d[other]], axis=1).max(axis=1)
                       / pd.concat([fixed, d[other]], axis=1).min(axis=1))
        sel = (ratio_before >= 5) & (ratio_after <= 2.5)
        for _, r in d[sel].iterrows():
            log.append((r["date"], r["commodity_id"], "digit_typo",
                        f"{col} {r[col]:g} -> {r[col] * fac:g}"))
        d.loc[sel, col] = fixed[sel]

    swap = d["price_min"] > d["price_max"]
    for _, r in d[swap].iterrows():
        log.append((r["date"], r["commodity_id"], "swapped_min_max",
                    f"{r['price_min']:g}/{r['price_max']:g}"))
    d.loc[swap, ["price_min", "price_max"]] = d.loc[swap, ["price_max", "price_min"]].values
    d["price_mid"] = (d["price_min"] + d["price_max"]) / 2

    d = d.sort_values(["commodity_id", "date"]).reset_index(drop=True)
    g = d.groupby("commodity_id")["price_mid"]
    before = g.transform(lambda s: s.shift(1).rolling(3, min_periods=2).median())
    after = g.transform(lambda s: s[::-1].shift(1).rolling(3, min_periods=2).median()[::-1])
    spike = (((d["price_mid"] / before - 1).abs() > 0.45)
             & ((d["price_mid"] / after - 1).abs() > 0.45)
             & ((before / after - 1).abs() < 0.20))
    for i, r in d[spike].iterrows():
        log.append((r["date"], r["commodity_id"], "isolated_spike_dropped",
                    f"{r['price_mid']:g} vs neighbours ~{before[i]:g}/{after[i]:g} ({r['source']})"))
    d = d[~spike]

    log = pd.DataFrame(log, columns=["date", "commodity_id", "rule", "detail"])
    return d, log.sort_values(["date", "commodity_id"])


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    obs = load()

    today = obs[obs["lag"] == "today"]
    primary = (today.groupby(["commodity_id", "obs_date"])
                    .agg(price_min=("price_min", "mean"), price_max=("price_max", "mean"),
                         n_reports=("report_date", "nunique"))
                    .reset_index().rename(columns={"obs_date": "date"}))
    primary["source"] = "report"

    consistency = self_consistency(obs, primary)

    have = set(zip(primary["commodity_id"], primary["date"]))
    lagged = obs[obs["lag"] != "today"].copy()
    lagged = lagged[[k not in have for k in zip(lagged["commodity_id"], lagged["obs_date"])]]
    lagged["prio"] = lagged["lag"].map(LAG_PRIORITY)
    best = lagged.groupby(["commodity_id", "obs_date"])["prio"].transform("min")
    lagged = lagged[lagged["prio"] == best]
    backfill = (lagged.groupby(["commodity_id", "obs_date", "lag"])
                      .agg(price_min=("price_min", "median"), price_max=("price_max", "median"),
                           n_reports=("report_date", "nunique"))
                      .reset_index().rename(columns={"obs_date": "date"}))
    backfill["source"] = "backfill_" + backfill.pop("lag")

    daily = pd.concat([primary, backfill], ignore_index=True)
    daily["price_mid"] = (daily["price_min"] + daily["price_max"]) / 2
    daily, cleaning = clean(daily)
    cleaning.to_csv(REF / "cleaning_log.csv", index=False)
    daily = daily.sort_values(["commodity_id", "date"])
    cols = ["date", "commodity_id", "price_min", "price_max", "price_mid", "source", "n_reports"]
    daily[cols].to_csv(PROC / "tcb_daily.csv", index=False, float_format="%.2f")

    # coverage: each calendar date counted once, under its best source
    rank = {"report": 0, "backfill_week": 1, "backfill_month": 2, "backfill_year": 3}
    d = (daily.assign(r=daily["source"].map(rank)).sort_values("r")
              .drop_duplicates("date"))
    cov = (d.assign(year=d["date"].dt.year).groupby(["year", "source"]).size()
            .unstack(fill_value=0))
    report = {
        "generated_from_reports": int(today["report_date"].nunique()),
        "commodities": int(daily["commodity_id"].nunique()),
        "date_range": [str(daily["date"].min().date()), str(daily["date"].max().date())],
        "rows": int(len(daily)),
        "rows_by_source": daily["source"].value_counts().to_dict(),
        "dates_by_year_and_source": {int(y): {k: int(v) for k, v in r.items() if v}
                                     for y, r in cov.iterrows()},
        "self_consistency_vs_original_report": consistency,
        "cleaning_actions": cleaning["rule"].value_counts().to_dict(),
        "parse_failures": pd.read_csv(REF / "tcb_parse_failures.csv")["reason"]
                            .value_counts().to_dict(),
    }
    (REF / "quality_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
