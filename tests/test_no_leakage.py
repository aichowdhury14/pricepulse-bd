"""Look-ahead test: nothing known at origin t may change when later data is deleted.

Build the modelling panel twice - on the full history and on a copy truncated at a
cut-off Thursday - and require every feature, scale, baseline forecast and interval
quantile at origins <= cut-off to be identical. If any feature peeked at the future,
truncating the future would change it.

    python tests/test_no_leakage.py        (or: pytest tests/)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analysis import data  # noqa: E402
from forecast import backtest as bt  # noqa: E402
from forecast import models, panel  # noqa: E402

CUTOFF = pd.Timestamp("2025-06-26")  # a Thursday, mid-backtest


def _truncated(fn):
    """Run fn with the dataset cut at CUTOFF, then restore the real loader."""
    original = data.daily_long
    full = original()
    data.daily_long = lambda: full[full["date"] <= CUTOFF]
    try:
        return fn()
    finally:
        data.daily_long = original


def _assert_same(a: pd.DataFrame, b: pd.DataFrame, what: str) -> None:
    a, b = a.sort_index(axis=1), b.sort_index(axis=1)
    assert a.shape == b.shape, f"{what}: shape {a.shape} != {b.shape}"
    for col in a.columns:
        x, y = a[col].to_numpy(), b[col].to_numpy()
        if x.dtype.kind in "fiu":
            assert np.allclose(x.astype(float), y.astype(float), equal_nan=True, atol=1e-12), \
                f"{what}: column '{col}' changes when the future is removed"
        else:
            assert (pd.Series(x).astype(str) == pd.Series(y).astype(str)).all(), f"{what}: {col}"


def test_panel_features_use_past_only():
    for h in panel.HORIZONS:
        full = panel.build(h)
        cut = _truncated(lambda: panel.build(h))
        key = ["date", "commodity_id"]
        cols = [c for c in full.columns if c != "y"]
        a = full[full["date"] <= CUTOFF].sort_values(key).reset_index(drop=True)[cols]
        b = cut.sort_values(key).reset_index(drop=True)[cols]
        _assert_same(a, b, f"panel h={h}")
        # targets: identical wherever the truncated panel has one
        yc = cut.sort_values(key).reset_index(drop=True)["y"]
        yf = full[full["date"] <= CUTOFF].sort_values(key).reset_index(drop=True)["y"]
        assert np.allclose(yc[yc.notna()], yf[yc.notna()])
        assert yc[cut.sort_values(key)["date"].to_numpy() > CUTOFF - pd.Timedelta(weeks=h)].isna().all()


def test_baselines_and_empirical_intervals_use_past_only():
    lp_full = panel.weekly_log_prices()
    lp_cut = _truncated(panel.weekly_log_prices)
    for h in panel.HORIZONS:
        f, c = models.baseline_changes(lp_full, h), models.baseline_changes(lp_cut, h)
        for name in f:
            # items first listed after the cut-off don't exist in the truncated copy
            _assert_same(f[name].loc[:CUTOFF, lp_cut.columns], c[name], f"baseline {name} h={h}")
        for qf, qc, name in zip(bt._empirical_quantiles(lp_full, h),
                                bt._empirical_quantiles(lp_cut, h), ("q10", "q90")):
            _assert_same(qf.loc[:CUTOFF, lp_cut.columns], qc, f"empirical {name} h={h}")


def test_training_rows_are_realised_before_refit():
    h = 4
    P = panel.build(h)
    refit = pd.Timestamp("2024-01-04")
    train = P[(P["date"] + pd.Timedelta(weeks=h) <= refit) & P["y"].notna()]
    assert (train["date"] + pd.Timedelta(weeks=h)).max() <= refit


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
