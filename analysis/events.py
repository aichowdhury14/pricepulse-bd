"""Festival event study: do prices rise before Ramadan and the two Eids?

Statistic for one festival occurrence at date t0 (log points ~ %):
    run_up(t0) = mean log p over [t0-14, t0-1]  -  mean log p over [t0-60, t0-31]
i.e. how much higher prices are in the fortnight before the festival than a month
earlier. Prices drift up with inflation anyway, so the raw run-up is compared with a
placebo distribution: the same statistic at every Thursday whose window does not
overlap any festival window. Because Ramadan moves ~11 days earlier each year, the
placebo also absorbs part of the calendar seasonality (harvest cycles) - but not all
of it, which is stated as a limitation.

Inference: permutation test - draw k placebo dates (k = number of festival years)
10,000 times and see how often their mean run-up is as extreme as the festival's.
Benjamini-Hochberg FDR across commodities within each festival (many items tested).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import data

PRE = (-60, -31)
RUN = (-14, -1)
MIN_COVERAGE = 0.7
N_PERM = 10000
FESTIVAL_LABELS = {"ramadan_start": "Ramadan", "eid_ul_fitr": "Eid-ul-Fitr",
                   "eid_ul_adha": "Eid-ul-Adha"}


def _window_mean(lp: pd.Series, t0: pd.Timestamp, lo: int, hi: int) -> float:
    seg = lp.loc[t0 + pd.Timedelta(days=lo): t0 + pd.Timedelta(days=hi)]
    need = (hi - lo + 1) * MIN_COVERAGE
    return seg.mean() if seg.notna().sum() >= need else np.nan


def run_up(lp: pd.Series, dates) -> np.ndarray:
    return np.array([_window_mean(lp, t, *RUN) - _window_mean(lp, t, *PRE) for t in dates])


def placebo_dates(lp_index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    fest = data.festivals()["date"]
    cand = pd.date_range(lp_index.min() + pd.Timedelta(days=-PRE[0]),
                         lp_index.max(), freq="W-THU")
    keep = []
    for t in cand:
        # candidate window [t-60, t] must not overlap any festival window [f-60, f+14]
        overlap = ((t + pd.Timedelta(days=PRE[0]) <= fest + pd.Timedelta(days=14))
                   & (t >= fest + pd.Timedelta(days=PRE[0]))).any()
        if not overlap:
            keep.append(t)
    return pd.DatetimeIndex(keep)


def bh(p: np.ndarray) -> np.ndarray:
    """Benjamini-Hochberg adjusted q-values."""
    p = np.asarray(p, float)
    n = np.sum(~np.isnan(p))
    order = np.argsort(np.where(np.isnan(p), np.inf, p))
    q = np.full_like(p, np.nan)
    prev = 1.0
    for rank in range(n, 0, -1):
        i = order[rank - 1]
        prev = min(prev, p[i] * n / rank)
        q[i] = prev
    return q


def study(seed: int = 11) -> pd.DataFrame:
    w = np.log(data.daily_wide())
    fest = data.festivals()
    placebo = placebo_dates(w.index)
    rng = np.random.default_rng(seed)
    rows = []
    for fname, label in FESTIVAL_LABELS.items():
        t0s = fest.loc[fest["festival"] == fname, "date"]
        for cid in w.columns:
            lp = w[cid]
            obs = run_up(lp, t0s)
            years = t0s[~np.isnan(obs)].dt.year.tolist()
            obs = obs[~np.isnan(obs)]
            pl = run_up(lp, placebo)
            pl = pl[~np.isnan(pl)]
            k = len(obs)
            if k < 4 or len(pl) < 30:
                continue
            draws = np.array([rng.choice(pl, k, replace=False).mean() for _ in range(N_PERM)])
            effect = obs.mean() - pl.mean()
            centred = draws - pl.mean()
            p = (np.sum(np.abs(centred) >= abs(effect)) + 1) / (N_PERM + 1)
            rows.append({
                "festival": label, "commodity_id": cid, "n_years": k,
                "years": ",".join(map(str, years)),
                "runup_pct": float(np.expm1(obs.mean()) * 100),
                "placebo_pct": float(np.expm1(pl.mean()) * 100),
                "abnormal_pct": float(np.expm1(effect) * 100),
                "years_above_placebo": int(np.sum(obs > np.median(pl))),
                "p_value": float(p),
            })
    res = pd.DataFrame(rows)
    res["q_value"] = np.nan
    for f in res["festival"].unique():
        sel = res["festival"] == f
        res.loc[sel, "q_value"] = bh(res.loc[sel, "p_value"].to_numpy())
    res.insert(2, "name_en", res["commodity_id"].map(data.commodities()["name_en"]))
    return res.sort_values(["festival", "p_value"]).reset_index(drop=True)


def event_paths(cid: str, festival: str = "ramadan_start",
                lo: int = -60, hi: int = 30) -> pd.DataFrame:
    """Price path around each occurrence, as % vs the PRE-window mean (for charts)."""
    lp = np.log(data.daily_wide()[cid])
    out = {}
    for t0 in data.festivals().query("festival == @festival")["date"]:
        base = _window_mean(lp, t0, *PRE)
        seg = lp.loc[t0 + pd.Timedelta(days=lo): t0 + pd.Timedelta(days=hi)]
        if np.isnan(base) or seg.notna().sum() < (hi - lo) * 0.6:
            continue
        seg.index = (seg.index - t0).days
        out[t0.year] = np.expm1(seg - base) * 100
    return pd.DataFrame(out)
