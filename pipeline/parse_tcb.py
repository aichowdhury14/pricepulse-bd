"""Parse raw TCB daily Excel reports into one tidy long table.

Each report has one block per commodity row with min/max prices for four reference
dates: today, 1 week ago, 1 month ago, 1 year ago. We keep all four ("lag" column)
because the lagged snapshots let us fill gaps where a day's report is missing
(e.g. 2022 has only 64 reports in the archive).

Layout quirks handled (verified on 2021 and 2026 files):
  * the header row ("পণ্যের নাম ... অদ্যকার মূল্য") floats between rows 5-6
  * category rows ("ভোজ্য তেল", "মসলাঃ") have no unit
  * a footer (market list, starred-items note) and sometimes a second summary
    table follow the main table and must be ignored
  * the same item can appear multiple times with different units (soybean 1L/2L/5L)
  * 0 means "not reported" in the lag columns

Output: data/processed/tcb_observations/YYYY-MM.csv (partitioned by report month).
Incremental: files already parsed (or logged as known source problems) are skipped.

    python pipeline/parse_tcb.py          # parse new raw files only
    python pipeline/parse_tcb.py --full   # re-parse everything
"""
from __future__ import annotations

import re
import sys
import unicodedata
import warnings
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "tcb"
OBS_DIR = ROOT / "data" / "processed" / "tcb_observations"  # one CSV per report month
QUALITY_LOG = ROOT / "data" / "reference" / "tcb_parse_failures.csv"


def classify_failure(err: str) -> str:
    """Known source-side problems found while auditing the archive (Nov 2026)."""
    if "BadZipFile" in err:
        return "corrupt_at_source"  # file on TCB's storage is zero-filled
    if "header row not found" in err:
        # 29 Jan - 8 Mar 2025 entries link to a Feb/Mar 2022 comparison sheet
        return "wrong_document_linked"
    return "unknown"

HEADER_KEYS = {"today": "অদ্যকার", "week": "সপ্তাহ", "month": "মাস", "year": "বছর"}
# Footer markers. NOTE: "পণ্যের নাম" is NOT a stop word: the header repeats mid-sheet
# (page 2 of the printout) right before sugar, eggs, dates, salt and vegetables.
STOP_WORDS = ("তারকা", "যে সকল", "বাজার হতে", "সূত্র")
BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")


def clean_text(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    # NFC: "য়"/"ড়" arrive both precomposed and as base + nukta; unify them
    s = unicodedata.normalize("NFC", str(v))
    s = s.replace("‌", "").replace("‍", "").replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()


def to_num(v) -> float | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, (int, float)):
        return float(v) if v > 0 else None
    s = clean_text(v).translate(BN_DIGITS).replace(",", "")
    m = re.search(r"\d+(?:\.\d+)?", s)
    if not m:
        return None
    x = float(m.group(0))
    return x if x > 0 else None


def to_date(v):
    d = pd.to_datetime(v, errors="coerce") if not isinstance(v, str) else pd.NaT
    if isinstance(v, str):
        s = v.translate(BN_DIGITS).strip()
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d"):
            d = pd.to_datetime(s, format=fmt, errors="coerce")
            if pd.notna(d):
                break
    return None if pd.isna(d) else d.date()


def find_header(df: pd.DataFrame) -> tuple[int, dict[str, int]]:
    for r in range(min(20, len(df))):
        cells = [clean_text(x) for x in df.iloc[r].tolist()]
        if any(HEADER_KEYS["today"] in c for c in cells):
            cols = {}
            for key, word in HEADER_KEYS.items():
                for c, text in enumerate(cells):
                    if word in text and "হ্রাস" not in text and key not in cols:
                        # "১ মাস" must not match the "মাসিক" change-% column
                        if key == "month" and "মাসিক" in text:
                            continue
                        if key == "year" and "বাৎসরিক" in text:
                            continue
                        cols[key] = c
            return r, cols
    raise ValueError("header row not found")


def parse_file(path: Path) -> list[dict]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = pd.read_excel(path, header=None, sheet_name=0, engine="openpyxl")
    hr, cols = find_header(df)
    if "today" not in cols:
        raise ValueError("no today column")

    date_row = df.iloc[hr + 1]
    obs_dates = {k: to_date(date_row.iloc[c]) for k, c in cols.items()}
    report_date = obs_dates.get("today")

    rows, category = [], ""
    for r in range(hr + 2, len(df)):
        name = clean_text(df.iat[r, 0])
        unit = clean_text(df.iat[r, 1]) if df.shape[1] > 1 else ""
        if not name:
            continue
        if any(w in name for w in STOP_WORDS):
            break
        if "পণ্যের নাম" in name:  # repeated header row
            continue
        if "সর্বনিম্ন" in clean_text(df.iat[r, cols["today"]]):
            # sub-header row; in old files it also carries the first category name
            category = name
            continue
        prices = {k: (to_num(df.iat[r, c]), to_num(df.iat[r, c + 1])) for k, c in cols.items()}
        if not unit and all(lo is None and hi is None for lo, hi in prices.values()):
            category = name.rstrip(":ঃ ")
            continue
        for lag, (lo, hi) in prices.items():
            if lo is None and hi is None:
                continue
            rows.append({
                "report_date": report_date,
                "lag": lag,
                "obs_date": obs_dates.get(lag),
                "category_raw": category,
                "item_raw": name,
                "unit_raw": unit,
                "price_min": lo if lo is not None else hi,
                "price_max": hi if hi is not None else lo,
                "source_file": path.name,
            })
    return rows


def main(full: bool = False) -> None:
    files = sorted(RAW_DIR.glob("*.xlsx"))
    existing = pd.DataFrame() if full else load_observations()
    old_log = (pd.read_csv(QUALITY_LOG) if QUALITY_LOG.exists() and not full
               else pd.DataFrame(columns=["file", "error", "reason"]))
    done = parsed_files() if not full else set()
    files = [f for f in files if f.name not in done]

    out, failures = [], []
    for i, f in enumerate(files, 1):
        try:
            rows = parse_file(f)
            if not rows:
                raise ValueError("no rows")
            out.extend(rows)
        except Exception as exc:  # keep going; report at the end
            failures.append((f.name, repr(exc)))
        if i % 200 == 0:
            print(f"  parsed {i}/{len(files)}", flush=True)

    log = pd.DataFrame(failures, columns=["file", "error"])
    log["reason"] = log["error"].map(classify_failure)
    log = pd.concat([old_log, log], ignore_index=True).drop_duplicates("file", keep="last")
    QUALITY_LOG.parent.mkdir(parents=True, exist_ok=True)
    log.sort_values("file").to_csv(QUALITY_LOG, index=False, encoding="utf-8")

    new = pd.DataFrame(out)
    if not new.empty:
        # listing date is the fallback when the file's own date cell is blank
        listed = pd.to_datetime(new["source_file"].str.slice(0, 10), errors="coerce")
        new["report_date"] = pd.to_datetime(new["report_date"]).fillna(listed)
        write_partitions(new, existing)

    print(f"New files: {len(files)}  parsed OK: {len(files) - len(failures)}  "
          f"failed: {len(failures)}  new rows: {len(new):,}")
    print("All failures by reason:", log["reason"].value_counts().to_dict())
    unknown = log[log["reason"] == "unknown"]
    for _, r in unknown.iterrows():
        print("  UNKNOWN FAILURE", r["file"], r["error"], file=sys.stderr)


def load_observations() -> pd.DataFrame:
    parts = sorted(OBS_DIR.glob("*.csv"))
    if not parts:
        return pd.DataFrame()
    return pd.concat((pd.read_csv(p, encoding="utf-8") for p in parts), ignore_index=True)


def parsed_files() -> set[str]:
    """Raw files already handled (parsed, or logged as a known source problem)."""
    done = set()
    if OBS_DIR.exists():
        for p in OBS_DIR.glob("*.csv"):
            done |= set(pd.read_csv(p, usecols=["source_file"])["source_file"])
    if QUALITY_LOG.exists():
        log = pd.read_csv(QUALITY_LOG)
        done |= set(log.loc[log["reason"] != "unknown", "file"])
    return done


def write_partitions(new: pd.DataFrame, existing: pd.DataFrame) -> None:
    """One CSV per report month, so a daily update rewrites only the current month."""
    OBS_DIR.mkdir(parents=True, exist_ok=True)
    new = new.copy()
    new["report_date"] = pd.to_datetime(new["report_date"]).dt.date.astype(str)
    months = set(new["report_date"].str.slice(0, 7))
    if not existing.empty:
        existing = existing[existing["report_date"].astype(str).str.slice(0, 7).isin(months)]
    df = pd.concat([existing, new], ignore_index=True)
    df["obs_date"] = pd.to_datetime(df["obs_date"]).dt.date.astype(str)
    for month, part in df.groupby(df["report_date"].astype(str).str.slice(0, 7)):
        part.sort_values(["report_date", "source_file"]).to_csv(
            OBS_DIR / f"{month}.csv", index=False, encoding="utf-8")


if __name__ == "__main__":
    main(full="--full" in sys.argv)
