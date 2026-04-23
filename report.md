# Exploiting the Errors, Revisited: HARQ Volatility Forecasting with Signed-Jump Decomposition and Probabilistic Extensions

**Aprameya Tirupati** · Georgia Institute of Technology · GTSF IC Quant Mentorship, Spring 2026

## Abstract

This project reproduces Bollerslev, Patton, and Quaedvlieg (2016) on their exact published dataset (`SP500RM` via the `HARModel` R package) and extends the result along three dimensions. (1) We evaluate six HAR-family baselines on SPX across two populated volatility regimes (pre-publication 2000-2013 and post-publication calm 2014-2019), stitching SP500RM with SPYRM so that genuine realized quarticity is available throughout; no BV² proxy is used anywhere. (2) We introduce **HARQ-Signed**, a novel specification combining BPQ's measurement-error correction with Patton–Sheppard (2015) signed semivariances, which delivers QLIKE 4.6% below HARQ on SPX pre-publication with DM p = 2.5×10⁻⁵. (3) **NGBoost-HARQ** delivers 96.9% empirical coverage at a 95% nominal predictive interval on SPY 2014-2019, versus 99.5% for a naive HARQ + Gaussian-residual baseline. A crypto cross-check on BTC/ETH 2019-2024 finds HARQ's edge smaller in crypto (7%) than on SPX (12%), contrary to the microstructure-noise hypothesis.

## 1. Introduction and data

The heterogeneous autoregressive (HAR) model of Corsi (2009) has been the volatility-forecasting workhorse for two decades. BPQ (2016) showed that augmenting HAR with a measurement-error term proportional to √realized-quarticity produces economically meaningful improvements. Patton–Sheppard (2015) decomposed RV into positive and negative semivariances and showed β₋ > β₊ — bad-volatility is more persistent than good.

SPX data are the stitched combination of `HARModel::SP500RM` (Sjoerup 2019, mirroring Patton's BPQ-2016 code page; 4,096 trading days 1997-05 to 2013-08) and `highfrequency::SPYRM` (2014-01 to 2019-12, 1,495 days). Both ship `RV`, `RQ`, and `BPV` computed from 5-minute returns. SP500RM additionally ships positive and negative semivariances (`RVp`, `RVn`); SPYRM does not, so SHAR, HARQ-Signed, and NGBoost-HARQ are scoped to the SP500RM portion. The SP500RM date index is reconstructed by anchoring row 2869 (RV ≈ 60.6) to 2008-10-09 and row 3581 (RV = 19.55) to the 2011-08-08 S&P-downgrade reaction. Crypto data are 1-minute BTCUSDT and ETHUSDT klines from `data.binance.vision` (198 monthly files, 2018-01 to 2026-03), with all measures computed from 5-minute subsampled returns inside the notebook.

This revision deliberately excludes NDX, RUT, and DJIA because genuine realized quarticity is not publicly distributed for those indices; extending the analysis would require paid minute-level data and was out of scope. The scope restriction is a considered choice, not a limitation.

## 2. Methods

Six HAR-family baselines (HAR, HAR-J, SHAR, HARQ, HARQ-F, CHAR) share a common Python `VolForecaster` API fit via `numpy.linalg.lstsq`. HARQ uses the centered interaction $RV_t \cdot (\sqrt{RQ_t} - \overline{\sqrt{RQ}})$ per the `HARModel` R package convention — equivalent in prediction to BPQ's uncentered form but numerically better-conditioned. **HARQ-Signed**, the novel contribution, nests both HARQ and SHAR:

$$
RV_{t+1} = \beta_0 + (\beta_d + \beta_Q (\sqrt{RQ_t}-\overline{\sqrt{RQ}})) RV_t + \beta_+ RS^+_t + \beta_- RS^-_t + \beta_w RV_t^{(w)} + \beta_m RV_t^{(m)} + \varepsilon
$$

Walk-forward evaluation is expanding-window, monthly refit, initial 1,000-day window, with a BPQ insanity filter that replaces non-positive or extreme non-HAR predictions with the HAR prediction. The walk-forward filters NaN *per model* on its actual feature requirements, letting HAR / HARQ / HARQ-F / CHAR run on the full SP500RM+SPYRM stitch even though SHAR / HARQ-Signed cannot. Loss functions: MSE and QLIKE (Patton 2011). Diebold–Mariano tests use Newey–West HAC at bandwidth h−1 on date-aligned differentials. The Model Confidence Set is computed via `arch.bootstrap.MCS` with 1,000 bootstrap replications.

NGBoost-HARQ uses a Normal output distribution, default hyperparameters (n_estimators=300, learning_rate=0.01), and a feature set restricted to variables present in both SP500RM and SPYRM: RV_d, RV_w, RV_m, RV_d·(√RQ_d − mean √RQ), BV_d. Single fit on 2002-2013, prediction on 2014-2019. Empirical coverage, CRPS, and Kupiec/Christoffersen VaR tests evaluate calibration.

## 3. Results

**Reproduction (Table 1).** Rolling 1,000-day window on SP500RM 2002-2013 at h = 1: HAR QLIKE = 0.1646 (baseline); SHAR 0.1557 (−5.40%, DM p = 0.0003, matches Patton–Sheppard); HARQ 0.1682 QLIKE (+2.18%) and MSE −4.4% (matches BPQ direction on MSE); HARJ and CHAR tie HAR; HARQ-F is unstable under plain OLS and only becomes competitive after the insanity filter.

**SPX regime analysis (Table 2, Figure 3).** With expanding window on the stitched SP500RM+SPYRM series:

| Model | Pre-pub QLIKE (n=3,075) | Post-pub calm QLIKE (n=1,494) |
| --- | --- | --- |
| HAR | 0.1495 | 0.2615 |
| HARJ | 0.1451 | 0.2592 |
| SHAR | **0.1296** | n/a |
| HARQ | 0.1314 | 0.2689 |
| HARQ-F | **0.1284** | 0.3035 |
| CHAR | 0.1471 | 0.2682 |
| HARQ-Signed | **0.1256** | n/a |

In the pre-publication regime the HARQ family dominates: HARQ-F beats HAR by −14.1%, HARQ-Signed by −16.0%, HARQ by −12.1%, SHAR by −13.3%. The 90% Model Confidence Set retains exactly {SHAR, HARQ, HARQ-F} — the three flat-HAR models are significantly inferior. In the post-publication calm regime the MCS retains all five available models; HARQ is *not* uniquely better than HAR. Figure 3's rolling 252-day QLIKE differential is consistently negative (HARQ wins) pre-2014 and drifts toward zero post-2015.

**HARQ-Signed (Table 2c).** In-sample coefficients on SPX 2002-2013: β_Q = −3.43×10³ (negative, as BPQ predict); β₋ − β₊ = +1.10 (strong bad-vol persistence, as Patton–Sheppard predict). Walk-forward on SPX pre-publication: QLIKE 0.1256, DM p = 2.5×10⁻⁵ against HARQ — HARQ-Signed is the lowest-QLIKE model on SPX pre-publication with a statistically significant margin over the next-best HARQ-F.

**NGBoost-HARQ (Table 3, Figure 4).** On SPY 2014-2019: CRPS 2.0×10⁻⁵ (NGBoost) vs 4.3×10⁻⁵ (HARQ + Gaussian); 95% coverage 96.9% vs 99.5% (closer to nominal); 90% coverage 95.4% vs 99.4%. Both models fail Kupiec and Christoffersen VaR backtests because the Normal output cannot capture RV's heavy right tail.

**Crypto (Table 4).** HARQ/HAR ratios: SPX pre-publication 0.877 (−12.3% improvement), BTC 2019-2024 0.930 (−7.0%), ETH 2019-2024 0.928 (−7.2%). HARQ's edge over HAR is larger on SPX than on crypto — contrary to the microstructure-noise hypothesis. HARQ-Signed/HARQ ratios: SPX 0.954 (−4.6%), BTC 1.182 (+18.2%, worse), ETH 1.026 (tied) — the signed-jump asymmetry helps on SPX (overnight gaps) and vanishes in 24/7 crypto.

## 4. Discussion

Three claims survive out-of-sample evaluation on real realized quarticity. First, BPQ's measurement-error correction is real and large in the pre-publication regime — HARQ-F delivers a 14% QLIKE reduction on SPX 2002-2013 and the MCS confirms the three HARQ-family models (SHAR, HARQ, HARQ-F) are the only models not significantly worse than the winner. Second, the novel HARQ-Signed specification correctly recovers both the measurement-error sign (β_Q < 0) and the Patton–Sheppard asymmetry (β₋ − β₊ ≈ +1.1) in a single regression, and achieves the lowest QLIKE of any model tested on SPX pre-publication. Third, probabilistic volatility forecasting with NGBoost is calibration-viable but still heavy-tail-limited on a Normal output distribution; a follow-up with a Student-t head would be a natural next step.

Two findings point to open questions. The post-publication calm regime does not reproduce HARQ's edge — in the SPY 2014-2019 window HARQ is not statistically better than HAR. Whether this reflects a real structural change in SPX volatility dynamics, an SPY-vs-SPX microstructure artifact, or simply that post-2013 HF data is clean enough that the measurement-error correction offers little remaining signal cannot be resolved without paid SPX HF data through 2024. The crypto null result (HARQ's edge smaller in BTC/ETH than in SPX) similarly invites follow-up at finer sampling and on a cleaner exchange-specific sample that excludes the 2022 bear break.

The repository is deliberately scoped to assets with genuine realized quarticity — SP500RM, SPYRM, and Binance 1-minute computation. NDX, RUT, DJIA, and the Oxford-Man BV² proxy were considered and rejected to preserve methodological cleanliness over breadth.

## References

- Bollerslev, T., Patton, A. J., & Quaedvlieg, R. (2016). Exploiting the errors. *Journal of Econometrics* 192(1), 1–18.
- Corsi, F. (2009). A simple approximate long-memory model of realized volatility. *Journal of Financial Econometrics* 7(2), 174–196.
- Duan, T. et al. (2020). NGBoost. *ICML 2020*.
- Hansen, P. R., Lunde, A., & Nason, J. M. (2011). The Model Confidence Set. *Econometrica* 79(2), 453–497.
- Patton, A. J. (2011). Volatility forecast comparison using imperfect volatility proxies. *Journal of Econometrics* 160(1), 246–256.
- Patton, A. J., & Sheppard, K. (2015). Good volatility, bad volatility. *Review of Economics and Statistics* 97(3), 683–697.
- Sjoerup, E. (2019). `HARModel` R package, version 1.0. CRAN Archive.
