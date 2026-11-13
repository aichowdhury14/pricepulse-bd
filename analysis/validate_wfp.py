"""External validation: TCB (our scrape) vs WFP Dhaka Sadar market (independent survey).

If the scraper/parser/backfill were wrong, monthly TCB prices would drift from an
independently collected series. We compare levels (ratio) and month-on-month
changes (correlation) where both exist.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import data

# WFP commodity name -> TCB id (same product and unit, per kg / litre)
PAIRS = {
    "Wheat flour": "atta_loose",
    "Rice (coarse)": "rice_coarse",
    "Oil (palm)": "palm_loose",
    "Lentils (masur)": "lentil_bold",
    "Oil (soybean, fortified)": "soybean_loose",
    "Sugar": "sugar",
    "Garlic (imported, China)": "garlic_imported",
    "Chili (green)": "green_chili",
    "Eggs (brown)": "eggs",  # WFP per piece, TCB per hali (4) -> scaled below
}
WFP_MARKET = "Dhaka Sadar"


def compare() -> tuple[pd.DataFrame, pd.DataFrame]:
    wfp = pd.read_csv(data.PROC / "wfp_prices.csv", parse_dates=["date"])
    wfp = wfp[wfp["market"] == WFP_MARKET]
    tcb = data.monthly_wide()
    rows, series = [], []
    for wname, tid in PAIRS.items():
        w = (wfp[wfp["commodity"] == wname].set_index("date")["price"]
             .resample("MS").mean())
        if tid == "eggs":
            w = w * 4
        t = tcb[tid] if tid in tcb else pd.Series(dtype=float)
        j = pd.concat({"wfp": w, "tcb": t}, axis=1).dropna()
        if len(j) < 6:
            continue
        mom = np.log(j).diff().dropna()
        rows.append({
            "commodity_id": tid, "wfp_commodity": wname, "months": len(j),
            "from": j.index.min().date(), "to": j.index.max().date(),
            "level_corr": j["wfp"].corr(j["tcb"]),
            "change_corr": mom["wfp"].corr(mom["tcb"]) if len(mom) > 5 else np.nan,
            "median_ratio_tcb_to_wfp": (j["tcb"] / j["wfp"]).median(),
        })
        series.append(j.assign(commodity_id=tid))
    summary = pd.DataFrame(rows).set_index("commodity_id")
    return summary, pd.concat(series)
