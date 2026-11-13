"""Figures for the Stage 2 report. Each function returns a matplotlib Figure.

Conventions (dataviz method): one y-axis per plot, categorical colours in fixed slot
order following the entity, thin 2px lines, hairline grid, titles state the finding,
legends for >= 2 series plus selective direct labels.
"""
from __future__ import annotations

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

from . import data, style
from .style import CONTEXT, INK, INK_2, MUTED, SERIES, UP, DOWN

style.apply()
SUPPLY_COLOR = {"import-dependent": SERIES[0], "domestic": SERIES[1], "other": CONTEXT}
DEDUP = {"soybean_2l", "soybean_5l", "atta_pkt", "maida_pkt", "milk_diploma", "milk_fresh",
         "milk_marks", "palm_super_loose", "rod_40"}


def _end_label(ax, s: pd.Series, text: str, color: str, dy: float = 0) -> None:
    s = s.dropna()
    ax.annotate(text, (s.index[-1], s.iloc[-1]), xytext=(6, dy), textcoords="offset points",
                color=INK, fontsize=9, va="center",
                bbox=dict(boxstyle="round,pad=0.2", fc="none", ec="none"))
    ax.plot(s.index[-1], s.iloc[-1], "o", ms=5, color=color, mec=style.SURFACE, mew=2)


def basket(index: pd.Series, by_supply: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(9, 4.6))
    idx = by_supply.iloc[:-1]  # drop the partial current month
    for g in ("import-dependent", "domestic"):
        ax.plot(idx.index, idx[g], color=SUPPLY_COLOR[g], label=g.capitalize() + " items")
    ax.axhline(100, color=style.AXIS, lw=1)
    _end_label(ax, idx["import-dependent"], f"{idx['import-dependent'].iloc[-1]:.0f}",
               SUPPLY_COLOR["import-dependent"])
    _end_label(ax, idx["domestic"], f"{idx['domestic'].iloc[-1]:.0f}", SUPPLY_COLOR["domestic"])
    ax.set_title("Import-dependent staples got far more expensive than domestic ones", pad=22)
    style.subtitle(ax, "Core-basket price index, Dhaka retail, FY2020-21 = 100 "
                       "(Jevons, monthly). Source: TCB")
    ax.legend(loc="upper left")
    ax.set_ylabel("Index")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.margins(x=0.06)
    return fig


def inflation_dots(inf: pd.DataFrame, test: dict) -> plt.Figure:
    x = inf[~inf.index.isin(DEDUP)].sort_values("change_pct")
    fig, ax = plt.subplots(figsize=(8, 0.22 * len(x) + 1.6))
    y = np.arange(len(x))
    colors = x["supply"].map(SUPPLY_COLOR)
    ax.hlines(y, 0, x["change_pct"], color=colors, lw=1.2, alpha=0.5)
    ax.scatter(x["change_pct"], y, s=36, c=colors, edgecolor=style.SURFACE, linewidth=1.5, zorder=3)
    ax.set_yticks(y, x["name_en"], fontsize=8)
    ax.axvline(0, color=style.AXIS, lw=1)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Price change, FY2020-21 average to latest 3 months (%)")
    for g, lab in (("import-dependent", "Import-dependent"), ("domestic", "Domestic"),
                   ("other", "Non-food / other")):
        ax.scatter([], [], s=36, c=SUPPLY_COLOR[g], label=lab)
    ax.legend(loc="lower right")
    ax.set_title(f"Median rise: {test['median_change_import_pct']:.0f}% for import-dependent "
                 f"vs {test['median_change_domestic_pct']:.0f}% for domestic items", pad=22)
    style.subtitle(ax, f"Permutation test p = {test['p_permutation_one_sided']:.3f} "
                       f"({test['n_import']} vs {test['n_domestic']} commodities)")
    return fig


def spike_series(cid: str, episodes: pd.DataFrame, known: pd.DataFrame) -> plt.Figure:
    p = data.daily_wide()[cid].dropna()
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.plot(p.index, p, color=SERIES[0], lw=1.6, label=data.name(cid))
    ev = episodes[episodes["commodity_id"] == cid]
    for e in ev.itertuples():
        ax.axvspan(pd.Timestamp(e.start), pd.Timestamp(e.end) + pd.Timedelta(days=1),
                   color=SERIES[1], alpha=0.18, lw=0)
    ax.axvspan(p.index[0], p.index[0], color=SERIES[1], alpha=0.18, label="Detected spike")
    for k in known[known["commodity_id"] == cid].itertuples():
        t = pd.Timestamp(k.date)
        ax.axvline(t, color=INK_2, lw=0.8)
        ax.text(t, ax.get_ylim()[1], " " + k.event.replace("bans", "bans\n"), fontsize=8,
                color=INK_2, va="top")
    ax.set_ylabel("Taka per kg (mid of min-max)")
    ax.set_title(f"{data.name(cid)}: every flagged spike, and the shocks behind two of them",
                 pad=22)
    style.subtitle(ax, "Spike = 14-day rise >= 10% and robust z >= 3.5 vs the item's own "
                       "past year (first ~7 months = baseline warm-up). Source: TCB")
    ax.legend(loc="upper right")
    return fig


def spike_timeline(episodes: pd.DataFrame, ids: list[str]) -> plt.Figure:
    ev = episodes[episodes["commodity_id"].isin(ids)]
    order = ev.groupby("commodity_id").size().reindex(ids).fillna(0).sort_values().index
    fig, ax = plt.subplots(figsize=(9, 0.32 * len(order) + 1.6))
    ymap = {c: i for i, c in enumerate(order)}
    ax.scatter(pd.to_datetime(ev["peak_date"]), ev["commodity_id"].map(ymap),
               s=np.clip(ev["change_14d_pct"], 10, 160) * 2.2, color=SERIES[0], alpha=0.75,
               edgecolor=style.SURFACE, linewidth=1.5, zorder=3)
    ax.set_yticks(range(len(order)), [data.name(c) for c in order], fontsize=8)
    ax.grid(axis="y", visible=False)
    for v in (20, 50, 100):
        ax.scatter([], [], s=v * 2.2, color=SERIES[0], alpha=0.75, label=f"+{v}% in 14 days")
    ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0), labelspacing=1.4)
    ax.set_title("Perishables spike often and hard; rice and edible oil almost never", pad=22)
    style.subtitle(ax, "Detected price spikes per core commodity, dot size = 14-day rise")
    return fig


def festival_paths(festival: str, ids: list[str], title: str) -> plt.Figure:
    from .events import event_paths
    fig, axes = plt.subplots(2, 3, figsize=(10, 5.6), sharex=True)
    for ax, cid in zip(axes.flat, ids):
        p = event_paths(cid, festival, lo=-90, hi=30)
        for yr in p.columns:
            ax.plot(p.index, p[yr], color=CONTEXT, lw=0.8)
        m = p.mean(axis=1)
        ax.plot(m.index, m, color=SERIES[0], lw=2)
        ax.axvline(0, color=INK_2, lw=0.8)
        ax.axhline(0, color=style.AXIS, lw=0.8)
        ax.set_title(data.name(cid), fontsize=10)
        ax.set_ylim(-30, 30)
    axes[0, 0].plot([], [], color=SERIES[0], label="Average")
    axes[0, 0].plot([], [], color=CONTEXT, lw=0.8, label="Single year")
    axes[0, 0].legend(loc="lower left", fontsize=8)
    for ax in axes[1]:
        ax.set_xlabel("Days from festival")
    for ax in axes[:, 0]:
        ax.set_ylabel("% vs 1-2 months before")
    fig.suptitle(title, x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.tight_layout()
    return fig


def festival_effects(res: pd.DataFrame, ids: list[str]) -> plt.Figure:
    fests = ["Ramadan", "Eid-ul-Fitr", "Eid-ul-Adha"]
    fig, axes = plt.subplots(1, 3, figsize=(10, 0.3 * len(ids) + 1.8), sharey=True)
    y = np.arange(len(ids))
    for ax, f in zip(axes, fests):
        r = res[res["festival"] == f].set_index("commodity_id").reindex(ids)
        sig = r["q_value"] < 0.10
        col = np.where(r["abnormal_pct"] >= 0, UP, DOWN)
        ax.hlines(y, 0, r["abnormal_pct"], color=col, lw=1.2, alpha=0.5)
        ax.scatter(r["abnormal_pct"][sig], y[sig.to_numpy()], s=40, c=col[sig.to_numpy()],
                   edgecolor=style.SURFACE, linewidth=1.5, zorder=3)
        ax.scatter(r["abnormal_pct"][~sig], y[~sig.to_numpy()], s=40, facecolor=style.SURFACE,
                   edgecolor=col[~sig.to_numpy()], linewidth=1.5, zorder=3)
        ax.axvline(0, color=style.AXIS, lw=1)
        ax.set_title(f, fontsize=10)
        ax.grid(axis="y", visible=False)
        ax.set_xlim(-30, 20)
    axes[0].set_yticks(y, [data.name(c) for c in ids], fontsize=8)
    axes[0].invert_yaxis()
    axes[1].set_xlabel("Extra price change in the 2 weeks before, vs a normal 6-week span (%)")
    h1 = axes[2].scatter([], [], s=40, c=INK_2)
    h2 = axes[2].scatter([], [], s=40, facecolor=style.SURFACE, edgecolor=INK_2)
    fig.suptitle("Before Ramadan, meat rises; harvest-season crops fall", x=0.01, ha="left",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.legend([h1, h2], ["Significant (FDR q < 0.10)", "Not significant"], loc="upper right",
               ncol=2, fontsize=8, bbox_to_anchor=(0.995, 0.995))
    return fig


def correlation_heatmap(corr: pd.DataFrame) -> plt.Figure:
    cmap = LinearSegmentedColormap.from_list("div", style.DIVERGING)
    fig, ax = plt.subplots(figsize=(8.2, 7))
    m = corr.to_numpy().copy()
    np.fill_diagonal(m, np.nan)
    im = ax.imshow(m, cmap=cmap, vmin=-0.7, vmax=0.7)
    labels = [data.name(c) for c in corr.index]
    ax.set_xticks(range(len(labels)), labels, rotation=90, fontsize=8)
    ax.set_yticks(range(len(labels)), labels, fontsize=8)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, shrink=0.6, label="Correlation of weekly price changes")
    cb.outline.set_visible(False)
    ax.set_title("Prices move in families: rice grades, edible oils, imported staples", pad=12)
    return fig


def wfp_validation(summary: pd.DataFrame, series: pd.DataFrame) -> plt.Figure:
    ids = summary.index.tolist()
    n = len(ids)
    cols = 3
    fig, axes = plt.subplots(int(np.ceil(n / cols)), cols, figsize=(10, 2.4 * np.ceil(n / cols)))
    for ax, cid in zip(axes.flat, ids):
        s = series[series["commodity_id"] == cid]
        ax.plot(s.index, s["tcb"], color=SERIES[0], lw=1.8)
        ax.plot(s.index, s["wfp"], color=SERIES[1], lw=1.8)
        ax.set_title(f"{data.name(cid)}  (r = {summary.loc[cid, 'level_corr']:.2f})", fontsize=9)
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%y"))
        ax.tick_params(labelsize=8)
    for ax in axes.flat[n:]:
        ax.set_visible(False)
    l1, = axes.flat[0].plot([], [], color=SERIES[0])
    l2, = axes.flat[0].plot([], [], color=SERIES[1])
    fig.suptitle("An independent survey (WFP) tracks the scraped TCB prices closely",
                 x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.legend([l1, l2], ["TCB (this project)", "WFP, Dhaka Sadar"], loc="upper right",
               ncol=2, fontsize=9, bbox_to_anchor=(0.995, 0.995))
    return fig
