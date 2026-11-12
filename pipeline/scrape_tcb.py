"""Collect TCB (Trading Corporation of Bangladesh) daily Dhaka retail price reports.

TCB publishes one Excel file per working day at https://tcb.gov.bd/pages/daily-rmps
(10 rows per listing page, archive back to May 2021). This script:

  1. crawls the listing pages into data/reference/tcb_manifest.csv (date, title, url)
  2. downloads every Excel file not already present into data/raw/tcb/

Incremental by default: crawling stops at the first page whose files are all known,
so the daily GitHub Action only touches page 1-2.

    python pipeline/scrape_tcb.py            # incremental update
    python pipeline/scrape_tcb.py --full     # re-crawl every listing page
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from html import unescape
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "tcb"
MANIFEST = ROOT / "data" / "reference" / "tcb_manifest.csv"
LISTING_URL = "https://tcb.gov.bd/pages/daily-rmps"
HEADERS = {"User-Agent": "Mozilla/5.0 (PricePulseBD open-data research)"}
POLITE_DELAY = 0.6  # seconds between listing-page requests

ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
FILE_RE = re.compile(r"https://objectstorage[^\"'\s<>]+\.(?:xlsx|xls|pdf)", re.I)
DATE_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})/(20\d\d)\b")
TITLE_RE = re.compile(r"/pages/daily-rmps/([^\"']+)")

FIELDS = ["listed_date", "title", "url", "file"]


def make_session() -> requests.Session:
    """Session that trusts certifi roots plus Sectigo's DV R36 intermediate.

    tcb.gov.bd serves its leaf certificate without the intermediate, which browsers
    fetch automatically but Python does not. We ship that public intermediate
    (pipeline/certs/sectigo_dv_r36.pem) instead of disabling verification.
    """
    import certifi

    bundle = ROOT / "data" / "raw" / "ca_bundle.pem"
    bundle.parent.mkdir(parents=True, exist_ok=True)
    extra = (Path(__file__).parent / "certs" / "sectigo_dv_r36.pem").read_text()
    bundle.write_text(Path(certifi.where()).read_text() + "\n" + extra)
    s = requests.Session()
    s.verify = str(bundle)
    return s


def fetch(url: str, session: requests.Session, retries: int = 3) -> requests.Response:
    for attempt in range(retries):
        try:
            r = session.get(url, headers=HEADERS, timeout=60)
            r.raise_for_status()
            return r
        except requests.RequestException:
            if attempt == retries - 1:
                raise
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("unreachable")


def parse_listing(html: str) -> list[dict]:
    rows = []
    for tr in ROW_RE.findall(html):
        files = FILE_RE.findall(tr)
        dates = DATE_RE.findall(tr)
        if not files:
            continue
        m, d, y = dates[0] if dates else ("", "", "")
        listed = datetime(int(y), int(m), int(d)).date().isoformat() if y else ""
        title = TITLE_RE.search(tr)
        for url in files:
            rows.append({
                "listed_date": listed,
                "title": unescape(title.group(1)) if title else "",
                "url": url,
                "file": "",
            })
    return rows


def load_manifest() -> dict[str, dict]:
    if not MANIFEST.exists():
        return {}
    with MANIFEST.open(encoding="utf-8", newline="") as f:
        return {r["url"]: r for r in csv.DictReader(f)}


def save_manifest(entries: dict[str, dict]) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(entries.values(), key=lambda r: (r["listed_date"], r["url"]))
    with MANIFEST.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def crawl(session: requests.Session, known: dict[str, dict], full: bool) -> int:
    added, page = 0, 1
    while True:
        html = fetch(f"{LISTING_URL}?page={page}", session).text
        rows = parse_listing(html)
        if not rows:
            break
        new = [r for r in rows if r["url"] not in known]
        for r in new:
            known[r["url"]] = r
        added += len(new)
        print(f"  page {page:>3}: {len(rows)} rows, {len(new)} new "
              f"({rows[-1]['listed_date']})", flush=True)
        if not new and not full:
            break
        page += 1
        time.sleep(POLITE_DELAY)
    return added


def local_name(entry: dict) -> str:
    ext = entry["url"].rsplit(".", 1)[-1].lower()
    stem = entry["url"].rsplit("/", 1)[-1].rsplit(".", 1)[0][:12]
    return f"{entry['listed_date']}_{stem}.{ext}"


def download_all(session: requests.Session, entries: dict[str, dict]) -> tuple[int, int]:
    from parse_tcb import parsed_files  # raw files are not kept in git; skip parsed ones

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    done = parsed_files()
    todo = []
    for e in entries.values():
        e["file"] = local_name(e)
        if e["file"] not in done and not (RAW_DIR / e["file"]).exists():
            todo.append(e)

    def grab(e: dict) -> bool:
        try:
            data = fetch(e["url"], session).content
        except requests.RequestException as exc:
            print(f"  ! failed {e['listed_date']}: {exc}", file=sys.stderr)
            return False
        (RAW_DIR / e["file"]).write_bytes(data)
        return True

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(grab, todo))
    return sum(results), len(results) - sum(results)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="crawl every listing page")
    args = ap.parse_args()

    session = make_session()
    entries = load_manifest()
    print(f"Manifest has {len(entries)} files. Crawling listing...")
    added = crawl(session, entries, full=args.full or not entries)
    print(f"{added} new listing entries.")
    ok, failed = download_all(session, entries)
    save_manifest(entries)
    print(f"Downloaded {ok} files ({failed} failed). Manifest: {len(entries)} files.")


if __name__ == "__main__":
    main()
