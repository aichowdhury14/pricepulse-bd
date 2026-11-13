"""Which prices move together, and does the imported variety lead the local one?

* correlation of weekly log changes across the core basket, ordered by hierarchical
  clustering (average linkage on 1 - correlation)
* lead-lag: cross-correlation of weekly changes for imported vs local pairs, plus a
  Granger-causality F-test (does the imported price history improve a forecast of the
  local price beyond the local price's own history?)
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.spatial.distance import squareform

from . import data

PAIRS = [("onion_imported", "onion_local"), ("garlic_imported", "garlic_local"),
         ("ginger_imported", "ginger_local"), ("chili_dry_imported", "chili_dry_local"),
         ("palm_loose", "soybean_loose")]


def weekly_returns(ids: list[str]) -> pd.DataFrame:
    return np.log(data.weekly_wide()[ids]).diff()


def correlation(ids: list[str] | None = None) -> pd.DataFrame:
    ids = ids or data.core_ids()
    r = weekly_returns(ids).dropna(how="all")
    corr = r.corr(min_periods=100)
    dist = squareform(1 - corr.fillna(0).to_numpy(), checks=False)
    order = leaves_list(linkage(dist, "average"))
    return corr.iloc[order, order]


def lead_lag(max_lag: int = 4) -> pd.DataFrame:
    from statsmodels.tsa.stattools import grangercausalitytests
    rows = []
    for lead, follow in PAIRS:
        r = weekly_returns([lead, follow]).dropna()
        ccf = {k: r[lead].shift(k).corr(r[follow]) for k in range(-max_lag, max_lag + 1)}
        best = max(ccf, key=lambda k: ccf[k])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            g = grangercausalitytests(r[[follow, lead]].to_numpy(), maxlag=2)
            g_rev = grangercausalitytests(r[[lead, follow]].to_numpy(), maxlag=2)
        rows.append({
            "leader": lead, "follower": follow, "weeks": len(r),
            "corr_same_week": ccf[0], "corr_leader_1w_earlier": ccf[1],
            "best_lag_weeks": best, "best_corr": ccf[best],
            "granger_p_leader_to_follower": g[2][0]["ssr_ftest"][1],
            "granger_p_follower_to_leader": g_rev[2][0]["ssr_ftest"][1],
        })
    return pd.DataFrame(rows)
