"""Figures for the Stage 3 report (same house style as analysis/figures.py)."""
from __future__ import annotations

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis import data, style
from analysis.style import CONTEXT, INK_2, SERIES

from . import backtest as bt
from . import panel

style.apply()

MODEL_LABEL = {"naive": "Naive (today's price)", "ses": "Exponential smoothing (ETS)",
               "gbm_median": "Gradient boosting, median", "drift": "Naive + drift",
               "gbm": "Gradient boosting, mean", "seasonal": "Seasonal naive"}
METHOD_LABEL = {"empirical": "Item's own past changes", "gbm_q": "ML quantiles, raw",
                "gbm_cqr": "ML + conformal (pooled)", "gbm_cqr_item": "ML + conformal (per item)"}
METHOD_COLOR = dict(zip(METHOD_LABEL, SERIES))  # colour follows the method everywhere
FEATURE_LABEL = {
    "vol_13": "Volatility, last 13 weeks", "vol_52": "Volatility, last 52 weeks",
    "spread": "Width of TCB's quoted min-max range", "commodity_id": "Which commodity",
    "weeks_since_change": "Weeks since the price last moved", "category": "Category",
    "gap_ma_8": "Price vs its 8-week average", "gap_ma_26": "Price vs its 26-week average",
    "gap_ma_52": "Price vs its 52-week average", "seasonal_change": "Same weeks last year",
    "cat_ret_4": "Category trend, 4 weeks", "mkt_ret_4": "Whole-basket trend, 4 weeks",
    "woy_sin": "Time of year (sin)", "woy_cos": "Time of year (cos)",
    "d_ramadan_start": "Days to/from Ramadan", "d_eid_ul_fitr": "Days to/from Eid-ul-Fitr",
    "d_eid_ul_adha": "Days to/from Eid-ul-Adha", "supply": "Import-dependent or domestic",
    **{f"ret_{k}": f"Price change, last {k} week{'s' if k > 1 else ''}" for k in panel.RET_LAGS},
}


def point_skill(point: pd.DataFrame) -> plt.Figure:
    order = ["ses", "gbm_median", "drift", "gbm", "seasonal"]
    fig, axes = plt.subplots(1, 4, figsize=(10, 2.9), sharey=True, sharex=True)
    y = np.arange(len(order))
    xmax = (point["rel_mae"].max() - 1) * 100 * 1.22
    for ax, h in zip(axes, sorted(point["h"].unique())):
        g = point[point["h"] == h].set_index("model").reindex(order)
        x = (g["rel_mae"] - 1) * 100
        ax.hlines(y, 0, x, color=SERIES[0], lw=1.2, alpha=0.5)
        ax.scatter(x, y, s=40, color=SERIES[0], edgecolor=style.SURFACE, linewidth=1.5, zorder=3)
        for xi, yi in zip(x, y):
            ax.annotate(f"+{xi:.0f}%" if xi >= 0.5 else f"{xi:+.1f}%", (xi, yi), xytext=(6, 0),
                        textcoords="offset points", va="center", fontsize=8, color=INK_2)
        ax.axvline(0, color=INK_2, lw=1)
        ax.set_title(f"{h} week{'s' if h > 1 else ''} ahead", fontsize=10)
        ax.grid(axis="y", visible=False)
        ax.set_xlim(-6, xmax)
    axes[0].set_yticks(y, [MODEL_LABEL[m] for m in order], fontsize=9)
    axes[0].invert_yaxis()
    fig.supxlabel("Mean absolute error vs the naive forecast (0 = same, right = worse)",
                  fontsize=9, color=INK_2)
    fig.suptitle("No model beats \"the price stays where it is\" at any horizon",
                 x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.tight_layout()
    return fig


def interval_calibration(iv: pd.DataFrame, chosen: str) -> plt.Figure:
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    for m in bt.INTERVALS:
        g = iv[iv["method"] == m].sort_values("h")
        lw = 2.6 if m == chosen else 1.6
        axes[0].plot(g["h"], g["coverage"] * 100, marker="o", ms=5, lw=lw,
                     color=METHOD_COLOR[m], label=METHOD_LABEL[m] + ("  (shipped)" if m == chosen else ""))
        axes[1].plot(g["h"], g["interval_score_pct"], marker="o", ms=5, lw=lw, color=METHOD_COLOR[m])
    axes[0].axhline(bt.NOMINAL * 100, color=INK_2, lw=1)
    axes[0].set_title("Share of actual prices inside the 80% range (dark line = target)",
                      fontsize=10)
    axes[0].set_ylabel("Coverage (%)")
    axes[1].set_title("Interval score (width + penalty for misses; lower is better)", fontsize=10)
    axes[1].set_ylabel("Score (% of price)")
    for ax in axes:
        ax.set_xticks([1, 2, 3, 4])
        ax.set_xlabel("Weeks ahead")
    fig.suptitle("Raw ML ranges are too narrow; the conformal step fixes that",
                 x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.tight_layout(rect=(0, 0.1, 1, 0.97))
    fig.legend(*axes[0].get_legend_handles_labels(), loc="lower center", ncol=4, fontsize=8.5)
    return fig


def item_coverage(E: pd.DataFrame, chosen: str, h: int = 4) -> plt.Figure:
    n = E[E["h"] == h].groupby("commodity_id").size()
    keep = n.index[n >= 52]
    fig, ax = plt.subplots(figsize=(9, 3.4))
    rng = np.random.default_rng(3)
    for i, m in enumerate(bt.INTERVALS):
        c = bt.coverage_by_item(E[E["h"] == h], m).set_index("commodity_id")["coverage"]
        c = c.reindex(keep).dropna() * 100
        ax.scatter(c, i + rng.uniform(-0.18, 0.18, len(c)), s=26, color=METHOD_COLOR[m],
                   alpha=0.8, edgecolor=style.SURFACE, linewidth=1)
    ax.axvspan(70, 90, color=CONTEXT, alpha=0.25, lw=0)
    ax.axvline(80, color=INK_2, lw=1)
    ax.set_yticks(range(len(bt.INTERVALS)),
                  [METHOD_LABEL[m] + ("  (shipped)" if m == chosen else "") for m in bt.INTERVALS],
                  fontsize=9)
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    ax.set_xlabel(f"Coverage of the 80% range, {h} weeks ahead (%) - one dot per commodity; "
                  "shaded = 70-90%")
    ax.set_title("Is the range honest for every item, not just on average?", pad=10)
    return fig


def backtest_bands(R: pd.DataFrame, method: str, ids: list[str], h: int = 4) -> plt.Figure:
    fig, axes = plt.subplots(len(ids), 1, figsize=(9, 2.5 * len(ids)), sharex=True)
    for ax, cid in zip(axes, ids):
        g = R[(R["h"] == h) & (R["commodity_id"] == cid)].dropna(subset=[f"lo_{method}"])
        t = g["date"] + pd.Timedelta(weeks=h)
        lo, hi = np.exp(g["lp"] + g[f"lo_{method}"]), np.exp(g["lp"] + g[f"hi_{method}"])
        actual = np.exp(g["lp"] + g["y"])
        ax.fill_between(t, lo, hi, color=SERIES[0], alpha=0.22, lw=0,
                        label=f"80% range forecast {h} weeks earlier")
        ax.plot(t, actual, color=SERIES[0], lw=1.6, label="Actual price")
        out = (actual < lo) | (actual > hi)
        ax.scatter(t[out], actual[out], s=14, color=SERIES[1], zorder=3, label="Outside the range")
        cov = 1 - out[actual.notna()].mean()
        ax.set_title(f"{data.name(cid)} - inside the range {cov:.0%} of weeks", fontsize=10)
        ax.set_ylabel("Taka")
    axes[0].legend(loc="upper left", ncol=3, fontsize=8)
    axes[-1].xaxis.set_major_locator(mdates.YearLocator())
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.suptitle("What the forecasts looked like in real time: ranges widen after shocks, "
                 "but sudden jumps still escape", x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.tight_layout()
    return fig


def forecast_fan(F: pd.DataFrame, ids: list[str], history_weeks: int = 26) -> plt.Figure:
    lp = panel.weekly_log_prices()
    fig, axes = plt.subplots(2, 3, figsize=(10, 5.4))
    for ax, cid in zip(axes.flat, ids):
        hist = np.exp(lp[cid].dropna().iloc[-history_weeks:])
        f = F[F["commodity_id"] == cid].sort_values("h")
        ax.plot(hist.index, hist, color=SERIES[0], lw=1.8)
        if len(f):
            x = [hist.index[-1]] + list(pd.to_datetime(f["target_date"]))
            now = f["price_now"].iloc[0]
            ax.fill_between(x, [now] + list(f["lo"]), [now] + list(f["hi"]), color=SERIES[0],
                            alpha=0.22, lw=0)
            ax.plot(x, [now] * len(x), color=SERIES[0], lw=1.2, ls=(0, (1, 2)))
            last = f.iloc[-1]
            ax.annotate(f"{last['lo']:.0f}-{last['hi']:.0f}", (x[-1], last["hi"]), xytext=(0, 4),
                        textcoords="offset points", ha="right", fontsize=8, color=INK_2)
        ax.set_title(f"{data.name(cid)}", fontsize=10)
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
        ax.tick_params(labelsize=8)
    for ax in axes[:, 0]:
        ax.set_ylabel("Taka")
    origin = pd.to_datetime(F["origin"].iloc[0])
    fig.suptitle(f"Forecast from {origin:%d %b %Y}: 80% price range for the next 4 weeks "
                 "(dotted = today's price)", x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.tight_layout()
    return fig


def importance(imp: pd.DataFrame, top: int = 12) -> plt.Figure:
    g = imp.head(top).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 0.34 * top + 1.4))
    y = np.arange(len(g))
    ax.barh(y, g["loss_increase_pct"], height=0.55, color=SERIES[0])
    ax.set_yticks(y, [FEATURE_LABEL.get(f, f) for f in g.index], fontsize=9)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Loss increase when the feature is shuffled (%), most recent year held out")
    ax.set_title("What sets the range: which item it is and how volatile it has been - "
                 "not the calendar", pad=10)
    return fig
