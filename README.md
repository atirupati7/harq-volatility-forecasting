# Exploiting the Errors, Revisited

Reproduction and extension of Bollerslev, Patton, and Quaedvlieg (2016) —
*Exploiting the errors: A simple approach for improved volatility forecasting*
— combined with the signed-jump decomposition of Patton and Sheppard (2015) —
*Good volatility, bad volatility*. Post-2013 out-of-sample evaluation, a novel
HARQ-Signed specification, a probabilistic NGBoost extension, and a crypto
cross-asset check.

**Author:** Aprameya Tirupati · Georgia Tech · Spring 2026
(GTSF IC Quant Mentorship final project)

---

## Papers reproduced and extended

- Bollerslev, T., Patton, A. J., & Quaedvlieg, R. (2016). "Exploiting the
  errors: A simple approach for improved volatility forecasting." *Journal of
  Econometrics*, 192(1), 1–18.
- Patton, A. J., & Sheppard, K. (2015). "Good volatility, bad volatility:
  Signed jumps and the persistence of volatility." *Review of Economics and
  Statistics*, 97(3), 683–697.
- Corsi, F. (2009). "A simple approximate long-memory model of realized
  volatility." *Journal of Financial Econometrics*, 7(2), 174–196.
- Duan, T. et al. (2019). "NGBoost: Natural Gradient Boosting for
  Probabilistic Prediction." *ICML*.
- Hansen, P. R., Lunde, A., & Nason, J. M. (2011). "The Model Confidence
  Set." *Econometrica*, 79(2), 453–497.

## Repository layout

```
harq-volatility-forecasting/
├── README.md                    # this file
├── requirements.txt             # pinned deps
├── harq_analysis.ipynb          # primary deliverable — runs end-to-end
├── report.md / report.pdf       # 2-page final report
├── slide_spec.md                # text spec for Gemini to render slide
├── data/
│   ├── raw/                     # downloaded sources (NOT committed; reconstructible)
│   └── processed/               # realized measures per asset (committed)
├── figures/                     # 5 figures as PNG + PDF
├── tables/                      # 3 tables as CSV + LaTeX
└── scripts/                     # data download scripts only
```

## Reproducing from scratch

```bash
# 1. Clone and create environment
git clone <this-repo> harq-volatility-forecasting
cd harq-volatility-forecasting
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Download source data (Oxford-Man + Binance are unauthenticated;
#    Polygon needs a free API key at https://polygon.io)
python scripts/download_oxford_man.py
python scripts/download_binance.py
export POLYGON_API_KEY=<your_key>      # see https://polygon.io (free tier OK)
python scripts/download_polygon.py

# 3. Open and Run All
jupyter notebook harq_analysis.ipynb
```

The notebook reads only from `data/processed/*.csv`, which is committed.
Steps 1 and 3 alone will execute the full analysis from a fresh clone.
Step 2 is only required if you want to rebuild `data/processed/` from raw.

## Data sources and provenance

| Window | Source | Notes |
| --- | --- | --- |
| 2000-01-03 to 2020-02-21 | Oxford-Man Realized Library mirror (`jonathancornelissen/highfrequency`) | Daily RV5, BV, RSV. The original Oxford-Man service was discontinued; we use the archived CSV shipped with the `highfrequency` R package. |
| 2024-04 to present | Polygon.io free tier, 1-minute SPY | Compute RV / RQ / RS± / BV directly from 5-minute subsampled returns. |
| 2018-01 to present | Binance public REST, 1-minute BTCUSDT/ETHUSDT | All measures computed from scratch; 24/7 market, no overnight gap. |

### Documented data limitations

1. **Oxford-Man does not distribute daily realized quarticity (RQ).** RQ
   requires raw 5-minute returns, which the library only aggregates. For the
   2000–2020 window we use the proxy `RQ ≈ RV²`, exact under a no-jump
   diffusion null. For the Polygon and Binance windows, we compute RQ
   directly from 5-minute intraday returns. The notebook cross-validates the
   proxy against the exact RQ on the overlap window.
2. **Signed semivariance:** Oxford-Man's `rsv` is the negative-return
   component (*RS⁻*). We derive `RS⁺ = RV5 − RSV`.
3. **Regime gap 2020-02-22 → 2024-04:** Polygon's free tier provides ~2
   years of history, leaving a ~4-year gap that covers the acute COVID
   volatility period and the 2022 bear market. Post-2020 US-equity
   out-of-sample evaluation is limited to the 8-month Polygon window. The
   BTC / ETH analysis is not affected (Binance coverage is continuous). This
   limitation is reported honestly in `report.pdf`.

## Key findings

*To be populated on completion.*

## License / attribution

Code is the author's own. Oxford-Man data is re-distributed under the terms of
the original library. Polygon and Binance data are subject to their
respective terms of use.
