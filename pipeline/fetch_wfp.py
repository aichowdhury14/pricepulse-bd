"""Download WFP's Bangladesh food price dataset from HDX (monthly, district markets).

Source: https://data.humdata.org/dataset/wfp-food-prices-for-bangladesh (CC BY-IGO)
Used for the district-level view and long history (1998-) that TCB (Dhaka only,
2020-) cannot give.

Output: data/processed/wfp_prices.csv (retail prices only, HXL tag row removed)
"""
from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed" / "wfp_prices.csv"
PACKAGE = "https://data.humdata.org/api/3/action/package_show?id=wfp-food-prices-for-bangladesh"
HEADERS = {"User-Agent": "Mozilla/5.0 (PricePulseBD open-data research)"}
KEEP = ["date", "admin1", "admin2", "market", "market_id", "latitude", "longitude",
        "category", "commodity", "commodity_id", "unit", "priceflag", "price"]


def main() -> None:
    meta = requests.get(PACKAGE, headers=HEADERS, timeout=60).json()["result"]
    url = next(r["url"] for r in meta["resources"] if r["url"].endswith("wfp_food_prices_bgd.csv"))
    raw = requests.get(url, headers=HEADERS, timeout=120).content
    df = pd.read_csv(io.BytesIO(raw), dtype=str)
    df = df[~df["date"].str.startswith("#")]  # HXL hashtag row
    df = df[df["pricetype"] == "Retail"][KEEP]
    df["date"] = pd.to_datetime(df["date"])
    for c in ("price", "latitude", "longitude"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["price"]).sort_values(["commodity", "market", "date"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"WFP: {len(df):,} retail rows, {df['market'].nunique()} markets, "
          f"{df['commodity'].nunique()} commodities, "
          f"{df['date'].min().date()} to {df['date'].max().date()} "
          f"(dataset updated {meta.get('last_modified', '?')[:10]})")


if __name__ == "__main__":
    main()
