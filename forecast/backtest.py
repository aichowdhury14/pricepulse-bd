"""Rolling-origin backtest: every model forecasts from every Thursday as if it were live.

Protocol
  * origins: every Thursday from FIRST_ORIGIN to the last week with a realised target
  * expanding training window; the GBM is refit every RETRAIN_EVERY weeks using only
    rows whose target was already realised at the refit date (t + h <= refit date)
  * all models are scored on the same rows (common sample)

Prediction intervals (nominal 80%)
  empirical   naive forecast + the item's own 10%/90% quantiles of past h-week changes
              (trailing 104 weeks)
  gbm_q       pooled quantile GBM (conditional: widens when the item is volatile)
  gbm_cqr     gbm_q + conformal correction (Romano et al. 2019): widen/narrow by the
              80% quantile of last year's out-of-sample misses, in volatility units,
              pooled over all commodities
  gbm_cqr_item  same, but each commodity is corrected with its own past misses, so
              coverage holds item by item and not only on average
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import panel
from .models import GBM, baseline_changes

FIRST_ORIGIN = pd.Timestamp("2023-01-05")
RETRAIN_EVERY = 13
NOMINAL = 0.80
LO, HI = 0.10, 0.90
EMP_WINDOW = 104
CQR_WINDOW = 52
POINT_MODELS = ["naive", "drift", "seasonal", "ses", "gbm", "gbm_median"]
INTERVALS = ["empirical", "gbm_q", "gbm_cqr", "gbm_cqr_item"]


def _empirical_quantiles(lp: pd.DataFrame, h: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    realised = lp - lp.shift(h)          # change that completed at row t (known at t)
    roll = realised.rolling(EMP_WINDOW, min_periods=30)
    return roll.quantile(LO), roll.quantile(HI)


def _stack(wide: pd.DataFrame, name: str) -> pd.Series:
    s = wide.stack(future_stack=True)
    s.index.names = ["date", "commodity_id"]
    return s.rename(name)


def run_horizon(h: int, verbose: bool = True) -> pd.DataFrame:
    P = panel.build(h)
    lp = panel.weekly_log_prices()
    step = pd.Timedelta(weeks=h)

    base = baseline_changes(lp, h)
    q_lo, q_hi = _empirical_quantiles(lp, h)
    extra = pd.concat([_stack(v, f"pred_{k}") for k, v in base.items()]
                      + [_stack(q_lo, "lo_empirical"), _stack(q_hi, "hi_empirical")], axis=1)
    P = P.merge(extra.reset_index(), on=["date", "commodity_id"], how="left")

    origins = np.sort(P.loc[P["date"] >= FIRST_ORIGIN, "date"].unique())
    blocks = origins[::RETRAIN_EVERY]
    parts = []
    for i, b in enumerate(blocks):
        end = blocks[i + 1] if i + 1 < len(blocks) else origins[-1] + np.timedelta64(1, "D")
        train = P[(P["date"] + step <= b) & P["y"].notna()]
        test = P[(P["date"] >= b) & (P["date"] < end)].copy()
        mean, med = GBM().fit(train), GBM(0.5).fit(train)
        lo, hi = GBM(LO).fit(train), GBM(HI).fit(train)
        test["pred_gbm"] = mean.predict(test)
        test["pred_gbm_median"] = med.predict(test)
        a, c = lo.predict_scaled(test), hi.predict_scaled(test)
        test["lo_gbm_q_s"], test["hi_gbm_q_s"] = np.minimum(a, c), np.maximum(a, c)
        test["trained_through"] = b
        parts.append(test)
        if verbose:
            print(f"  h={h} refit {pd.Timestamp(b).date()} train={len(train):,} test={len(test):,}",
                  flush=True)
    R = pd.concat(parts, ignore_index=True)
    R["lo_gbm_q"] = R["lo_gbm_q_s"] * R["scale"]
    R["hi_gbm_q"] = R["hi_gbm_q_s"] * R["scale"]
    return conformalise(R, h)


def cqr_correction(R: pd.DataFrame, origin: pd.Timestamp, h: int) -> float:
    """Conformal widening (in volatility units) from misses realised before `origin`."""
    step = pd.Timedelta(weeks=h)
    cal = R[(R["date"] + step <= origin) & (R["date"] > origin - pd.Timedelta(weeks=CQR_WINDOW))
            & R["y"].notna()]
    if len(cal) < 200:
        return np.nan
    ys = cal["y"] / cal["scale"]
    miss = np.maximum(cal["lo_gbm_q_s"] - ys, ys - cal["hi_gbm_q_s"])
    level = min(1.0, NOMINAL * (1 + 1 / len(cal)))
    return float(np.quantile(miss, level))


def item_cqr_correction(R: pd.DataFrame, h: int) -> pd.Series:
    """Per-commodity conformal correction from that item's own misses over the last
    52 weeks. A miss made at origin s is only known at s + h, hence the shift."""
    ys = R["y"] / R["scale"]
    miss = np.maximum(R["lo_gbm_q_s"] - ys, ys - R["hi_gbm_q_s"])
    wide = (R.assign(miss=miss).pivot(index="date", columns="commodity_id", values="miss")
             .asfreq("7D"))
    level = min(1.0, NOMINAL * (1 + 1 / CQR_WINDOW))
    corr = wide.shift(h).rolling(CQR_WINDOW, min_periods=26).quantile(level)
    s = corr.stack(future_stack=True)
    s.index.names = ["date", "commodity_id"]
    return s.rename("cqr_item")


def conformalise(R: pd.DataFrame, h: int) -> pd.DataFrame:
    corr = {d: cqr_correction(R, d, h) for d in np.sort(R["date"].unique())}
    R["cqr"] = R["date"].map(corr)
    R["lo_gbm_cqr"] = (R["lo_gbm_q_s"] - R["cqr"]) * R["scale"]
    R["hi_gbm_cqr"] = (R["hi_gbm_q_s"] + R["cqr"]) * R["scale"]
    R = R.merge(item_cqr_correction(R, h).reset_index(), on=["date", "commodity_id"], how="left")
    R["cqr_item"] = R["cqr_item"].fillna(R["cqr"])     # young items: pooled correction
    R["lo_gbm_cqr_item"] = (R["lo_gbm_q_s"] - R["cqr_item"]) * R["scale"]
    R["hi_gbm_cqr_item"] = (R["hi_gbm_q_s"] + R["cqr_item"]) * R["scale"]
    return R


def run(verbose: bool = True) -> pd.DataFrame:
    return pd.concat([run_horizon(h, verbose) for h in panel.HORIZONS], ignore_index=True)


# ----------------------------------------------------------------------------- metrics

def common_sample(R: pd.DataFrame) -> pd.DataFrame:
    """Rows with a realised target and a forecast from every model and interval method."""
    need = ["y"] + [f"pred_{m}" for m in POINT_MODELS] + \
           [f"{s}_{m}" for m in INTERVALS for s in ("lo", "hi")]
    return R.dropna(subset=need)


def point_metrics(E: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for h, g in E.groupby("h"):
        mae_naive = g["y"].abs().mean()
        rmse_naive = np.sqrt((g["y"] ** 2).mean())
        for m in POINT_MODELS:
            err = g["y"] - g[f"pred_{m}"]
            moved = g["y"].abs() > 1e-9
            called = g[f"pred_{m}"].abs() > 0.005
            rows.append({
                "h": h, "model": m, "n": len(g),
                "mae_pct": err.abs().mean() * 100,
                "rmse_pct": np.sqrt((err ** 2).mean()) * 100,
                "rel_mae": err.abs().mean() / mae_naive,
                "rel_rmse": np.sqrt((err ** 2).mean()) / rmse_naive,
                # of the moves the model called (>0.5%), how often was the direction right?
                "direction_hit": float((np.sign(g[f"pred_{m}"]) == np.sign(g["y"]))[moved & called].mean())
                                 if (moved & called).any() else np.nan,
                "share_called": float(called.mean()),
            })
    return pd.DataFrame(rows)


def diebold_mariano(E: pd.DataFrame, model: str, loss: str = "abs") -> pd.DataFrame:
    """DM test vs naive on the weekly cross-sectional mean loss differential
    (Newey-West variance, h-1 lags). Negative stat = model better than naive."""
    from scipy import stats
    rows = []
    for h, g in E.groupby("h"):
        e_m, e_n = g["y"] - g[f"pred_{model}"], g["y"]
        d = (e_m.abs() - e_n.abs()) if loss == "abs" else (e_m ** 2 - e_n ** 2)
        d = d.groupby(g["date"]).mean().to_numpy()
        n = len(d)
        dc = d - d.mean()
        lrv = np.sum(dc ** 2) / n
        for k in range(1, int(h)):
            lrv += 2 * (1 - k / h) * np.sum(dc[k:] * dc[:-k]) / n
        stat = d.mean() / np.sqrt(max(lrv, 1e-18) / n)
        rows.append({"h": h, "model": model, "loss": loss, "weeks": n, "dm_stat": stat,
                     "p_value": 2 * (1 - stats.norm.cdf(abs(stat)))})
    return pd.DataFrame(rows)


def per_item(E: pd.DataFrame, model: str = "gbm") -> pd.DataFrame:
    g = E.assign(ae_m=(E["y"] - E[f"pred_{model}"]).abs(), ae_n=E["y"].abs())
    out = g.groupby(["h", "commodity_id"]).agg(n=("y", "size"), mae_model=("ae_m", "mean"),
                                               mae_naive=("ae_n", "mean")).reset_index()
    out["rel_mae"] = out["mae_model"] / out["mae_naive"].replace(0, np.nan)
    return out


def interval_metrics(E: pd.DataFrame) -> pd.DataFrame:
    alpha = 1 - NOMINAL
    rows = []
    for h, g in E.groupby("h"):
        for m in INTERVALS:
            lo, hi, y = g[f"lo_{m}"], g[f"hi_{m}"], g["y"]
            score = (hi - lo) + (2 / alpha) * ((lo - y).clip(lower=0) + (y - hi).clip(lower=0))
            rows.append({"h": h, "method": m, "n": len(g),
                         "coverage": float(((y >= lo) & (y <= hi)).mean()),
                         "mean_width_pct": float((hi - lo).mean() * 100),
                         "interval_score_pct": float(score.mean() * 100)})
    return pd.DataFrame(rows)


def coverage_by_item(E: pd.DataFrame, method: str) -> pd.DataFrame:
    ok = (E["y"] >= E[f"lo_{method}"]) & (E["y"] <= E[f"hi_{method}"])
    return ok.groupby([E["h"], E["commodity_id"]]).mean().rename("coverage").reset_index()


def interval_score(E: pd.DataFrame, method: str) -> pd.Series:
    """Winkler / interval score (lower is better): width + penalty for misses."""
    alpha = 1 - NOMINAL
    lo, hi, y = E[f"lo_{method}"], E[f"hi_{method}"], E["y"]
    return (hi - lo) + (2 / alpha) * ((lo - y).clip(lower=0) + (y - hi).clip(lower=0))


def dm_interval(E: pd.DataFrame, method: str, reference: str = "empirical") -> pd.DataFrame:
    """DM test on the interval-score differential (negative = `method` better)."""
    from scipy import stats
    rows = []
    for h, g in E.groupby("h"):
        d = (interval_score(g, method) - interval_score(g, reference)).groupby(g["date"]).mean()
        d = d.to_numpy()
        n = len(d)
        dc = d - d.mean()
        lrv = np.sum(dc ** 2) / n
        for k in range(1, int(h)):
            lrv += 2 * (1 - k / h) * np.sum(dc[k:] * dc[:-k]) / n
        stat = d.mean() / np.sqrt(max(lrv, 1e-18) / n)
        rows.append({"h": h, "method": method, "vs": reference, "weeks": n, "dm_stat": stat,
                     "p_value": 2 * (1 - stats.norm.cdf(abs(stat)))})
    return pd.DataFrame(rows)


def item_calibration(E: pd.DataFrame) -> pd.DataFrame:
    """How evenly is coverage spread across commodities? (items with >= 52 scored weeks)"""
    rows = []
    for m in INTERVALS:
        c = coverage_by_item(E, m).merge(
            E.groupby(["h", "commodity_id"]).size().rename("n").reset_index())
        c = c[c["n"] >= 52]
        for h, g in c.groupby("h"):
            rows.append({"h": h, "method": m, "items": len(g),
                         "median_item_coverage": g["coverage"].median(),
                         "min_item_coverage": g["coverage"].min(),
                         "share_items_70_90": float(g["coverage"].between(0.70, 0.90).mean()),
                         "mean_abs_gap": float((g["coverage"] - NOMINAL).abs().mean())})
    return pd.DataFrame(rows)
