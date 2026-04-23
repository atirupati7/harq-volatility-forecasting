# Exploiting the Errors, Revisited

Reproduction and extension of Bollerslev, Patton, and Quaedvlieg (2016) — *Exploiting the errors: A simple approach for improved volatility forecasting* — combined with the signed-jump decomposition of Patton and Sheppard (2015). Scope is deliberately restricted to assets for which publicly-distributed **genuine realized quarticity** is available — no BV² or other proxies for RQ. US equity evaluation is SPX only (SP500RM stitched with SPYRM). Cryptocurrency cross-asset check on BTCUSDT and ETHUSDT at 1-minute frequency from Binance's public archive.

**Author.** Aprameya Tirupati · Georgia Tech · Spring 2026 (GTSF IC Quant Mentorship).

---

## Headline findings

- **HARQ family dominates HAR in BPQ's pre-publication regime on SPX** (n = 3,075 days, 2000-2013 on SP500RM). HARQ-F QLIKE 0.1284 vs HAR 0.1495 (−14.1%), HARQ 0.1314 (−12.1%), SHAR 0.1296 (−13.3%), **HARQ-Signed 0.1256 (−16.0%, the lowest of all models)**. The 90% Model Confidence Set retains exactly {SHAR, HARQ, HARQ-F}.
- **HARQ-Signed, the novel extension,** recovers β_Q = −3.4×10³ and β₋ − β₊ = +1.10 in-sample, beats HARQ by 4.6% in walk-forward QLIKE on SPX pre-publication with DM p = 2.5×10⁻⁵.
- **NGBoost-HARQ** delivers 96.9% empirical coverage at a 95% nominal target on SPY 2014-2019, versus 99.5% for a naive HARQ + Gaussian-residual baseline. CRPS roughly halved.
- **Post-publication calm regime (SPYRM 2014-2019)** does *not* reproduce HARQ's edge: HARQ is +2.8% worse than HAR on QLIKE and the MCS retains all five evaluable models. SHAR and HARQ-Signed are not evaluated because SPYRM does not distribute positive/negative semivariances.
- **Crypto check fails the microstructure-noise hypothesis.** HARQ beats HAR by 12.3% on SPX pre-pub but only 7% on BTC/ETH. Signed-jump asymmetry helps on SPX and vanishes in 24/7 crypto.

## Papers reproduced and extended

- Bollerslev, T., Patton, A. J., & Quaedvlieg, R. (2016). Exploiting the errors. *Journal of Econometrics*, 192(1), 1–18.
- Patton, A. J., & Sheppard, K. (2015). Good volatility, bad volatility. *Review of Economics and Statistics*, 97(3), 683–697.
- Corsi, F. (2009). A simple approximate long-memory model of realized volatility. *Journal of Financial Econometrics*, 7(2), 174–196.
- Duan, T. et al. (2020). NGBoost. *ICML 2020*.
- Hansen, P. R., Lunde, A., & Nason, J. M. (2011). The Model Confidence Set. *Econometrica*, 79(2), 453–497.

## Repository layout

```
harq-volatility-forecasting/
├── README.md                      # this file
├── PROJECT_WRITEUP.md             # standalone 4,700-word writeup
├── requirements.txt
├── harq_analysis.ipynb            # primary deliverable
├── report.md / report.pdf         # two-page final report
├── slide_spec.md                  # text spec for Gemini to render slide
├── data/
│   ├── raw/                       # NOT committed; reconstructible
│   └── processed/                 # committed: spx, btc, eth measures
├── figures/                       # 5 figures × (PNG + PDF)
├── tables/                        # 5 tables as CSV + 3 as LaTeX
└── scripts/                       # 2 download scripts (Binance, Polygon)
```

## Reproducing from scratch

```bash
# 1. Python 3.12 environment
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Download source data. Binance is unauthenticated; the R-package datasets
#    (SP500RM.RData, SPYRM.rda) are fetched from the CRAN archive.
python scripts/download_binance.py
# (optional) export POLYGON_API_KEY=<key>
# python scripts/download_polygon.py

# 3. Open and run the notebook
jupyter notebook harq_analysis.ipynb    # Run All
```

The notebook reads only from `data/processed/*.csv`, which *is* committed. A clone + `pip install -r requirements.txt` + Run All reproduces every table, figure, and number in `report.pdf`.

## Data sources and provenance

| Window | Source | Notes |
| --- | --- | --- |
| 1997-05 → 2013-08 (SPX) | `HARModel::SP500RM` (Sjoerup 2019, CRAN Archive; Patton's BPQ-2016 code page) | Exact realized quarticity. Canonical BPQ dataset. |
| 2014-01 → 2019-12 (SPY) | `highfrequency::SPYRM` (Cornelissen's package, CRAN) | Exact RQ from 5-minute returns; no positive/negative semivariances. |
| 2018-01 → 2026-03 (BTCUSDT, ETHUSDT) | Binance Vision public monthly archive, 1-minute klines | RV / RQ / RS± / BV computed in-notebook from 5-minute subsampled returns. |
| 2024-04 → now (SPY, optional) | Polygon.io free tier, 1-minute | Requires `POLYGON_API_KEY`; not used in the executed build. |

### Scope decision

The evaluation is restricted to assets for which publicly-distributed *genuine* realized quarticity is available. Extending to NDX, RUT, or DJIA would require paid minute-level data (Polygon Stocks Starter tier or equivalent) and was rejected to preserve methodological cleanliness over breadth. The Oxford-Man Realized Library archive was considered as a source but explicitly not used because its BV² proxy for RQ distorts HARQ's interaction coefficient.

## Attribution

All code, figures, tables, and written analysis are the author's own work. Source datasets are redistributed under the terms of their respective providers (`HARModel` and `highfrequency` R packages; Binance Vision; Polygon.io terms of use where applicable).
