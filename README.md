# Exploiting the Errors, Revisited

Reproduction and extension of Bollerslev, Patton, and Quaedvlieg (2016)
— *Exploiting the errors: A simple approach for improved volatility
forecasting* — combined with the signed-jump decomposition of Patton
and Sheppard (2015). Post-2013 out-of-sample evaluation across four
volatility regimes, a novel **HARQ-Signed** specification, a
probabilistic **NGBoost-HARQ** extension, and a BTC / ETH cross-check.

**Author.** Aprameya Tirupati · Georgia Tech · Spring 2026
(GTSF IC Quant Mentorship final project)

---

## Headline findings

- **HARQ is the unique best model in the 90% Model Confidence Set** for
  SPX and NDX in 2014–2019. SPX HARQ QLIKE is 19.1% below HAR; NDX,
  13.6%. DJIA belongs to HARQ-F; RUT ties all models.
- **Reproduction check passes direction.** SHAR beats HAR by 5.4% on
  QLIKE (matches Patton–Sheppard 2015); HARQ reduces MSE by 4.4% on
  SPX 2002–2013 (matches BPQ direction).
- **Novel HARQ-Signed** recovers β<sub>−</sub> − β<sub>+</sub> ≈ +1.1
  (bad-volatility persistence) and improves on HARQ by 2.2% on SPX /
  1.5% on DJIA in the post-pub calm regime.
- **NGBoost-HARQ** delivers 97.7% coverage at a 95% nominal prediction
  interval versus 99.5% for a naive HARQ + Gaussian-residual baseline.
  VaR tails are still heavy-tail-limited (Kupiec / Christoffersen reject
  at 1% and 5%).
- **Crypto check fails the microstructure-noise hypothesis.** HARQ's
  edge is 19% on SPX but only 7% on BTC / ETH — 24/7 markets produce
  *cleaner*, not noisier, price processes. Signed-jump asymmetry also
  vanishes in crypto (no overnight gaps).

## Papers reproduced and extended

- Bollerslev, T., Patton, A. J., & Quaedvlieg, R. (2016). Exploiting
  the errors: A simple approach for improved volatility forecasting.
  *Journal of Econometrics*, 192(1), 1–18.
- Patton, A. J., & Sheppard, K. (2015). Good volatility, bad
  volatility: Signed jumps and the persistence of volatility. *Review
  of Economics and Statistics*, 97(3), 683–697.
- Corsi, F. (2009). A simple approximate long-memory model of
  realized volatility. *Journal of Financial Econometrics*, 7(2),
  174–196.
- Duan, T. et al. (2019). NGBoost: Natural Gradient Boosting for
  Probabilistic Prediction. *ICML 2020*.
- Hansen, P. R., Lunde, A., & Nason, J. M. (2011). The Model
  Confidence Set. *Econometrica*, 79(2), 453–497.

## Repository layout

```
harq-volatility-forecasting/
├── README.md                        # this file
├── requirements.txt                 # pinned Python dependencies
├── harq_analysis.ipynb              # primary deliverable; runs end-to-end
├── report.md / report.pdf           # two-page final report
├── slide_spec.md                    # paste into Gemini to render the hero slide
├── data/
│   ├── raw/                         # source downloads (NOT committed)
│   │   ├── r_packages/              # highfrequency + HARModel .RData bundles
│   │   ├── oxford_man_mirror/       # oxfordmanrealizedvolatilityindices.csv
│   │   └── binance_crypto/          # Binance Vision monthly 1-min klines
│   └── processed/                   # daily realized measures (committed; notebook input)
│       ├── spx_measures.csv         # SP500RM (exact RQ; 1997-05→2013-08)
│       ├── spx_measures_oxman_bv2proxy.csv  # Oxford-Man extension (2000→2020)
│       ├── ndx_measures.csv         # Oxford-Man .IXIC (Nasdaq Composite)
│       ├── rut_measures.csv         # Oxford-Man .RUT
│       ├── djia_measures.csv        # Oxford-Man .DJI
│       ├── btc_measures.csv         # Binance 2018→2026
│       └── eth_measures.csv
├── figures/                         # 5 figures, PNG + PDF each
├── tables/                          # 5 tables, CSV (+ LaTeX for 3 main)
└── scripts/
    ├── download_oxford_man.py
    ├── download_polygon.py          # optional; gracefully skips without POLYGON_API_KEY
    └── download_binance.py
```

## Reproducing from scratch

```bash
# 1. Python 3.12 environment
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Download source data. Oxford-Man + Binance Vision are unauthenticated;
#    the R-package datasets are fetched from CRAN; Polygon is optional.
python scripts/download_oxford_man.py
python scripts/download_binance.py
# (optional) export POLYGON_API_KEY=<key>
# python scripts/download_polygon.py

# 3. Reconstruct data/processed/ from raw (one-time, ~5 minutes)
#    The notebook also regenerates on demand if data/processed is present.
#    For a fully clean rebuild, delete data/processed/ and run the first
#    cells of harq_analysis.ipynb; they call process_oxford_man_csv()
#    and the Binance processing block.

# 4. Run the notebook
jupyter notebook harq_analysis.ipynb    # Run All
```

The notebook reads only from `data/processed/*.csv`, which *is*
committed. `git clone` + `pip install -r requirements.txt` + Run All
will reproduce every table, figure, and number in `report.pdf`.

## Data sources and provenance

| Window | Source | Notes |
| --- | --- | --- |
| 1997-05 → 2013-08 (SPX) | `HARModel::SP500RM` (Sjoerup 2019, CRAN Archive) — mirrors Patton's public code-page file for BPQ 2016 | Exact realized quarticity. This is the canonical BPQ dataset. |
| 2000-01 → 2020-02 (SPX, NDX=IXIC, RUT, DJIA) | `highfrequency` R package snapshot of the Oxford-Man Realized Library | Exact RV / BV / RSV; RQ not distributed — we use the jump-robust proxy $RQ \approx BV^2$ and flag it. |
| 2014-01 → 2019-12 (SPY) | `highfrequency::SPYRM` | Exact RQ; used as a sensitivity check on the Oxford-Man proxy |
| 2018-01 → 2026-03 (BTCUSDT, ETHUSDT) | Binance Vision public monthly archive, 1-minute klines | RV / RQ / RS± / BV computed in-notebook from 5-minute subsampled returns |
| 2024-04 → now (SPY) | Polygon.io free tier, 1-minute | Optional; requires `POLYGON_API_KEY` |

### Documented limitations

1. Oxford-Man never distributed daily RQ, so for NDX / RUT / DJIA the
   HARQ feature uses $RQ \approx BV^2$. The Polygon / SPYRM cross-check
   quantifies the proxy's distortion. HARQ's QLIKE improvement on
   NDX post-pub calm (13.6%) suggests the proxy still carries real
   information for that asset.
2. Polygon's free tier goes back ~2 years, so 2020-02 → 2024-04 is a
   data gap for US equities at 5-minute frequency. The four-regime
   analysis in §3 therefore reports only two populated regimes
   (pre-publication, post-publication calm) for SPX; COVID-onset and
   Post-COVID rows are N/A.
3. HARQ-F (BPQ's full six-feature specification) is unstable with
   plain OLS. BPQ acknowledge this and apply insanity filters; stronger
   regularization (ridge) would stabilize coefficients at the cost of
   departing from the published OLS spec.

## Attribution

All code, figures, tables, and written analysis are the author's own
work. Source datasets are redistributed under the terms of their
respective providers (Oxford-Man Realized Library archive,
Patton/BPQ/Sjoerup R packages, Binance Vision public domain, Polygon.io
terms of use where applicable).
