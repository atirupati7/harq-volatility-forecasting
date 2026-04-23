"""Download 1-minute klines for BTCUSDT and ETHUSDT from Binance.

The REST API at api.binance.com returns HTTP 451 for US IPs, so we pull from
`data.binance.vision`, Binance's public monthly archive of historical kline
data (same schema, no geo-block, no rate limits). Each month is a zip
containing one CSV. We unpack in-memory and rewrite per-month CSVs under
data/raw/binance_crypto/.

Usage:
    python scripts/download_binance.py [--start 2018-01] [--end 2026-04]
"""
from __future__ import annotations

import argparse
import io
import sys
import time
import zipfile
from datetime import date
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "data" / "raw" / "binance_crypto"

BASE = "https://data.binance.vision/data/spot/monthly/klines"
SYMBOLS = ["BTCUSDT", "ETHUSDT"]
INTERVAL = "1m"

# CSV columns present in every Binance monthly kline archive
KLINE_COLS = [
    "open_time", "open", "high", "low", "close", "volume",
    "close_time", "quote_volume", "n_trades",
    "taker_buy_base", "taker_buy_quote", "ignore",
]


def months(start: tuple[int, int], end: tuple[int, int]):
    y, m = start
    while (y, m) <= end:
        yield y, m
        m += 1
        if m == 13:
            y, m = y + 1, 1


def fetch_month(symbol: str, y: int, m: int, dst: Path) -> tuple[int, str]:
    """Returns (bars_written, status_tag)."""
    tag = f"{y:04d}-{m:02d}"
    url = f"{BASE}/{symbol}/{INTERVAL}/{symbol}-{INTERVAL}-{tag}.zip"
    r = requests.get(url, timeout=120)
    if r.status_code == 404:
        return 0, "missing"
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        name = zf.namelist()[0]
        raw = zf.read(name).decode("utf-8")
    lines = raw.splitlines()
    # Newer monthly files include a header row; older ones don't.
    if lines and lines[0].split(",")[0] == "open_time":
        body = "\n".join(lines[1:])
    else:
        body = "\n".join(lines)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open("w") as f:
        f.write(",".join(KLINE_COLS) + "\n")
        f.write(body)
        if not body.endswith("\n"):
            f.write("\n")
    return len(lines) - (1 if lines and lines[0].startswith("open_time") else 0), "ok"


def parse_ym(s: str) -> tuple[int, int]:
    y, m = s.split("-")
    return int(y), int(m)


def main() -> int:
    ap = argparse.ArgumentParser()
    today = date.today()
    ap.add_argument("--start", default="2018-01", help="YYYY-MM")
    # Default end = previous month (current month's archive may not be published yet)
    prev_y, prev_m = (today.year - 1, 12) if today.month == 1 else (today.year, today.month - 1)
    ap.add_argument("--end", default=f"{prev_y:04d}-{prev_m:02d}", help="YYYY-MM")
    args = ap.parse_args()

    start = parse_ym(args.start)
    end = parse_ym(args.end)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    total_ok = total_missing = 0
    for symbol in SYMBOLS:
        print(f"[binance-vision] {symbol} {args.start} → {args.end}")
        for y, m in months(start, end):
            out = OUT_DIR / f"{symbol.lower()}_1min_{y:04d}-{m:02d}.csv"
            if out.exists() and out.stat().st_size > 1024:
                continue
            t0 = time.time()
            try:
                n, status = fetch_month(symbol, y, m, out)
            except requests.RequestException as e:
                print(f"[binance-vision] ERROR on {symbol} {y}-{m:02d}: {e}", file=sys.stderr)
                return 1
            elapsed = time.time() - t0
            if status == "ok":
                total_ok += 1
                print(f"[binance-vision] {out.name}: {n:,} bars in {elapsed:.1f}s")
            else:
                total_missing += 1
                print(f"[binance-vision] {y}-{m:02d} missing for {symbol} (archive not published)")
    print(f"[binance-vision] done: {total_ok} months written, {total_missing} missing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
