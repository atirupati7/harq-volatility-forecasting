# Exploiting the Errors, Revisited

Reproduction and extension of Bollerslev, Patton, and Quaedvlieg (2016) — *Exploiting the errors: A simple approach for improved volatility forecasting* — combined with the signed-jump decomposition of Patton and Sheppard (2015). Scope is deliberately restricted to the S&P 500 index using the exact SP500RM dataset distributed by BPQ plus the SPYRM post-publication window, so that every evaluation uses publicly-distributed **genuine realized quarticity** (no BV² or other proxies).

**Author.** Aprameya Tirupati · Georgia Tech · Spring 2026 (GTSF IC Quant Mentorship).

---

## Headline findings

- **HARQ family dominates HAR in BPQ's pre-publication regime on SPX** (n = 3,075 days, 2000-2013 on SP500RM). HARQ-F QLIKE 0.1284 vs HAR 0.1495 (−14.1%), HARQ 0.1314 (−12.1%), SHAR 0.1296 (−13.3%), **HARQ-Signed 0.1256 (−16.0%, the lowest of all models)**. The 90% Model Confidence Set retains exactly {SHAR, HARQ, HARQ-F}.
- **HARQ-Signed, the novel extension,** recovers β_Q = −3.4×10³ and β₋ − β₊ = +1.10 in-sample, beats HARQ by 4.6% in walk-forward QLIKE on SPX pre-publication with DM p = 2.5×10⁻⁵.
- **NGBoost-HARQ** delivers 96.9% empirical coverage at a 95% nominal target on SPY 2014-2019, versus 99.5% for a naive HARQ + Gaussian-residual baseline. CRPS roughly halved.
- **Post-publication calm regime (SPYRM 2014-2019)** does *not* reproduce HARQ's edge: HARQ is +2.8% worse than HAR on QLIKE and the MCS retains all five evaluable models. SHAR and HARQ-Signed are not evaluated because SPYRM does not distribute positive/negative semivariances.

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
├── report.tex / references.bib    # LaTeX source for the final report
├── report.pdf                     # compiled 3-page final report
├── report.md                      # content source (kept as a readable reference)
├── slide_spec.md                  # text spec for Gemini to render slide
├── data/
│   ├── raw/                       # NOT committed; reconstructible
│   └── processed/                 # committed: spx_measures.csv
├── figures/                       # 5 figures × (PNG + PDF)
├── tables/                        # 4 tables as CSV + 3 as LaTeX
└── scripts/                       # 1 download script (Polygon, optional)
```

## Reproducing from scratch

**Prerequisites.** Python 3.12 and a LaTeX distribution (TeX Live, MacTeX, or equivalent) for compiling the report. The build was developed against [tectonic](https://tectonic-typesetting.github.io/), which handles bibtex internally in a single pass; `pdflatex` + `bibtex` also work.

```bash
# 1. Python 3.12 environment
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Processed SPX measures are already committed under data/processed/. The
#    R-package datasets (SP500RM.RData, SPYRM.rda) are redistributable from
#    the CRAN archive if you need to rebuild the stitched CSV from raw.
# (optional) export POLYGON_API_KEY=<key>
# python scripts/download_polygon.py

# 3. Open and run the notebook (reproduces tables, figures, and processed CSVs)
jupyter notebook harq_analysis.ipynb    # Run All

# 4. Compile the LaTeX report. Tectonic is a one-shot build:
tectonic report.tex
# Or, with a traditional TeX Live install, the standard triple-compile:
#   pdflatex report.tex && bibtex report && pdflatex report.tex && pdflatex report.tex
```

The notebook reads only from `data/processed/*.csv`, which *is* committed. A clone + `pip install -r requirements.txt` + Run All reproduces every table, figure, and number in `report.pdf`.

## Data sources and provenance

| Window | Source | Notes |
| --- | --- | --- |
| 1997-05 → 2013-08 (SPX) | `HARModel::SP500RM` (Sjoerup 2019, CRAN Archive; Patton's BPQ-2016 code page) | Exact realized quarticity. Canonical BPQ dataset. |
| 2014-01 → 2019-12 (SPY) | `highfrequency::SPYRM` (Cornelissen's package, CRAN) | Exact RQ from 5-minute returns; no positive/negative semivariances. |
| 2024-04 → now (SPY, optional) | Polygon.io free tier, 1-minute | Requires `POLYGON_API_KEY`; not used in the executed build. |

### Scope decision

The evaluation is restricted to assets for which publicly-distributed *genuine* realized quarticity is available. Extending to NDX, RUT, or DJIA would require paid minute-level data (Polygon Stocks Starter tier or equivalent) and was rejected to preserve methodological cleanliness over breadth. The Oxford-Man Realized Library archive was considered as a source but explicitly not used because its BV² proxy for RQ distorts HARQ's interaction coefficient.

## Attribution

All code, figures, tables, and written analysis are the author's own work. Source datasets are redistributed under the terms of their respective providers (`HARModel` and `highfrequency` R packages; Polygon.io terms of use where applicable).
