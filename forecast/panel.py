"""Weekly modelling panel: Thursday prices, features known at the forecast origin.

Target for horizon h (weeks):  y_h(t) = log p(t+h) - log p(t)

Thursday *point-in-time* prices are used, not weekly averages. Averaging a random
walk induces spurious autocorrelation in its changes (Working, 1960), which would
let any model "beat" the naive forecast for free.

Every feature at origin t uses information available on day t only. Calendar
features (week of year, distance to festivals) refer to the target date t+h, which
is known in advance.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from analysis import data

HORIZONS = (1, 2, 3, 4)
RET_LAGS = (1, 2, 4, 8, 13, 26, 52)
MA_WINDOWS = (8, 26, 52)
SCALE_FLOOR = 0.01       # 1% weekly: floor for sticky/administered prices
FEST_CLIP = 90
CATEGORICAL = ["commodity_id", "category", "supply"]


def weekly_log_prices() -> pd.DataFrame:
    w = data.daily_wide()                       # calendar-daily, gaps <= 7d forward-filled
    return np.log(w[w.index.dayofweek == 3])    # Thursdays


def weekly_spread() -> pd.DataFrame:
    """log(max/min) of TCB's quoted range: wide ranges signal quality mix / uncertainty."""
    d = data.daily_long()
    s = np.log(d["price_max"] / d["price_min"])
    w = (d.assign(spread=s).pivot_table(index="date", columns="commodity_id", values="spread")
           .asfreq("D").ffill(limit=7))
    return w[w.index.dayofweek == 3]


def _weeks_since_change(r1: pd.DataFrame) -> pd.DataFrame:
    out = {}
    for c in r1:
        changed = r1[c].abs() > 1e-9
        out[c] = changed.groupby(changed.cumsum()).cumcount().clip(upper=52)
    return pd.DataFrame(out, index=r1.index).where(r1.notna().cumsum() > 0)


def _festival_distance(target: pd.DatetimeIndex) -> pd.DataFrame:
    """Signed days from the nearest occurrence of each festival to the target date."""
    out = {}
    for name, g in data.festivals().groupby("festival"):
        dates = g["date"].to_numpy()
        diff = (target.to_numpy()[:, None] - dates[None, :]) / np.timedelta64(1, "D")
        nearest = diff[np.arange(len(target)), np.abs(diff).argmin(axis=1)]
        out[f"d_{name}"] = np.clip(nearest, -FEST_CLIP, FEST_CLIP)
    return pd.DataFrame(out, index=target)


def scale(lp: pd.DataFrame, h: int) -> pd.DataFrame:
    """Per-item volatility scale so one pooled model can serve onion and milk powder."""
    r1 = lp.diff()
    vol = r1.rolling(52, min_periods=26).std()
    vol = vol.fillna(r1.rolling(13, min_periods=8).std()).fillna(0.03)
    return np.maximum(vol, SCALE_FLOOR) * np.sqrt(h)


def build(h: int) -> pd.DataFrame:
    """Long panel (one row per origin week x commodity) for horizon h."""
    lp = weekly_log_prices()
    r1 = lp.diff()
    c = data.commodities()
    wide: dict[str, pd.DataFrame] = {"lp": lp, "y": lp.shift(-h) - lp, "scale": scale(lp, h)}

    for k in RET_LAGS:
        wide[f"ret_{k}"] = lp - lp.shift(k)
    for k in MA_WINDOWS:
        wide[f"gap_ma_{k}"] = lp - lp.rolling(k, min_periods=k // 2).mean()
    wide["vol_13"] = r1.rolling(13, min_periods=8).std()
    wide["vol_52"] = r1.rolling(52, min_periods=26).std()
    wide["weeks_since_change"] = _weeks_since_change(r1)
    wide["spread"] = weekly_spread().reindex(lp.index)
    # what this item did over the same h-week window one year ago
    wide["seasonal_change"] = lp.shift(52 - h) - lp.shift(52)

    cats = c["category"].reindex(lp.columns)
    ret4 = wide["ret_4"]
    cat_mean = ret4.T.groupby(cats).transform("mean").T
    wide["cat_ret_4"] = cat_mean.where(ret4.notna())
    wide["mkt_ret_4"] = pd.DataFrame(
        np.repeat(ret4.mean(axis=1).to_numpy()[:, None], lp.shape[1], axis=1),
        index=lp.index, columns=lp.columns)

    long = pd.concat({k: v.stack(future_stack=True) for k, v in wide.items()}, axis=1)
    long.index.names = ["date", "commodity_id"]
    long = long.reset_index()
    long = long[long["lp"].notna()]

    target = pd.DatetimeIndex(long["date"]) + pd.Timedelta(weeks=h)
    woy = target.isocalendar().week.to_numpy(dtype=float)
    long["woy_sin"] = np.sin(2 * np.pi * woy / 52.18)
    long["woy_cos"] = np.cos(2 * np.pi * woy / 52.18)
    fest = _festival_distance(target)
    for col in fest:
        long[col] = fest[col].to_numpy()

    long["category"] = long["commodity_id"].map(c["category"])
    long["supply"] = long["commodity_id"].map(c["supply"])
    long["h"] = h
    return long.reset_index(drop=True)


def design_matrix(rows: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    """Model input: categoricals as stable integer codes (fixed category lists, so a
    code means the same commodity at every refit)."""
    c = data.commodities()
    X = rows[features].copy()
    for col in CATEGORICAL:
        levels = sorted(c.index) if col == "commodity_id" else sorted(c[col].unique())
        X[col] = pd.Categorical(X[col].astype(str), categories=levels).codes.astype(float)
    return X


def feature_columns(panel: pd.DataFrame) -> list[str]:
    skip = {"date", "lp", "y", "scale", "h"}
    return [col for col in panel.columns if col not in skip]
