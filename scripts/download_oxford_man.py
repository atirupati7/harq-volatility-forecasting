"""Download the Oxford-Man Realized Library snapshot.

The original Oxford-Man service was discontinued. We use the archived CSV
shipped in the `highfrequency` R package's data-raw/ directory, which is the
canonical public mirror of the Realized Library (version 0.2).

Output: data/raw/oxford_man_mirror/oxfordmanrealizedvolatilityindices.csv

The CSV covers 2000-01-03 through 2020-02-21 for 31 symbols including
.SPX, .IXIC (Nasdaq Composite, used as NDX proxy), .RUT, .DJI. Columns
include rv5, bv, rsv (negative-return semivariance), medrv, rk_*, open_to_close,
and nobs. Realized quarticity (RQ) is NOT in this snapshot; downstream code
approximates it by RQ ~ RV^2 (exact under a diffusion no-jump null) and
cross-validates against exact RQ from Polygon minute data on the overlap.
"""
from __future__ import annotations

import sys
from pathlib import Path

import requests

URL = (
    "https://raw.githubusercontent.com/jonathancornelissen/highfrequency/"
    "master/data-raw/oxfordmanrealizedvolatilityindices.csv"
)
REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "data" / "raw" / "oxford_man_mirror"
OUT_PATH = OUT_DIR / "oxfordmanrealizedvolatilityindices.csv"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if OUT_PATH.exists() and OUT_PATH.stat().st_size > 10_000_000:
        print(f"[oxford-man] already present at {OUT_PATH} ({OUT_PATH.stat().st_size/1e6:.1f} MB); skipping")
        return 0
    print(f"[oxford-man] downloading {URL}")
    try:
        r = requests.get(URL, timeout=120, stream=True)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"[oxford-man] ERROR: {e}", file=sys.stderr)
        print(
            "The jonathancornelissen/highfrequency mirror appears unreachable. "
            "Try again later or pull a different archived copy "
            "(ef4s/RoughVol, ericwbzhang/Vol_prediction, "
            "LuukOudshoorn25/HighFrequencyTrading).",
            file=sys.stderr,
        )
        return 1
    total = 0
    with OUT_PATH.open("wb") as f:
        for chunk in r.iter_content(chunk_size=1 << 20):
            f.write(chunk)
            total += len(chunk)
    print(f"[oxford-man] wrote {OUT_PATH} ({total/1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
