"""Run every Stage 2 analysis; write tables, website JSON and figures.

    python -m analysis.run

Outputs
  outputs/*.csv        full result tables (read by the notebook)
  outputs/*.json       compact payloads for the website (Stage 4)
  reports/figures/*.png
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from . import comovement, data, eda, events, figures, spikes, style, validate_wfp

RAMADAN_ITEMS = ["beef", "chicken_broiler", "dates", "chickpea", "sugar", "soybean_loose"]
EFFECT_ITEMS = ["beef", "mutton", "chicken_broiler", "chicken_local", "eggs", "dates",
                "chickpea", "sugar", "soybean_loose", "atta_loose", "lentil_bold",
                "onion_local", "garlic_local", "potato", "ginger_imported", "rice_coarse"]


def _json(name: str, obj) -> None:
    data.OUTPUTS.mkdir(parents=True, exist_ok=True)
    (data.OUTPUTS / f"{name}.json").write_text(
        json.dumps(obj, indent=1, ensure_ascii=False, default=str))


def _records(df: pd.DataFrame, digits: int = 3) -> list[dict]:
    return json.loads(df.round(digits).replace({np.nan: None}).to_json(
        orient="records", date_format="iso"))


def main() -> None:
    out = data.OUTPUTS
    out.mkdir(parents=True, exist_ok=True)

    print("basket + inflation ...")
    idx = eda.basket_index()
    by = eda.basket_by_supply()
    inf = eda.item_inflation()
    test = eda.import_vs_domestic(inf)
    inf.to_csv(out / "item_inflation.csv")
    pd.concat([idx, by], axis=1).to_csv(out / "basket_index.csv")
    _json("basket_index", {"base": "FY2020-21 = 100", "method": "Jevons, monthly",
                           "series": _records(pd.concat([idx, by], axis=1).reset_index()
                                              .rename(columns={"index": "month"}), 1)})
    _json("item_inflation", {"test": test, "items": _records(inf.reset_index(), 2)})

    print("WFP validation ...")
    wsum, wser = validate_wfp.compare()
    wsum.to_csv(out / "wfp_validation.csv")
    _json("wfp_validation", _records(wsum.reset_index()))

    print("spikes ...")
    up, down = spikes.detect("up"), spikes.detect("down")
    known = spikes.evaluate_known()
    up.to_csv(out / "spikes_up.csv", index=False)
    down.to_csv(out / "spikes_down.csv", index=False)
    known.to_csv(out / "spikes_known_shocks.csv", index=False)
    _json("spikes", {"up": _records(up, 2), "down": _records(down, 2),
                     "known_shock_recall": _records(known, 2)})

    print("festival event study (slow, ~2 min) ...")
    fest = events.study()
    fest.to_csv(out / "festival_effects.csv", index=False)
    _json("festival_effects", _records(fest))

    print("co-movement ...")
    corr = comovement.correlation()
    ll = comovement.lead_lag()
    corr.to_csv(out / "correlation_core.csv")
    ll.to_csv(out / "lead_lag.csv", index=False)
    _json("comovement", {"order": corr.index.tolist(), "corr": corr.round(3).values.tolist(),
                         "lead_lag": _records(ll)})

    print("figures ...")
    raw_known = pd.read_csv(data.REF / "known_shocks.csv")
    style.save(figures.basket(idx, by), "01_basket_index")
    style.save(figures.inflation_dots(inf, test), "02_inflation_by_item")
    style.save(figures.wfp_validation(wsum, wser), "03_wfp_validation")
    style.save(figures.spike_series("onion_local", up, raw_known), "04_spikes_onion")
    style.save(figures.spike_timeline(up, data.core_ids()), "05_spike_timeline")
    style.save(figures.festival_paths(
        "ramadan_start", RAMADAN_ITEMS,
        "Around Ramadan: meat steps up and stays; iftar staples barely move"),
        "06_ramadan_paths")
    style.save(figures.festival_effects(fest, EFFECT_ITEMS), "07_festival_effects")
    style.save(figures.correlation_heatmap(corr), "08_correlation")

    summary = {
        "generated": pd.Timestamp.now().isoformat(timespec="seconds"),
        "data_through": str(data.daily_long()["date"].max().date()),
        "core_basket_index_latest": round(float(idx.iloc[-2]), 1),
        "import_vs_domestic": test,
        "wfp_level_corr_range": [round(float(wsum["level_corr"].min()), 2),
                                 round(float(wsum["level_corr"].max()), 2)],
        "spike_episodes_up": int(len(up)),
        "known_shocks_detected": f"{int(known['detected'].fillna(False).sum())}"
                                 f"/{int(known['evaluable'].sum())} evaluable",
        "festival_significant_q10": fest[fest["q_value"] < 0.10]
            .groupby("festival").size().to_dict(),
    }
    _json("summary", summary)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
