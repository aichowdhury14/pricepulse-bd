"""Run the whole data pipeline (what the daily GitHub Action will call).

    python pipeline/run_all.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = ["scrape_tcb.py", "parse_tcb.py", "build_dataset.py", "fetch_wfp.py"]

for step in STEPS:
    print(f"\n=== {step} ===", flush=True)
    subprocess.run([sys.executable, str(HERE / step)], check=True)
