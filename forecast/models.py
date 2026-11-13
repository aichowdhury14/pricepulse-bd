"""Forecast models. All return the predicted h-week log change from the origin price.

Baselines (per item, no training):
  naive     0                      random walk: next price = today's price
  drift     h x mean weekly change over the trailing 52 weeks
  seasonal  the change this item made over the same h weeks one year ago
  ses       simple exponential smoothing = ETS(A,N,N); alpha re-chosen at every
            origin from a grid, by one-step error over the trailing 104 weeks

Machine learning:
  GBM       one pooled gradient-boosting model per horizon across all commodities
            (sklearn HistGradientBoostingRegressor), target scaled by each item's
            own volatility. Three flavours:
              gbm         squared-error loss  -> conditional mean
              gbm_median  quantile loss 0.5   -> conditional median (the right target
                          when forecasts are scored by absolute error; Gneiting 2011)
              quantile loss 10% / 90%         -> prediction interval
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from .panel import CATEGORICAL, design_matrix, feature_columns

ALPHAS = np.round(np.arange(0.05, 1.0001, 0.05), 2)
SES_WINDOW = 104


def baseline_changes(lp: pd.DataFrame, h: int) -> dict[str, pd.DataFrame]:
    r1 = lp.diff()
    return {
        "naive": lp * 0.0,
        "drift": r1.rolling(52, min_periods=26).mean() * h,
        "seasonal": lp.shift(52 - h) - lp.shift(52),
        "ses": ses_level(lp) - lp,
    }


def ses_level(lp: pd.DataFrame) -> pd.DataFrame:
    """SES level at each origin, with alpha selected using past errors only."""
    out = {}
    for col in lp:
        y = lp[col].to_numpy()
        n = len(y)
        levels = np.full((len(ALPHAS), n), np.nan)
        sq_err = np.zeros((len(ALPHAS), n))
        for i, a in enumerate(ALPHAS):
            level = np.nan
            for t in range(n):
                if np.isnan(y[t]):
                    levels[i, t] = level
                    continue
                if np.isnan(level):
                    level = y[t]
                else:
                    sq_err[i, t] = (y[t] - level) ** 2
                    level += a * (y[t] - level)
                levels[i, t] = level
        csum = np.cumsum(sq_err, axis=1)
        trailing = csum.copy()
        trailing[:, SES_WINDOW:] -= csum[:, :-SES_WINDOW]
        # ties -> largest alpha (closest to naive): flip so argmin picks the last one
        best = len(ALPHAS) - 1 - np.argmin(trailing[::-1], axis=0)
        out[col] = levels[best, np.arange(n)]
    return pd.DataFrame(out, index=lp.index)


class GBM:
    """Pooled gradient boosting on the volatility-scaled target."""

    PARAMS = dict(max_iter=250, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=40,
                  l2_regularization=1.0, early_stopping=False, random_state=0,
                  categorical_features=CATEGORICAL)

    def __init__(self, quantile: float | None = None):
        if quantile is None:
            self.model = HistGradientBoostingRegressor(loss="squared_error", **self.PARAMS)
        else:
            self.model = HistGradientBoostingRegressor(loss="quantile", quantile=quantile,
                                                       **self.PARAMS)
        self.features: list[str] = []

    def fit(self, train: pd.DataFrame) -> "GBM":
        self.features = feature_columns(train)
        self.model.fit(design_matrix(train, self.features), train["y"] / train["scale"])
        return self

    def predict_scaled(self, rows: pd.DataFrame) -> np.ndarray:
        return self.model.predict(design_matrix(rows, self.features))

    def predict(self, rows: pd.DataFrame) -> np.ndarray:
        return self.predict_scaled(rows) * rows["scale"].to_numpy()
