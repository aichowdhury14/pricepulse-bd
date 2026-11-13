"""Loading helpers shared by every analysis module."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
REF = ROOT / "data" / "reference"
OUTPUTS = ROOT / "outputs"
FIGURES = ROOT / "reports" / "figures"

# Import-dependent vs mainly domestic supply. Judgement call based on Bangladesh's
# import shares (wheat ~85%+, edible oil ~90%, sugar ~95%, lentils ~half, dates,
# milk powder and most whole spices imported); documented so it can be challenged.
IMPORT_DEPENDENT = {
    "atta_loose", "atta_pkt", "maida_loose", "maida_pkt",
    "soybean_loose", "soybean_1l", "soybean_2l", "soybean_5l", "palm_loose",
    "palm_super_loose", "lentil_bold", "lentil_medium", "chickpea", "anchor_dal",
    "sugar", "dates", "milk_dano", "milk_diploma", "milk_fresh", "milk_marks",
    "garlic_imported", "ginger_imported", "onion_imported", "chili_dry_imported",
    "turmeric_imported", "cumin", "cinnamon", "clove", "cardamom",
}
DOMESTIC = {
    "rice_fine", "rice_medium", "rice_coarse", "potato", "onion_local", "garlic_local",
    "ginger_local", "chili_dry_local", "turmeric_local", "rui", "hilsa", "beef",
    "mutton", "chicken_broiler", "chicken_local", "eggs", "salt", "lentil_fine", "mung",
    "coriander", "bay_leaf",
}


@lru_cache(maxsize=1)
def commodities() -> pd.DataFrame:
    c = pd.read_csv(REF / "commodities.csv")
    c["supply"] = np.where(c["commodity_id"].isin(IMPORT_DEPENDENT), "import-dependent",
                  np.where(c["commodity_id"].isin(DOMESTIC), "domestic", "other"))
    return c.set_index("commodity_id")


def name(cid: str) -> str:
    return commodities().loc[cid, "name_en"]


@lru_cache(maxsize=1)
def daily_long() -> pd.DataFrame:
    return pd.read_csv(PROC / "tcb_daily.csv", parse_dates=["date"])


def daily_wide(ffill_limit: int = 7) -> pd.DataFrame:
    """Calendar-daily price_mid, one column per commodity.

    Short gaps (weekends, holidays, missing reports) are forward-filled up to
    `ffill_limit` days; longer gaps stay NaN so they never masquerade as data.
    """
    w = daily_long().pivot_table(index="date", columns="commodity_id", values="price_mid")
    w = w.asfreq("D")
    return w.ffill(limit=ffill_limit)


def weekly_wide() -> pd.DataFrame:
    """Weekly (week ending Thursday, TCB's last working day) mean price."""
    w = daily_long().pivot_table(index="date", columns="commodity_id", values="price_mid")
    return w.resample("W-THU").mean()


def monthly_wide() -> pd.DataFrame:
    w = daily_long().pivot_table(index="date", columns="commodity_id", values="price_mid")
    return w.resample("MS").mean()


@lru_cache(maxsize=1)
def festivals() -> pd.DataFrame:
    return pd.read_csv(REF / "festivals.csv", parse_dates=["date"])


def core_ids() -> list[str]:
    c = commodities()
    return c.index[c["core"] == 1].tolist()
