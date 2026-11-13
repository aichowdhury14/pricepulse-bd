"""Is a new forecast due? Prints `due=true|false` (for $GITHUB_OUTPUT).

Forecasts start from the latest Thursday price, so they only need recomputing when
the data has reached a Thursday newer than the published forecast origin.

    python -m forecast.due
"""
from __future__ import annotations

import json

import pandas as pd

from analysis import data


def due() -> bool:
    latest = data.daily_long()["date"].max()
    last_thursday = latest - pd.Timedelta(days=(latest.dayofweek - 3) % 7)
    published = data.OUTPUTS / "forecasts.json"
    if not published.exists():
        return True
    origin = json.loads(published.read_text(encoding="utf-8"))["origin"]
    return str(last_thursday.date()) > origin


if __name__ == "__main__":
    print(f"due={'true' if due() else 'false'}")
