"""Descriptive analysis: basket index, per-item inflation, volatility, import vs domestic."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from . import data

BASE = ("2020-07-01", "2021-06-30")  # Bangladesh fiscal year 2020-21 = 100


def basket_index(ids: list[str] | None = None) -> pd.Series:
    """Monthly Jevons index (geometric mean of price relatives) of the core basket.

    Jevons is the standard elementary-aggregate formula (ILO/IMF CPI manual): it is
    unaffected by the units items are quoted in (kg vs hali vs litre).
    """
    ids = ids or data.core_ids()
    m = data.monthly_wide()[ids]
    rel = m / m.loc[BASE[0]:BASE[1]].mean()
    idx = np.exp(np.log(rel).mean(axis=1, skipna=False)) * 100
    return idx.dropna().rename("core_basket_index")


def latest_window(m: pd.DataFrame, months: int = 3) -> pd.DataFrame:
    """Last `months` complete months (the current month is partial)."""
    last_complete = pd.Timestamp.today().to_period("M").to_timestamp() - pd.offsets.MonthBegin(1)
    return m.loc[:last_complete].iloc[-months:]


def item_inflation() -> pd.DataFrame:
    """% change from FY2020-21 average to the latest 3 complete months, + volatility."""
    m = data.monthly_wide()
    base = m.loc[BASE[0]:BASE[1]].mean()
    base_n = m.loc[BASE[0]:BASE[1]].notna().sum()
    recent = latest_window(m).mean()
    w = data.weekly_wide()
    weekly_ret = np.log(w).diff()
    out = pd.DataFrame({
        "base_price": base, "latest_price": recent,
        "change_pct": (recent / base - 1) * 100,
        "log_change": np.log(recent / base),
        # typical week-to-week move, a robust volatility measure
        "weekly_vol_pct": weekly_ret.abs().median() * 100,
        "weekly_vol_p90_pct": weekly_ret.abs().quantile(0.9) * 100,
    })
    out = out[base_n >= 9].dropna(subset=["change_pct"])  # need most of the base year
    c = data.commodities()
    out = out.join(c[["name_en", "category", "supply", "core"]])
    return out.sort_values("change_pct", ascending=False)


def import_vs_domestic(inf: pd.DataFrame, n_perm: int = 20000, seed: int = 7) -> dict:
    """Do import-dependent items show higher inflation than domestic ones?

    Unit = commodity. Permutation test on the difference in mean log change, plus
    Mann-Whitney as a rank-based check. Pack-size duplicates (soybean 1L/5L, packet vs
    loose flour) are collapsed to one representative so a product isn't counted twice.
    """
    dedup = {"soybean_1l", "soybean_2l", "soybean_5l", "atta_pkt", "maida_pkt",
             "milk_diploma", "milk_fresh", "milk_marks", "palm_super_loose"}
    x = inf[~inf.index.isin(dedup) & inf["supply"].isin(["import-dependent", "domestic"])]
    a = x.loc[x["supply"] == "import-dependent", "log_change"].to_numpy()
    b = x.loc[x["supply"] == "domestic", "log_change"].to_numpy()
    obs = a.mean() - b.mean()
    rng = np.random.default_rng(seed)
    pooled = np.concatenate([a, b])
    perm = np.empty(n_perm)
    for i in range(n_perm):
        rng.shuffle(pooled)
        perm[i] = pooled[: len(a)].mean() - pooled[len(a):].mean()
    p_perm = (np.sum(perm >= obs) + 1) / (n_perm + 1)
    mw = stats.mannwhitneyu(a, b, alternative="greater")
    return {
        "n_import": int(len(a)), "n_domestic": int(len(b)),
        "median_change_import_pct": float(np.expm1(np.median(a)) * 100),
        "median_change_domestic_pct": float(np.expm1(np.median(b)) * 100),
        "mean_log_diff": float(obs),
        "p_permutation_one_sided": float(p_perm),
        "p_mannwhitney_one_sided": float(mw.pvalue),
    }


def basket_by_supply() -> pd.DataFrame:
    """Separate Jevons indices for import-dependent and domestic core items."""
    c = data.commodities()
    core = c[c["core"] == 1]
    return pd.DataFrame({
        g: basket_index(core.index[core["supply"] == g].tolist())
        for g in ("import-dependent", "domestic")
    })
