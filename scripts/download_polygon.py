"""Download 1-minute SPY bars from Polygon.io for the post-Oxford-Man window.

Requires POLYGON_API_KEY in the environment. The free tier permits
~5 calls/minute and ~2 years of history; we respect both limits. Data is
written one month per CSV under data/raw/polygon_spy/.

Usage:
    export POLYGON_API_KEY=<key>   # free tier at https://polygon.io
    python scripts/download_polygon.py [--start 2023-01-01] [--end 2025-01-01]

If POLYGON_API_KEY is unset, prints instructions and exits 0 so that the
notebook can still run against whatever data is already on disk.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "data" / "raw" / "polygon_spy"

# Free tier: 5 requests / minute => 12s per request minimum, use 13s for safety.
MIN_SECONDS_BETWEEN_REQUESTS = 13.0
TICKER = "SPY"


def _first_of_next_month(d: date) -> date:
    return date(d.year + (d.month == 12), 1 if d.month == 12 else d.month + 1, 1)


def month_bounds(start: date, end: date):
    """Yield (first_day, last_day_inclusive) for each calendar month overlapping [start, end]."""
    cur = date(start.year, start.month, 1)
    while cur <= end:
        nxt = _first_of_next_month(cur)
        lo = max(cur, start)
        hi = min(nxt - timedelta(days=1), end)
        yield lo, hi
        cur = nxt


def fetch_month(api_key: str, lo: date, hi: date) -> list[dict]:
    """Fetch all 1-minute bars between lo and hi (inclusive)."""
    url = (
        f"https://api.polygon.io/v2/aggs/ticker/{TICKER}/range/1/minute/"
        f"{lo.isoformat()}/{hi.isoformat()}"
    )
    results: list[dict] = []
    params = {
        "adjusted": "true",
        "sort": "asc",
        "limit": 50000,
        "apiKey": api_key,
    }
    next_url = url
    while True:
        r = requests.get(next_url, params=params if next_url == url else {"apiKey": api_key}, timeout=60)
        if r.status_code == 429:
            print(f"[polygon]  rate limited; sleeping 60s")
            time.sleep(60)
            continue
        r.raise_for_status()
        body = r.json()
        batch = body.get("results") or []
        results.extend(batch)
        next_url = body.get("next_url")
        if not next_url:
            break
        time.sleep(MIN_SECONDS_BETWEEN_REQUESTS)
    return results


def write_csv(rows: list[dict], path: Path) -> int:
    if not rows:
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = ["t", "o", "h", "l", "c", "v", "vw", "n"]
    with path.open("w") as f:
        f.write(",".join(keys) + "\n")
        for row in rows:
            f.write(",".join(str(row.get(k, "")) for k in keys) + "\n")
    return len(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default=None, help="YYYY-MM-DD (default: two years ago)")
    ap.add_argument("--end", default=None, help="YYYY-MM-DD (default: today)")
    args = ap.parse_args()

    api_key = os.environ.get("POLYGON_API_KEY")
    if not api_key:
        print(
            "POLYGON_API_KEY is not set.\n"
            "\n"
            "To pull post-Oxford-Man 1-minute SPY data:\n"
            "  1. Sign up for a free account at https://polygon.io\n"
            "  2. Copy your API key from the dashboard\n"
            "  3. export POLYGON_API_KEY=<your_key>\n"
            "  4. Re-run: python scripts/download_polygon.py\n"
            "\n"
            "The notebook will still run without this step, using the\n"
            "Oxford-Man archive (through 2020-02-21) and Binance crypto data.\n"
            "Post-2024 US-equity out-of-sample evaluation will be skipped.\n",
            file=sys.stderr,
        )
        return 0

    today = date.today()
    default_start = date(today.year - 2, today.month, 1)
    start = date.fromisoformat(args.start) if args.start else default_start
    end = date.fromisoformat(args.end) if args.end else today

    print(f"[polygon] SPY 1-min from {start} through {end} (5 req/min)")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for lo, hi in month_bounds(start, end):
        out = OUT_DIR / f"spy_1min_{lo:%Y-%m}.csv"
        if out.exists() and out.stat().st_size > 1024:
            print(f"[polygon] {out.name} already present; skipping")
            continue
        t0 = time.time()
        try:
            rows = fetch_month(api_key, lo, hi)
        except requests.RequestException as e:
            print(f"[polygon] ERROR fetching {lo}..{hi}: {e}", file=sys.stderr)
            return 1
        n = write_csv(rows, out)
        elapsed = time.time() - t0
        print(f"[polygon] {out.name}: {n:,} bars in {elapsed:.1f}s")
        # Enforce 5 req/min ceiling between months too
        if elapsed < MIN_SECONDS_BETWEEN_REQUESTS:
            time.sleep(MIN_SECONDS_BETWEEN_REQUESTS - elapsed)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
