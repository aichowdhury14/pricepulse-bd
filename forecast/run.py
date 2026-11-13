"""Stage 3 driver: backtest every model, pick what to ship by a fixed rule, forecast.

    python -m forecast.run            # full rolling-origin backtest (~8 min) + forecast
    python -m forecast.run --reuse    # reuse the saved backtest, redo metrics/forecast/figures

Shipping rules (fixed before looking at the results)
  point forecast   ship the best model only if it beats naive on MAE with
                   Diebold-Mariano p < 0.05 at that horizon; otherwise ship naive
  interval         among methods whose pooled coverage is within 80% +/- 3 points at
                   every horizon, the lowest mean interval score

Outputs
  outputs/backtest_predictions.parquet   every out-of-sample forecast
  outputs/backtest_*.csv                 metric tables
  outputs/forecasts.json                 latest 1-4 week forecast per commodity (website)
  reports/figures/09..14_*.png
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from analysis import data, style

from . import backtest as bt
from . import panel
from .models import GBM

PRED_FILE = data.OUTPUTS / "backtest_predictions.parquet"
MIN_SCORED_WEEKS = 52
COVERAGE_TOL = 0.03
KEEP = (["date", "commodity_id", "h", "lp", "y", "scale", "ret_4", "lo_gbm_q_s", "hi_gbm_q_s",
         "cqr", "cqr_item"] + [f"pred_{m}" for m in bt.POINT_MODELS]
        + [f"{s}_{m}" for m in bt.INTERVALS for s in ("lo", "hi")])


def choose_point(point: pd.DataFrame, dm: pd.DataFrame) -> dict[int, str]:
    chosen = {}
    for h, g in point.groupby("h"):
        best = g[g["model"] != "naive"].sort_values("rel_mae").iloc[0]
        p = dm[(dm["h"] == h) & (dm["model"] == best["model"])]["p_value"].iloc[0]
        chosen[int(h)] = best["model"] if (best["rel_mae"] < 1 and p < 0.05) else "naive"
    return chosen


def choose_interval(iv: pd.DataFrame) -> str:
    ok = iv.groupby("method")["coverage"].apply(
        lambda c: ((c - bt.NOMINAL).abs() <= COVERAGE_TOL).all())
    eligible = ok.index[ok].tolist() or iv["method"].unique().tolist()
    score = iv[iv["method"].isin(eligible)].groupby("method")["interval_score_pct"].mean()
    return score.idxmin()


def latest_forecast(R: pd.DataFrame, E: pd.DataFrame, method: str,
                    point_model: dict[int, str]) -> tuple[pd.DataFrame, dict]:
    """Refit the interval models on all realised data and forecast from the last Thursday."""
    rows_out = []
    scored = E.groupby(["h", "commodity_id"]).size()
    for h in panel.HORIZONS:
        P = panel.build(h)
        T = P["date"].max()
        train, now = P[P["y"].notna()], P[P["date"] == T].copy()
        lo, hi = GBM(bt.LO).fit(train), GBM(bt.HI).fit(train)
        a, c = lo.predict_scaled(now), hi.predict_scaled(now)
        now["lo_s"], now["hi_s"] = np.minimum(a, c), np.maximum(a, c)
        corr = R[(R["h"] == h) & (R["date"] == T)].set_index("commodity_id")
        col = {"gbm_q": None, "gbm_cqr": "cqr", "gbm_cqr_item": "cqr_item"}.get(method)
        for r in now.itertuples():
            n = int(scored.get((h, r.commodity_id), 0))
            if n < MIN_SCORED_WEEKS or r.commodity_id not in corr.index:
                continue
            if method == "empirical":
                lo_c, hi_c = corr.loc[r.commodity_id, ["lo_empirical", "hi_empirical"]]
            else:
                q = 0.0 if col is None else float(corr.loc[r.commodity_id, col])
                lo_c, hi_c = (r.lo_s - q) * r.scale, (r.hi_s + q) * r.scale
            price = float(np.exp(r.lp))
            rows_out.append({
                "commodity_id": r.commodity_id, "h": h, "origin": T.date(),
                "target_date": (T + pd.Timedelta(weeks=h)).date(), "price_now": price,
                "point": price,  # naive unless a model earned its place (see choose_point)
                "lo": price * float(np.exp(lo_c)), "hi": price * float(np.exp(hi_c)),
                "lo_pct": float(np.expm1(lo_c) * 100), "hi_pct": float(np.expm1(hi_c) * 100),
                "scored_weeks": n,
            })
    F = pd.DataFrame(rows_out)
    assert all(m == "naive" for m in point_model.values()), \
        "a non-naive point model was selected: wire its prediction into latest_forecast"
    return F, {"origin": str(F["origin"].iloc[0]), "interval_method": method,
               "point_model": point_model, "nominal_coverage": bt.NOMINAL}


def feature_importance(h: int = 4, n_repeats: int = 5) -> pd.DataFrame:
    """Permutation importance of the interval models on the most recent year (held out):
    how much does the pinball loss worsen when one feature is shuffled?"""
    from sklearn.inspection import permutation_importance
    from sklearn.metrics import make_scorer, mean_pinball_loss
    P = panel.build(h)
    P = P[P["y"].notna()]
    cut = P["date"].max() - pd.Timedelta(weeks=52)
    train = P[P["date"] + pd.Timedelta(weeks=h) <= cut]
    test = P[P["date"] > cut]
    out = []
    for q in (bt.LO, bt.HI):
        m = GBM(q).fit(train)
        X, y = panel.design_matrix(test, m.features), test["y"] / test["scale"]
        scorer = make_scorer(mean_pinball_loss, alpha=q, greater_is_better=False)
        base = mean_pinball_loss(y, m.model.predict(X), alpha=q)
        pi = permutation_importance(m.model, X, y, scoring=scorer, n_repeats=n_repeats,
                                    random_state=0)
        out.append(pd.Series(pi.importances_mean / base * 100, index=m.features, name=f"q{q}"))
    imp = pd.concat(out, axis=1)
    imp["loss_increase_pct"] = imp.mean(axis=1)
    return imp.sort_values("loss_increase_pct", ascending=False)


def _records(df: pd.DataFrame, digits: int = 3) -> list[dict]:
    return json.loads(df.round(digits).replace({np.nan: None}).to_json(
        orient="records", date_format="iso"))


def main(reuse: bool = False) -> None:
    out = data.OUTPUTS
    out.mkdir(parents=True, exist_ok=True)
    if reuse and PRED_FILE.exists():
        R = pd.read_parquet(PRED_FILE)
        print(f"reusing {PRED_FILE.name}: {len(R):,} rows")
    else:
        print("rolling-origin backtest ...")
        R = bt.run()[KEEP]
        R.to_parquet(PRED_FILE, index=False)

    E = bt.common_sample(R)
    point = bt.point_metrics(E)
    dm = pd.concat([bt.diebold_mariano(E, m) for m in bt.POINT_MODELS if m != "naive"])
    iv = bt.interval_metrics(E)
    cal = bt.item_calibration(E)
    dmi = pd.concat([bt.dm_interval(E, m) for m in bt.INTERVALS if m != "empirical"])
    items = pd.concat([bt.per_item(E, m).assign(model=m) for m in ("gbm", "gbm_median", "ses")])
    point.to_csv(out / "backtest_point.csv", index=False)
    dm.to_csv(out / "backtest_dm_point.csv", index=False)
    iv.to_csv(out / "backtest_intervals.csv", index=False)
    cal.to_csv(out / "backtest_item_calibration.csv", index=False)
    dmi.to_csv(out / "backtest_dm_intervals.csv", index=False)
    items.to_csv(out / "backtest_per_item.csv", index=False)

    point_model = choose_point(point, dm)
    method = choose_interval(iv)
    print("point model by horizon:", point_model, "| interval method:", method)

    print("latest forecast ...")
    F, meta = latest_forecast(R, E, method, point_model)
    cov = bt.coverage_by_item(E, method).set_index(["h", "commodity_id"])["coverage"]
    F["backtest_coverage"] = [cov.get((r.h, r.commodity_id), np.nan) for r in F.itertuples()]
    F.to_csv(out / "forecasts.csv", index=False)

    print("feature importance ...")
    imp = feature_importance()
    imp.to_csv(out / "forecast_feature_importance.csv")

    c = data.commodities()
    payload = {
        **meta,
        "evaluation": {
            "period": [str(E["date"].min().date()), str(E["date"].max().date())],
            "forecasts_scored": int(len(E)), "commodities": int(E["commodity_id"].nunique()),
            "point": _records(point), "intervals": _records(iv),
        },
        "items": [
            {"commodity_id": cid, "name_en": c.loc[cid, "name_en"], "name_bn": c.loc[cid, "name_bn"],
             "unit": c.loc[cid, "unit"], "category": c.loc[cid, "category"],
             "price_now": round(float(g["price_now"].iloc[0]), 1),
             "horizons": _records(g[["h", "target_date", "lo", "hi", "lo_pct", "hi_pct",
                                     "backtest_coverage"]], 2)}
            for cid, g in F.groupby("commodity_id")
        ],
    }
    (out / "forecasts.json").write_text(json.dumps(payload, indent=1, ensure_ascii=False,
                                                   default=str), encoding="utf-8")

    print("figures ...")
    from . import figures as fg
    style.save(fg.point_skill(point), "09_point_skill")
    style.save(fg.interval_calibration(iv, method), "10_interval_calibration")
    style.save(fg.item_coverage(E, method), "11_item_coverage")
    style.save(fg.backtest_bands(R, method, ["onion_local", "chicken_broiler", "soybean_loose"]),
               "12_backtest_bands")
    style.save(fg.forecast_fan(F, ["rice_coarse", "onion_local", "potato", "eggs",
                                   "chicken_broiler", "soybean_loose"]), "13_forecast_fan")
    style.save(fg.importance(imp), "14_feature_importance")

    pd.set_option("display.width", 200)
    print(point.round(3).to_string(index=False))
    print(iv.round(3).to_string(index=False))
    print(f"published forecasts: {F['commodity_id'].nunique()} commodities x {len(panel.HORIZONS)} horizons")


if __name__ == "__main__":
    main(reuse="--reuse" in sys.argv)
