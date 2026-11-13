"""Build the website's data files from the pipeline, analysis and forecast outputs.

    python -m analysis.site

Writes
  site/data/app.json           everything the page needs on first load (~200 KB)
  site/data/series/<id>.json   full daily history per commodity, loaded on demand
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from . import data

SITE = data.ROOT / "site" / "data"
SPARK_WEEKS = 26
ALERT_DAYS = 14          # a spike is "active" if it was still flagged this recently
RECENT_SPIKE_DAYS = 365

CATEGORY_BN = {
    "Rice": "চাল", "Flour": "আটা-ময়দা", "Edible oil": "ভোজ্য তেল", "Pulses": "ডাল",
    "Vegetables": "সবজি", "Spices": "মসলা", "Fish & meat": "মাছ-মাংস",
    "Eggs & dairy": "ডিম-দুধ", "Other groceries": "অন্যান্য মুদি", "Non-food": "খাদ্য-বহির্ভূত",
}
UNIT_BN = {
    "kg": "কেজি", "litre": "লিটার", "1 L bottle": "১ লিটার বোতল", "2 L bottle": "২ লিটার বোতল",
    "5 L bottle": "৫ লিটার বোতল", "hali (4 pcs)": "হালি (৪টি)", "dista (24 sheets)": "দিস্তা",
    "metric ton": "মেট্রিক টন",
}
FESTIVAL_KEY = {"Ramadan": "ramadan_start", "Eid-ul-Fitr": "eid_ul_fitr", "Eid-ul-Adha": "eid_ul_adha"}
FESTIVAL_ITEMS = ["beef", "mutton", "chicken_broiler", "chicken_local", "eggs", "dates",
                  "chickpea", "sugar", "soybean_loose", "atta_loose", "lentil_bold",
                  "onion_local", "garlic_local", "potato", "ginger_imported", "rice_coarse"]


def _r(x, digits: int = 1):
    return None if x is None or (isinstance(x, float) and not np.isfinite(x)) else round(float(x), digits)


def _pct(now: float, then: float):
    return None if not (np.isfinite(now) and np.isfinite(then)) or then == 0 else _r((now / then - 1) * 100)


def _items(T: pd.Timestamp) -> list[dict]:
    c = data.commodities()
    long = data.daily_long()
    wide = data.daily_wide()
    weekly = wide[wide.index.dayofweek == T.dayofweek].iloc[-SPARK_WEEKS:]
    last = long.sort_values("date").groupby("commodity_id").tail(1).set_index("commodity_id")

    out = data.OUTPUTS
    spikes = pd.read_csv(out / "spikes_up.csv", parse_dates=["start", "end"])
    active = spikes[spikes["end"] >= T - pd.Timedelta(days=ALERT_DAYS)].groupby("commodity_id").tail(1)
    active = active.set_index("commodity_id")
    inflation = pd.read_csv(out / "item_inflation.csv", index_col=0)["change_pct"]
    fc_file = out / "forecasts.csv"
    fc = pd.read_csv(fc_file) if fc_file.exists() else pd.DataFrame(columns=["commodity_id"])

    def at(cid: str, days: int) -> float:
        s = wide[cid]
        t = T - pd.Timedelta(days=days)
        return float(s.loc[t]) if t in s.index else np.nan

    items = []
    for cid, row in c.iterrows():
        if cid not in last.index:
            continue
        obs = last.loc[cid]
        if (T - obs["date"]).days > 21:          # no longer reported by TCB
            continue
        now = float(obs["price_mid"])
        f = fc[fc["commodity_id"] == cid].sort_values("h")
        items.append({
            "id": cid, "en": row["name_en"], "bn": row["name_bn"], "unit": row["unit"],
            "unit_bn": UNIT_BN.get(row["unit"], row["unit"]), "cat": row["category"],
            "supply": row["supply"], "core": int(row["core"]),
            "min": _r(obs["price_min"]), "max": _r(obs["price_max"]), "mid": _r(now),
            "date": str(obs["date"].date()),
            "chg": {"w1": _pct(now, at(cid, 7)), "m1": _pct(now, at(cid, 30)),
                    "y1": _pct(now, at(cid, 365))},
            "since_base": _r(inflation.get(cid, np.nan)),
            "spark": [_r(v) for v in weekly[cid].tolist()],
            "spike": ({"start": str(active.loc[cid, "start"].date()),
                       "pct": _r(active.loc[cid, "change_14d_pct"], 0)}
                      if cid in active.index else None),
            "fc": ([{"h": int(r.h), "date": str(r.target_date), "lo": _r(r.lo), "hi": _r(r.hi)}
                    for r in f.itertuples()] or None),
            "cov": _r(f["backtest_coverage"].iloc[-1] * 100, 0) if len(f) else None,
        })
    return items


def _series(T: pd.Timestamp) -> int:
    long = data.daily_long().sort_values("date")
    (SITE / "series").mkdir(parents=True, exist_ok=True)
    epoch = pd.Timestamp("2020-01-01")
    n = 0
    for cid, g in long.groupby("commodity_id"):
        payload = {"epoch": str(epoch.date()),
                   "d": ((g["date"] - epoch).dt.days).tolist(),
                   "lo": [_r(v) for v in g["price_min"]],
                   "hi": [_r(v) for v in g["price_max"]]}
        (SITE / "series" / f"{cid}.json").write_text(json.dumps(payload, separators=(",", ":")))
        n += 1
    return n


def _festivals(T: pd.Timestamp) -> dict:
    out = data.OUTPUTS
    eff = pd.read_csv(out / "festival_effects.csv")
    eff = eff[eff["commodity_id"].isin(FESTIVAL_ITEMS)]
    fest = data.festivals()
    upcoming = fest[fest["date"] >= T].sort_values("date").groupby("festival").head(1)
    return {
        "items": FESTIVAL_ITEMS,
        "effects": [{"festival": FESTIVAL_KEY[r.festival], "id": r.commodity_id,
                     "pct": _r(r.abnormal_pct), "sig": bool(r.q_value < 0.10),
                     "years": int(r.n_years), "above": int(r.years_above_placebo)}
                    for r in eff.itertuples()],
        "next": [{"festival": r.festival, "date": str(r.date.date()),
                  "projected": "PROJECTED" in str(r.note)}
                 for r in upcoming.sort_values("date").itertuples()],
    }


def build() -> dict:
    out = data.OUTPUTS
    T = data.daily_long()["date"].max()
    c = data.commodities()

    basket = pd.read_csv(out / "basket_index.csv", index_col=0, parse_dates=True)
    basket = basket[basket.index < T.to_period("M").to_timestamp()]      # complete months only
    spikes = pd.read_csv(out / "spikes_up.csv", parse_dates=["start", "end", "peak_date"])
    recent = spikes[spikes["end"] >= T - pd.Timedelta(days=RECENT_SPIKE_DAYS)]
    summary = json.loads((out / "summary.json").read_text())
    inflation = json.loads((out / "item_inflation.json").read_text())["test"]
    quality = json.loads((data.REF / "quality_report.json").read_text(encoding="utf-8"))

    fc_json = out / "forecasts.json"
    forecast = None
    if fc_json.exists():
        f = json.loads(fc_json.read_text(encoding="utf-8"))
        point = pd.DataFrame(f["evaluation"]["point"])
        iv = pd.DataFrame(f["evaluation"]["intervals"])
        forecast = {
            "origin": f["origin"], "method": f["interval_method"],
            "scored": f["evaluation"]["forecasts_scored"],
            "commodities": f["evaluation"]["commodities"], "period": f["evaluation"]["period"],
            "point": [{"h": int(r.h), "model": r.model, "rel": _r(r.rel_mae, 3)}
                      for r in point.itertuples()],
            "naive_mae": [{"h": int(r.h), "pct": _r(r.mae_pct, 1)}
                          for r in point[point["model"] == "naive"].itertuples()],
            "intervals": [{"h": int(r.h), "method": r.method, "cov": _r(r.coverage * 100, 1),
                           "width": _r(r.mean_width_pct, 1)} for r in iv.itertuples()],
        }

    items = _items(T)
    app = {
        "meta": {
            "data_through": str(T.date()),
            "generated": pd.Timestamp.now(tz="UTC").isoformat(timespec="minutes"),
            "items": len(items), "reports": quality["generated_from_reports"],
            "first_date": quality["date_range"][0],
        },
        "categories": [{"id": k, "bn": CATEGORY_BN[k]} for k in CATEGORY_BN
                       if any(i["cat"] == k for i in items)],
        "items": items,
        "basket": {"months": [str(d.date())[:7] for d in basket.index],
                   "all": [_r(v) for v in basket["core_basket_index"]],
                   "imp": [_r(v) for v in basket["import-dependent"]],
                   "dom": [_r(v) for v in basket["domestic"]]},
        "inflation": {"imp_median": _r(inflation["median_change_import_pct"], 0),
                      "dom_median": _r(inflation["median_change_domestic_pct"], 0),
                      "p": _r(inflation["p_permutation_one_sided"], 3)},
        "spikes": [{"id": r.commodity_id, "start": str(r.start.date()), "end": str(r.end.date()),
                    "pct": _r(r.change_14d_pct, 0), "before": _r(r.price_before),
                    "peak": _r(r.price_peak)}
                   for r in recent.sort_values("start", ascending=False).itertuples()
                   if r.commodity_id in c.index],
        "spike_recall": summary["known_shocks_detected"],
        "festivals": _festivals(T),
        "forecast": forecast,
    }
    SITE.mkdir(parents=True, exist_ok=True)
    (SITE / "app.json").write_text(json.dumps(app, ensure_ascii=False, separators=(",", ":")),
                                   encoding="utf-8")
    n = _series(T)
    return {"items": len(items), "series_files": n, "data_through": app["meta"]["data_through"],
            "app_kb": round((SITE / "app.json").stat().st_size / 1024)}


if __name__ == "__main__":
    print(build())
