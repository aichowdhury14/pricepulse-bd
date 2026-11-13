"""Price-spike detection: robust z-score of the 14-day change vs the item's own history.

For each commodity and day t:
    r14(t) = log p(t) - log p(t-14)
    z(t)   = (r14(t) - median) / (1.4826 * MAD)
where median/MAD come from the trailing 365 days of r14 (ending before t-14, so the
window under test never contaminates its own baseline). A spike is
    z >= Z_MIN  and  r14 >= MIN_RISE       (a big rise *for this item*)
Consecutive flagged days (gaps <= 10 days) are merged into one episode.

Why this design
  * robust stats: a few past shocks don't inflate the baseline the way std would
  * per-item scale: +15% in 2 weeks is routine for green chilli, alarming for rice
  * MIN_RISE floor: administered/sticky prices (milk powder, salt) have MAD ~ 0, so
    any 1-taka move would otherwise be "infinitely" unusual
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import data

HORIZON = 14
BASELINE_DAYS = 365
Z_MIN = 3.5
MIN_RISE = np.log(1.10)   # >= +10% over 14 days
MIN_FALL = np.log(0.90)   # <= -10% (for drop episodes)
SCALE_FLOOR = 0.02        # 2% minimum scale for the z denominator
MERGE_GAP = 10


def scores(ids: list[str] | None = None) -> dict[str, pd.DataFrame]:
    w = data.daily_wide()
    ids = ids or list(w.columns)
    lp = np.log(w[ids])
    r = lp - lp.shift(HORIZON)
    base = r.shift(HORIZON + 1)
    med = base.rolling(BASELINE_DAYS, min_periods=180).median()
    mad = (base - med).abs().rolling(BASELINE_DAYS, min_periods=180).median()
    scale = np.maximum(1.4826 * mad, SCALE_FLOOR)
    z = (r - med) / scale
    return {"r14": r, "z": z, "price": w[ids]}


def _episodes(flag: pd.Series) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    days = flag.index[flag.fillna(False).to_numpy(dtype=bool)]
    if len(days) == 0:
        return []
    out, start, prev = [], days[0], days[0]
    for d in days[1:]:
        if (d - prev).days > MERGE_GAP:
            out.append((start, prev))
            start = d
        prev = d
    out.append((start, prev))
    return out


def detect(direction: str = "up") -> pd.DataFrame:
    s = scores()
    r, z, p = s["r14"], s["z"], s["price"]
    rows = []
    for cid in r.columns:
        if direction == "up":
            flag = (z[cid] >= Z_MIN) & (r[cid] >= MIN_RISE)
        else:
            flag = (z[cid] <= -Z_MIN) & (r[cid] <= MIN_FALL)
        for a, b in _episodes(flag):
            seg = r[cid].loc[a:b]
            peak = seg.idxmax() if direction == "up" else seg.idxmin()
            before = p[cid].loc[: a - pd.Timedelta(days=HORIZON)].dropna()
            rows.append({
                "commodity_id": cid, "start": a.date(), "end": b.date(),
                "peak_date": peak.date(), "days_flagged": int(flag.loc[a:b].sum()),
                "change_14d_pct": float(np.expm1(r[cid].loc[peak]) * 100),
                "z_peak": float(z[cid].loc[peak]),
                "price_before": float(before.iloc[-1]) if len(before) else np.nan,
                "price_peak": float(p[cid].loc[a:b + pd.Timedelta(days=HORIZON)].max()
                                    if direction == "up" else
                                    p[cid].loc[a:b + pd.Timedelta(days=HORIZON)].min()),
            })
    ev = pd.DataFrame(rows)
    if ev.empty:
        return ev
    names = data.commodities()["name_en"]
    ev.insert(1, "name_en", ev["commodity_id"].map(names))
    return ev.sort_values("start").reset_index(drop=True)


def evaluate_known(window_days: int = 21) -> pd.DataFrame:
    """Recall check: is each externally documented supply shock detected within
    `window_days` after it happened? Shocks inside the baseline warm-up are marked
    not evaluable rather than counted as misses."""
    known = pd.read_csv(data.REF / "known_shocks.csv", parse_dates=["date"])
    ev = detect("up")
    z = scores()["z"]
    rows = []
    for k in known.itertuples():
        evaluable = k.commodity_id in z and z[k.commodity_id].loc[:k.date].notna().any()
        hit = ev[(ev["commodity_id"] == k.commodity_id)
                 & (pd.to_datetime(ev["end"]) >= k.date)
                 & (pd.to_datetime(ev["start"]) <= k.date + pd.Timedelta(days=window_days))]
        rows.append({
            "date": k.date.date(), "commodity_id": k.commodity_id, "event": k.event,
            "evaluable": bool(evaluable), "detected": bool(len(hit)) if evaluable else None,
            "lag_days": int((pd.to_datetime(hit["start"]).min() - k.date).days) if len(hit) else None,
            "change_14d_pct": float(hit["change_14d_pct"].max()) if len(hit) else None,
        })
    return pd.DataFrame(rows)
