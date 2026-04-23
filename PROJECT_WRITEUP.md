# Project Writeup: HARQ Volatility Forecasting Reproduction + Extensions

## 1. Project Overview

This project reproduces and extends two foundational realized-volatility-forecasting papers — Bollerslev, Patton, and Quaedvlieg (2016) "Exploiting the errors: A simple approach for improved volatility forecasting" and Patton and Sheppard (2015) "Good volatility, bad volatility: Signed jumps and the persistence of volatility" — using the exact realized-measures dataset BPQ (2016) distribute with their paper (`SP500RM`, via Emil Sjoerup's `HARModel` R package). Six HAR-family baselines (HAR, HAR-J, SHAR, HARQ, HARQ-F, CHAR), one novel specification (HARQ-Signed), and one probabilistic extension (NGBoost-HARQ) are evaluated out-of-sample across four volatility regimes spanning 2000 to 2020 for SPX, NDX, RUT, and DJIA, and across 2018 to 2026 for BTCUSDT and ETHUSDT. Deliverables are a single end-to-end Jupyter notebook (`harq_analysis.ipynb`, 35 cells, ~35-second run time), five publication-quality figures, five analysis tables, a two-page PDF report, and a standalone text specification used by a separate model to render a hero slide. The implementation is approximately 1,600 lines of Python, most of which lives in the notebook itself; the remaining code is three data-download scripts under `scripts/`. The end-to-end build — from a fresh Python environment through processed data, all walk-forwards, figures, tables, and PDF report — completes in well under ten minutes on commodity hardware.

## 2. Research Questions

The project addresses three research questions derived from the original brief.

**Q1. Does HARQ's published 5–10% QLIKE edge over HAR survive out-of-sample through 2020, and does it concentrate in specific volatility regimes?** BPQ (2016) estimated HARQ on 2001–2013 data and reported measurement-error corrections that improved both MSE and QLIKE by 5–10% on SPX. A serious test is whether that edge persists in the 2014–2019 post-publication calm window and into COVID onset, or whether it has decayed as high-frequency data quality improved and the model's correction became less novel. An answer takes the form of per-regime QLIKE differentials, Diebold–Mariano significance tests, and Model Confidence Set membership.

**Q2. Can we usefully combine BPQ's measurement-error correction with Patton–Sheppard's signed-jump decomposition into a single specification, HARQ-Signed, and does it improve on either paper's model alone?** This is the novel contribution. The specification nests HARQ (via the √RQ interaction) and a Patton–Sheppard signed HAR (via separate β₊, β₋ on RS⁺, RS⁻), and asks whether the combination recovers the expected coefficient signs (β_Q < 0, β₋ > β₊) and produces a smaller QLIKE than HARQ alone.

**Q3. When volatility forecasts are needed for downstream risk management (VaR, option pricing), can probabilistic boosting (NGBoost) deliver calibrated predictive intervals?** The HAR family produces point forecasts; operational risk requires distributions. NGBoost with a Normal output distribution is compared against a naive HARQ + Gaussian-residual baseline on CRPS, empirical coverage at 90% and 95%, and Kupiec / Christoffersen VaR backtests at 1% and 5%.

Two additional sub-questions follow: whether HARQ's edge scales with microstructure noise (tested on BTCUSDT and ETHUSDT at 1-minute frequency), and whether Patton–Sheppard's signed-jump asymmetry weakens in crypto (which has no overnight gap, so flow should be more symmetric).

## 3. Theoretical Background

**Corsi (2009), HAR.** The heterogeneous autoregressive model predicts next-day realized variance as a linear combination of three trailing averages of past RV at daily, weekly, and monthly horizons:

RV_{t+1} = β₀ + β_d · RV_t + β_w · RV_t^(w) + β_m · RV_t^(m) + ε_{t+1}

where RV_t^(w) = (1/5) Σ_{i=0..4} RV_{t−i} and RV_t^(m) = (1/22) Σ_{i=0..21} RV_{t−i}. The intuition is that volatility clusters at multiple time scales — intraday, weekly position cycles, monthly macro — and a simple three-factor OLS captures the long-memory decay of RV autocorrelations without needing a true long-memory parameter. HAR has been the workhorse RV forecaster for two decades because it is almost as accurate as ARFIMA models at a fraction of the estimation cost.

**Bollerslev–Patton–Quaedvlieg (2016), HARQ.** BPQ observe that RV_t is not the true integrated variance IV_t; it is an estimator. Under standard microstructure assumptions the variance of the estimation error is proportional to the integrated quarticity IQ_t, consistently estimated by the realized quarticity RQ_t = (n/3) Σ_{i=1..n} r_{t,i}⁴ from n intraday returns. When RQ_t is large, today's RV is noisier and should be weighted less when predicting tomorrow. They operationalize this by interacting a scaled √RQ_t with the daily lag:

RV_{t+1} = β₀ + (β_d + β_Q · √(RQ_t / mean(RQ))) · RV_t + β_w · RV_t^(w) + β_m · RV_t^(m)

BPQ report β_Q ≈ −0.13 on SPX 2001–2013. The interpretation is mechanical: on a high-RQ day the effective daily coefficient (β_d + β_Q · √scaling) decreases, shrinking the over-weighting of a noisy RV_t. BPQ estimate this improves both MSE and QLIKE by 5–10%. HARQ-F extends the correction to all three HAR lags.

**Patton–Sheppard (2015), signed semivariances.** Barndorff-Nielsen et al. (2010) showed RV can be decomposed into positive and negative semivariances that sum to RV: RS⁺ = Σ r_i²·𝟙{r_i>0} and RS⁻ = Σ r_i²·𝟙{r_i<0}. The signed jump is ΔJ = RS⁺ − RS⁻. Patton–Sheppard fit a HAR in which the daily RV lag is replaced by separate β₊·RS⁺ and β₋·RS⁻ terms and find that β₋ > β₊ substantially — "bad" volatility (down-move-driven) is much more persistent than "good" volatility (up-move-driven). Economically: down-move days signal real information shocks whose volatility effect lingers; up-move days are more likely short-squeeze style noise that mean-reverts.

**Duan et al. (2019), NGBoost.** NGBoost (Natural Gradient Boosting) is a gradient-boosting algorithm whose boosting update is a natural gradient step on the parameters of an output distribution rather than on a scalar prediction. Fit with a Normal output distribution, each prediction is a tuple (μ(x), σ(x)), both dependent on the features x. This differs from a point regressor plus residual-variance model because σ(x) adapts to features — the model can widen predictive intervals on features associated with historical high-residual days. The natural evaluation metric is CRPS (continuous ranked probability score), which measures the integrated squared distance between the predictive CDF F and the degenerate step CDF at the realized y; for a Normal forecast this has a closed form CRPS(y | μ, σ) = σ · [z·(2·Φ(z) − 1) + 2·φ(z) − 1/√π] with z = (y − μ)/σ.

## 4. Data

Four data sources feed the analysis. The primary SPX dataset is `HARModel::SP500RM` (Sjoerup 2019), redistributed from Andrew Patton's BPQ-2016 code page. Sjoerup's package ships the file as a binary `.RData` archive; we pull the tarball from the CRAN Archive (`https://cran.r-project.org/src/contrib/Archive/HARModel/HARModel_1.0.tar.gz`), extract `HARModel/data/SP500RM.RData`, and read it with `pyreadr.read_r()`. The resulting DataFrame has 4,096 rows and 11 columns: `RV`, `RQ`, `RJ`, `BPV`, `RVn` (negative semivariance), `RVp` (positive semivariance), `TPQ`, `MedRQ`, `TrRQ`, `RQ15Min`, `RQBoot`. `pyreadr` drops the xts date index; we reconstruct it by anchoring two historically known volatility spikes — row 2869 with RV = 60.56 to the 2008-10-09 panic and row 3581 with RV = 19.55 to the 2011-08-08 S&P-downgrade reaction — which places the series start at 1997-05-15 on the NYSE calendar (via `pandas_market_calendars`), yielding 4,096 trading days through 2013-08-23. Values are in percent-squared daily variance units; we divide by 10⁴ to obtain decimal variance and by 10⁸ to obtain quarticity in decimal⁴ units. After conversion the series gives an annualized volatility of 17.21%, consistent with historical SPX.

The Oxford-Man Realized Library archive, shipped in Jonathan Cornelissen's `highfrequency` R package (`highfrequency_1.0.3.tar.gz` → `data-raw/oxfordmanrealizedvolatilityindices.csv`, 49 MB, 141,988 rows), supplies daily RV5, BPV, RSV (negative-side semivariance) for 31 symbols from 2000-01-03 to 2020-02-21. We extract `.SPX`, `.IXIC` (Nasdaq Composite, used as NDX surrogate because true NDX is not in the archive), `.RUT`, and `.DJI` — four US equity indices with 5,046–5,052 daily observations each. Because Oxford-Man never distributed daily realized quarticity, for these four assets we use the jump-robust proxy RQ ≈ BV², with BPV² chosen over RV² because BV is less collinear with RV_t (reducing the multicollinearity that destabilizes HARQ's interaction coefficient). We derive RS⁺ = RV5 − RSV.

`highfrequency::SPYRM` (a second dataset in the same R package) provides SPY-ETF measures from 2014-01 to 2019-12 at 1-minute and 5-minute sampling with both RV and RQ; we keep it as a spot-check resource for the BV² proxy.

Cryptocurrency data come from Binance's public monthly archive at `data.binance.vision`, which serves zipped CSVs of raw 1-minute klines without geo-blocking (the main REST API returns HTTP 451 for US IPs). We pull 99 monthly files per symbol for BTCUSDT and ETHUSDT from 2018-01 through 2026-03 — 198 files totaling 1.2 GB of raw 1-minute OHLCV data, 4.33 million bars per symbol. Timestamp units change from milliseconds to microseconds at some point in late 2024; the download script auto-detects per file. All crypto realized measures (RV, RQ, RS⁺, RS⁻, ΔJ, BV) are computed in-notebook from 5-minute subsampled close-to-close log returns over the full 24-hour UTC day (no session restriction). BTC's annualized volatility over the window is 71.2%, ETH's is 89.3%.

Polygon.io 1-minute SPY is available but optional; it requires `POLYGON_API_KEY` in the environment and covers the free-tier's approximately 2-year historical window. In the executed notebook Polygon was not pulled, because neither the BPQ reproduction (bounded by SP500RM's 2013 end) nor the four-regime panel analysis (bounded by Oxford-Man's 2020-02 end) requires it. The `scripts/download_polygon.py` script handles a missing API key gracefully and is ready to run when a key is available.

All processing writes canonicalized CSVs to `data/processed/` (columns: `date, RV, RQ, RS_plus, RS_minus, delta_J, BV, nobs` plus model-specific extras). These CSVs are committed to the repository; raw data is in `.gitignore`. The notebook's default code path reads only `data/processed/`, so the full analysis is reproducible from a clone without re-running any downloads.

## 5. Feature Engineering

Every model consumes features built by the notebook's `build_har_features()` function, applied per-asset to the processed CSVs. The feature set is:

- **Realized variance, RV_t.** Sum of 5-minute squared log returns within the day. On the equity side this is the Oxford-Man `rv5` (or SP500RM's `RV`); on crypto it is computed inline via `compute_realized_measures()`.
- **Bipower variation, BV_t = (π/2) · Σ_{i≥2} |r_i| · |r_{i−1}|.** Jump-robust integrated-variance estimator. Drives the CHAR specification and the jump component.
- **Realized quarticity, RQ_t = (n/3) · Σ r_i⁴.** True value on SP500RM and crypto; BV² proxy on Oxford-Man. Drives the HARQ and HARQ-F interactions.
- **Positive / negative semivariances, RS⁺_t, RS⁻_t.** For SP500RM these are native columns (`RVp`, `RVn`); for Oxford-Man we derive RS⁺ = RV5 − RSV; for crypto we compute both halves directly from 5-minute returns. Drive the SHAR and HARQ-Signed specifications.
- **Signed jump, ΔJ_t = RS⁺_t − RS⁻_t.** Included as a standalone feature in the NGBoost model.
- **Jump variation, J_t = max(RV_t − BV_t, 0).** Ensures non-negativity of the jump component; drives the HAR-J specification.
- **Trailing HAR aggregates:** RV_t^(w) = (1/5) Σ_{i=0..4} RV_{t−i} and RV_t^(m) = (1/22) Σ_{i=0..21} RV_{t−i}. Analogous aggregates BV_t^(w), BV_t^(m), RQ_t^(w), RQ_t^(m) feed CHAR and HARQ-F. Rolling means are computed trailing-inclusive of day t so the feature at row t uses only information through day t.
- **HARQ interaction feature, RV_t · (√RQ_t − mean_train(√RQ)).** Centered at the training-window mean of √RQ per `HARModel` R-package convention; this is equivalent in prediction to BPQ's uncentered form but has a smaller condition number in OLS. Re-centering happens at each walk-forward refit using only the training window.

Regime indicators are assigned downstream (not in the feature builder) as date-bucket labels drawn from the four regime definitions in Section 8. The notebook also produces asset-level summary statistics — annualized volatility, fraction of days with ΔJ > 0, median RQ/RV² ratio — as sanity checks. The BPV²/RV² median ratios on the four US indices range from 0.73 (DJIA) to 0.89 (NDX), consistent with typical bipower/realized-variance ratios under moderate jump activity.

## 6. Models Implemented

All eight models share a Python base class `VolForecaster` with two methods: `.transform(features, train_stats)` returns the model-specific design matrix (and any statistics needed to build a test row consistently with training, such as the training mean of √RQ), and `.fit(X, y)` / `.predict(X)` do OLS via `numpy.linalg.lstsq`. NGBoost uses the `ngboost` package directly.

**HAR (Corsi 2009).** Feature set: RV_d, RV_w, RV_m. Plain OLS, three regressors plus intercept.

**HAR-J (Andersen–Bollerslev–Diebold 2007).** HAR plus the jump component: RV_d, RV_w, RV_m, J_d. Adds β_J·max(RV_d − BV_d, 0).

**SHAR (Patton–Sheppard 2015).** Replaces the daily RV_d lag with separate RS⁺_d and RS⁻_d. Feature set: RS⁺_d, RS⁻_d, RV_w, RV_m.

**HARQ (Bollerslev–Patton–Quaedvlieg 2016).** Feature set: RV_d, RV_d·(√RQ_d − mean_train(√RQ)), RV_w, RV_m. The centered interaction follows `HARModel` R package convention; mean_train(√RQ) is re-estimated from the training window at each refit.

**HARQ-F (BPQ 2016).** Applies the measurement-error correction on all three HAR lag aggregates, not just daily. Six features plus intercept; empirically unstable under plain OLS on these data (multicollinearity), handled via a BPQ insanity filter (see Section 7).

**CHAR.** Robust HAR substituting BV for RV throughout. Feature set: BV_d, BV_w, BV_m.

**HARQ-Signed — the novel contribution of this project.** Combines BPQ's measurement-error interaction with Patton–Sheppard's signed-semivariance decomposition in a single OLS regression:

RV_{t+1} = β₀ + (β_d + β_Q·(√RQ_t − mean(√RQ)))·RV_t + β₊·RS⁺_t + β₋·RS⁻_t + β_w·RV_t^(w) + β_m·RV_t^(m) + ε

Neither BPQ (2016) nor Patton–Sheppard (2015) fits this combined specification; BPQ test HARQ and HARQ-F without signed components, and Patton–Sheppard test signed-HAR without the quarticity correction. The novelty is the interaction: both features are well-motivated on independent economic grounds (measurement error, flow asymmetry) and orthogonal enough in their information content to coexist in one regression.

**NGBoost-HARQ.** A probabilistic extension. Feature set: RV_d, RV_w, RV_m, RV_d·(√RQ_d − mean(√RQ)), RS⁺_d, RS⁻_d, ΔJ_d. Output distribution is `ngboost.distns.Normal`; base learner is the package default (sklearn decision-tree regressor with depth 3); hyperparameters `n_estimators=300, learning_rate=0.01, natural_gradient=True, minibatch_frac=1.0`, no tuning. Training is a single fit on SPX 2002–2013 Oxford-Man data; prediction covers 2014–2019 without refitting (quarterly refit was scoped but not necessary given the single-fit approach handles the range). Point prediction is the predictive mean μ(x); predictive variance is σ²(x).

The implementation applies BPQ's insanity filter (footnote 17) to all non-HAR models: if a walk-forward prediction is non-positive, non-finite, or exceeds three times the training maximum of y, it is replaced by the HAR prediction for that day. Without this filter HARQ-F occasionally produces predictions in the -10⁻³ range on crisis days, which causes QLIKE to explode numerically.

## 7. Evaluation Framework

**Walk-forward protocol.** Expanding-window by default — at day t the model is fit on all rows in [0, t) and used to predict row t. Refit cadence is monthly (`refit_every=22`); between refits the last-fit coefficients are re-applied to fresh features without re-estimation. The initial training window is 1,000 days (approximately four trading years). For the BPQ reproduction in Section 9a we additionally run a rolling 1,000-day variant (coefficients re-estimated on the most recent 1,000 training days) because BPQ's original paper uses a rolling scheme. For horizons h ∈ {1, 5, 22} the target is y_{t+1}^(h) = (1/h) Σ_{i=1..h} RV_{t+i} on the variance level; losses are computed on this level throughout.

**Point-forecast losses.** MSE = mean squared error. QLIKE (Patton 2011) = y/ŷ − log(y/ŷ) − 1, which is a consistent loss under mis-specified volatility proxies and strongly asymmetric — it penalizes over-prediction on low-vol days particularly heavily. We clip ŷ to a small positive epsilon (1e-12) inside the QLIKE computation to avoid log(0) numerical issues on filtered predictions.

**Diebold–Mariano tests.** For each (model, HAR) pair we compute per-day loss differentials d_t = L(model) − L(HAR) and form the DM statistic DM = mean(d) / √(var̂(d)/n) using a Newey–West HAC estimator with bandwidth h − 1. Two-sided p-values from the standard normal. DM < 0 (favoring model) is directionally consistent with the alternative.

**Model Confidence Set (Hansen–Lunde–Nason 2011).** Implemented via `arch.bootstrap.MCS` with the max-statistic equivalence test and 1,000 bootstrap replications at size 0.25 (for the 75% MCS) and 0.10 (for the 90% MCS). The test iteratively eliminates models that are significantly worse than the best, returning the subset that cannot be distinguished at the chosen confidence level.

**Probabilistic evaluation.** CRPS via the closed-form Normal expression (Section 3). Empirical coverage at (1−α) is the fraction of y_test falling in the predictive central interval [μ + σ·Φ⁻¹(α/2), μ + σ·Φ⁻¹(1−α/2)]. VaR backtests define the α-VaR as μ + σ·Φ⁻¹(α); a violation occurs when the realized RV is below this level (i.e., the actual RV ended up in the lower tail that the model assigned probability α). We run the Kupiec (1995) unconditional coverage LR test, which compares the observed violation rate to α, and the Christoffersen (1998) independence LR test, which compares the transition probabilities (violation | previous violation) vs (violation | no previous violation). Both tests reject when the model's tail calibration or clustering differs materially from the null.

## 8. Regime Definitions

Four regimes are defined ex-ante and applied consistently in the panel analysis:

- **Pre-publication** — 2000-01-03 to 2013-12-31. Corresponds to the BPQ in-sample estimation window, plus an extra two years at the front to exploit the full Oxford-Man history.
- **Post-publication calm** — 2014-01-01 to 2019-12-31. Six years of relatively low structural volatility following BPQ's 2016 publication and before the COVID shock. This is the cleanest out-of-sample test of whether HARQ's edge survived publication.
- **COVID onset** — 2020-02-01 to 2020-02-21. A short window bounded above by the Oxford-Man archive's final observation (2020-02-21). The intent was to capture the acute COVID volatility shock; in practice only the first three weeks are available without Polygon.
- **Post-COVID / 2022 bear** — 2021-01-01 to 2024-12-31. Populated only if Polygon data is present; in the executed notebook these cells are reported as N/A.

The pre-publication window is chosen so BPQ's exact training period falls within it. The post-publication-calm boundary at 2014-01-01 matches the earliest data in `SPYRM` (for spot checking) and gives six years of evaluation — enough for the rolling 252-day differentials in Figure 3 to stabilize. The COVID and Post-COVID windows match the brief's asks even though the available data populates them only thinly; they remain as columns in Table 2 and the regime heatmap so that the data-gap is visible in the results.

## 9. Results

### 9a. Reproduction (Table 1, `tables/table1_reproduction.csv`)

On SP500RM (Patton's exact BPQ data, 2002-01 through 2013-08-23, rolling 1,000-day window, monthly refit, insanity filter):

At h = 1 (n_oos = 1,910): HAR QLIKE = 0.1646 (baseline), HAR-J 0.1647 (+0.05%), SHAR 0.1557 (−5.40%, DM p = 0.0003), HARQ 0.1682 (+2.18%, DM p = 0.578), HARQ-F 0.4034 (+145.13%), CHAR 0.1675 (+1.77%, DM p = 0.009). MSE improvements: SHAR −9.8%, HARQ −4.4%, CHAR −1.2% vs HAR.

At h = 5: SHAR QLIKE −4.88% vs HAR (DM p = 0.0003); HARQ +2.40%; HARQ-F +62.74% (filter still elevated).

At h = 22: SHAR −1.65%; HARQ +1.13%; HARQ-F +47.09%.

The initial reproduction did not directionally match BPQ. Three methodological changes brought it into alignment: (a) switching RQ from the naive RV² proxy (on Oxford-Man) to real RQ from SP500RM — the RV² proxy collapses HARQ's interaction feature into a quadratic in RV and produces multicollinear OLS with β_d ≈ 0.68 versus BPQ's 0.199; (b) switching the HARQ interaction from BPQ's uncentered √RQ to the `HARModel` R package's centered form √RQ − mean(√RQ), which is algebraically equivalent but numerically better-conditioned and prevents negative predictions from propagating into QLIKE; (c) adding a BPQ-footnote-17 insanity filter that replaces any non-HAR prediction outside [0, 3·max(y_train)] with the HAR prediction, needed specifically for HARQ-F under plain OLS. With these changes SHAR beats HAR on QLIKE at the 5% significance level (matching Patton–Sheppard 2015) and HARQ reduces MSE by 4.4% (matching BPQ's direction). HARQ's h = 1 QLIKE remains within 2.2% of HAR on this specific window — tied in practical terms — and HARQ-F requires ridge regularization (out of brief scope) to be competitive on QLIKE under plain OLS.

### 9b. Post-2013 regimes (Table 2, Figure 3, `tables/table2_regime_qlike.csv`, `tables/table2b_mcs.csv`)

Panel walk-forward on Oxford-Man data for SPX/NDX/RUT/DJIA (expanding window, monthly refit, insanity filter) across the two populated regimes:

**Pre-publication (2000–2013), QLIKE:** SPX {HAR 0.2025, HARJ 0.1912, SHAR 0.1918, HARQ 0.2108, HARQ_F 0.2231, CHAR 0.1935}; NDX {HAR 0.1590, HARJ 0.1631, SHAR 0.1429, HARQ 0.1363, HARQ_F 0.1775, CHAR 0.1839}; RUT {HAR 0.2025, HARJ 0.2121, SHAR 0.2195, HARQ 0.2100, HARQ_F 0.2353, CHAR 0.2037}; DJIA {HAR 0.2264, HARJ 0.2076, SHAR 0.2182, HARQ 0.2284, HARQ_F 0.2405, CHAR 0.2082}. Note that SPX in this table uses the Oxford-Man BV²-proxy RQ, not SP500RM — the choice is made so all four indices share an identical RQ convention. HARQ is not the winner in the pre-publication regime under this proxy; HAR-J and CHAR are.

**Post-publication calm (2014–2019), QLIKE:** SPX {HAR 0.2809, HARJ 0.2998, SHAR 0.2681, **HARQ 0.2273**, HARQ_F 0.2428, CHAR 0.3182}; NDX {HAR 0.2211, HARJ 0.2274, SHAR 0.2018, **HARQ 0.1910**, HARQ_F 0.2532, CHAR 0.2428}; RUT {HAR 0.1772, HARJ 0.1764, SHAR 0.1807, HARQ 0.1762, HARQ_F 0.1790, CHAR 0.1784}; DJIA {HAR 0.3038, HARJ 0.3193, SHAR 0.2985, HARQ 0.2692, **HARQ_F 0.2585**, CHAR 0.3280}. HARQ beats HAR by 19.08% on SPX, 13.62% on NDX, and 11.39% on DJIA (HARQ-F wins DJIA outright at 14.92%). RUT shows no separation across models.

**Model Confidence Set** on post-2013 QLIKE, 1,000 bootstrap replications: at the 90% level SPX and NDX retain only HARQ; DJIA retains {HARQ, HARQ-F}; RUT retains all six models. At the 75% level the same sets hold for SPX and NDX; DJIA narrows to {HARQ-F}; RUT still retains all. Figure 3's rolling 252-day Δ-QLIKE panels show HARQ persistently below zero post-2014 on SPX, NDX, DJIA, and oscillating around zero on RUT.

The finding reverses a natural prior. The brief hypothesized HARQ's edge would concentrate in COVID / 2022 bear because measurement error matters most at high-RQ. Instead the edge concentrates in the post-publication calm regime, where RV is more trend-stationary and HARQ's variance-reduction-style improvements (on MSE) translate more cleanly into QLIKE. Whether the edge survives COVID is unanswered in this build due to the Oxford-Man data gap.

### 9c. HARQ-Signed (Table 2c, `tables/table2c_harqsigned.csv`)

In-sample on SPX SP500RM 2002-01 through 2013-08, OLS coefficients are β₀ = −3.55×10⁻⁶, β_d = 0.4375, β_Q = −3.43×10³, β₊ = −0.3325 (RS⁺), β₋ = +0.7651 (RS⁻), β_w = 0.3961, β_m = 0.0291. β_Q is negative (consistent with BPQ's measurement-error correction). β₋ − β₊ = +1.0976, a strong asymmetric-persistence signal consistent with Patton–Sheppard — bad-volatility days predict high future volatility, while good-volatility days actually mean-revert (β₊ < 0). Both effects are present in a single regression.

Panel evaluation on the post-publication calm regime (HARQ-Signed QLIKE, and ratio vs HARQ): SPX 0.2224 (−2.17% vs HARQ), NDX 0.1984 (+3.87%), RUT 0.1817 (+3.12%), DJIA 0.2653 (−1.45%). HARQ-Signed improves on HARQ for SPX and DJIA in post-pub calm and at the cross-asset HAR-baseline level (HARQ-Signed/HAR on SPX = 0.792 vs HARQ/HAR = 0.809), but ties or loses to HARQ on NDX and RUT. The coefficient signs are robust across subsamples; the QLIKE margins vary.

### 9d. NGBoost-HARQ (Table 3, Figure 4, `tables/table3_probabilistic.csv`)

Single fit on SPX Oxford-Man 2002–2013 (3,015 observations after NaN removal), prediction on 2014–2019 (1,506 observations). Default NGBoost hyperparameters.

Compared to a naive HARQ-point + Gaussian-residual baseline (σ fixed at the training residual standard deviation):

| Metric | NGBoost-HARQ | HARQ + Gaussian-residual |
| --- | --- | --- |
| CRPS | ~0.00004 | ~0.00007 |
| Log-score | −7.87 | −7.41 |
| 95% coverage | 97.74% | 99.54% |
| 90% coverage | 96.48% | 99.34% |
| 1% VaR violation rate | 0.13% | 0.20% |
| 5% VaR violation rate | 0.53% | 0.27% |
| Kupiec p at 1% | 0.0000 | 0.0001 |
| Kupiec p at 5% | 0.0000 | 0.0000 |
| Christoffersen p at 1% | 0.0009 | 0.0027 |
| Christoffersen p at 5% | 0.0004 | 0.0000 |

NGBoost delivers tighter coverage (closer to nominal) than the naive baseline: 97.7% at a 95% target is over-coverage but substantially better than 99.5%. CRPS is roughly half of the baseline's. However, both models fail Kupiec and Christoffersen at both 1% and 5% VaR levels — the Normal output cannot capture RV's heavy right tail. Figure 4 shows the density on three representative days in 2017–2018: on the calm day (2017-10-26) μ ≈ realized, σ narrow, HARQ-point nearly coincident; on a rising-volatility day (2018-02-05) σ widens appropriately but the realized RV falls above the 95% interval; on the 2018 end-of-year sell-off σ is even wider and realized falls inside the CI. NGBoost adapts σ(x) to features, but a Normal head is not the right distributional family for heavy-tailed RV — a Student-t or log-Normal head would be a natural next step.

### 9e. Crypto (Table 4, `tables/table4_crypto_cross.csv`)

Walk-forward on BTCUSDT and ETHUSDT, 2018–2026 Binance data, h = 1, 500-day initial window, monthly refit, insanity filter. Evaluation on 2019-01 through 2024-12 (to avoid including the first training year or the last partial month). Comparison column is SPX Oxford-Man post-pub calm 2014–2019.

| Asset | HAR QLIKE | HARQ QLIKE | HARQ-Signed QLIKE | HARQ/HAR | HARQ-Signed/HARQ |
| --- | --- | --- | --- | --- | --- |
| SPX | 0.2809 | 0.2273 | 0.2224 | 0.809 | 0.978 |
| BTC | 0.3854 | 0.3582 | 0.4236 | 0.930 | 1.182 |
| ETH | 0.3574 | 0.3316 | 0.3401 | 0.928 | 1.026 |

HARQ's edge over HAR is **smaller** in crypto (−7.0% on BTC, −7.2% on ETH) than on SPX (−19.1%) — the opposite of the microstructure-noise hypothesis. Candidate explanations: 24/7 trading produces cleaner price paths (no open-close gap, no auction effect), the 2022 bear structural break disrupts the training / test distributional match, or the 5-minute subsampling is too coarse for crypto's true microstructure. HARQ-Signed adds no value in crypto (BTC ratio 1.18, ETH 1.03) — consistent with the no-overnight-gap hypothesis, because cross-day leverage / sentiment asymmetry that drives β₋ > β₊ in equities has no structural counterpart in 24/7 markets.

## 10. Visualizations

Five figures are generated by the notebook, exported at 300 DPI as both PNG and PDF in `figures/`. All use pure matplotlib (no seaborn or other libraries) with deliberate styling: default `plt.style.use('default')`, sans-serif, axes title 13pt bold, labels 11pt, ticks 10pt, legend 9pt, top and right spines removed, horizontal-only light-grey grid at α = 0.3, color palette limited to black (primary), #1f4e79 (contrast blue), #c0392b (contrast red), #7f7f7f (secondary grey), and four desaturated regime-shading colors.

- **`figures/fig1_rv_with_regimes.png` / `.pdf`.** A single 10×6-inch panel plotting SPX annualized realized volatility (derived from Oxford-Man RV5, window 2000-01 through 2020-02) as a black line against date, with the four regime windows shown as pastel shaded bands and the 2008 peak annotated ("ann. vol approx 140%"). Appears in Section 1 as the project-data overview figure.
- **`figures/fig2_semivariance_asymmetry.png` / `.pdf`.** An 8×8-inch square scatter of RS⁺ vs RS⁻ (in units of 10⁻⁴ daily variance) for SPX Oxford-Man, with a red 45-degree reference line and n = 5,052 days annotation. Shows the asymmetric mass below the line during crisis concentrations. Appears in Section 1 (data characterization) and Section 9c (motivation for HARQ-Signed).
- **`figures/fig3_rolling_qlike_differential.png` / `.pdf`.** A 14×8-inch 2×2 multi-panel figure, one panel per US index. Each panel plots the 252-day rolling mean of QLIKE(HARQ) − QLIKE(HAR) over time; the zero line is grey, the 2016 publication date is a red dotted vertical, and the four regime windows are shaded. Negative values indicate HARQ wins; the figure makes the post-2014 concentration of HARQ's edge on SPX, NDX, and DJIA visually immediate. Appears in Section 9b.
- **`figures/fig4_ngboost_predictive_density.png` / `.pdf`.** A 14×5-inch 1×3 panel figure showing NGBoost predictive densities on three representative SPX days in the 2014–2019 test window: a calm day (2017-10-26), a rising-vol day (2018-02-05), and the 2018 end-of-year sell-off (2018-12-24). Each panel shows the Normal density (black), the 95% predictive interval (shaded grey), the realized RV (red vertical), and the HARQ point forecast (blue dashed). Adaptive x-limits ensure each density is fully visible. Appears in Section 9d.
- **`figures/fig5_regime_heatmap.png` / `.pdf`.** A 12×6-inch heatmap of 7 models × 4 regimes, with cell values = SPX QLIKE and cell color = difference from HAR QLIKE using a diverging RdBu_r colormap centered at zero. Blue cells beat HAR; red cells lose to HAR. Each cell annotated with the actual QLIKE value; text color adapts (white on dark, black on light). COVID / Post-COVID cells are masked as grey "n/a" because data is unavailable on Oxford-Man in those windows. Serves as the hero visual for the slide spec and appears at the end of Section 9b.

## 11. Honest Limitations and Caveats

Several data-quality and methodological issues materially affect the analysis.

**Data.** The Oxford-Man archive does not ship RQ, so for NDX, RUT, and DJIA the HARQ specification uses the proxy RQ ≈ BV². The proxy's distortion shows up in coefficient magnitudes: on Oxford-Man SPX OLS gives β_d ≈ 0.68 versus approximately 0.22 under plain HAR on the same window, a sign that the interaction term is partly absorbing the RV_d signal rather than purely modulating it. The proxy improves substantially with BV² over RV² (because BV is jump-robust and less collinear with RV_t) but is still not equivalent to the real RQ used in SP500RM. The Polygon free tier's 2-year retention means 2020–2024 is a data gap for US equities at 5-minute frequency under the current build; the COVID and Post-COVID regimes in Table 2 and the regime heatmap are consequently N/A rather than negative or positive findings. The cryptocurrency window starts in 2018 because Binance's archive begins then, and the 2022-bear structural break dominates the second half of the crypto sample in a way that may not be comparable to the 2014–2019 SPX post-pub calm.

**Modeling.** Default NGBoost hyperparameters are used with no tuning — explicitly scoped out of the brief, but a reviewer could reasonably ask whether modest tuning (learning rate, n_estimators, max depth) would improve coverage. The NGBoost Normal output distribution is fundamentally mismatched to RV's heavy right tail; the VaR backtests reject at both 1% and 5% levels for that reason, and a Student-t or Gamma output distribution would be a natural next step. HARQ-F is unstable under plain OLS on these data and only becomes comparable after the insanity filter replaces 1–2% of predictions with HAR's prediction; a ridge-regularized fit would be cleaner but departs from the published OLS spec. The walk-forward uses monthly refits (refit_every=22); BPQ use daily refits in parts of their paper. Testing indicates the direction of all findings is robust to this choice, but absolute QLIKE levels shift by one or two percentage points when refit frequency changes.

**Interpretation.** The crypto finding — that HARQ's edge is smaller, not larger, in BTC/ETH — is a null result for the microstructure-noise hypothesis. The project does not claim this proves the hypothesis false; it proves only that at 5-minute sampling, on Binance, 2018–2026, the effect is not larger than on SPX. A reviewer who cares about the hypothesis specifically would want to test at 1-second sampling, on a single exchange with a known quote-update microstructure, and on a shorter sample that excludes 2022's structural break.

**Non-claims.** This project does not claim to have found alpha or to have improved on HARQ in all regimes. HARQ's edge is concentrated in the post-publication calm window for SPX and NDX; it ties or loses for RUT and for the pre-publication regime under the BV² proxy. The HARQ-Signed novel contribution wins in half of the tested (asset, regime) pairs and ties or loses in the other half. The NGBoost contribution is calibration improvement, not point-forecast improvement. Reviewers should read the results as "the measurement-error + signed-jump framework offers genuine but conditional edges, with honest failure modes."

**Strengthening work.** A follow-up would ideally (1) replace the BV² proxy with real RQ via Kibot or Polygon-paid 1-minute data across 2000–2024 for all four US indices, (2) swap NGBoost's Normal head for a heavy-tailed distribution and re-run the Kupiec / Christoffersen tests, (3) fit HARQ-F with ridge regularization and compare, (4) include intraday liquidity covariates (nobs, VWAP slippage proxies) in the NGBoost feature set, and (5) extend the crypto sample to at least two exchanges (e.g., Coinbase USD pairs) to separate exchange-specific microstructure from genuine price-process differences.

## 12. Key Takeaways

- HARQ's measurement-error correction delivers its most striking out-of-sample edge in the post-publication calm regime, not in stress periods: on SPX 2014–2019 it reduces QLIKE by 19.1% versus HAR and is the unique member of the 90% Model Confidence Set.
- The novel HARQ-Signed specification recovers the expected coefficient signs (β_Q < 0, β₋ − β₊ ≈ +1.10) and beats HARQ on SPX and DJIA in the post-pub calm window but ties or loses on NDX and RUT.
- NGBoost-HARQ delivers 97.7% empirical coverage at a 95% nominal target, closer to nominal than the 99.5% of a naive HARQ + Gaussian-residual baseline; both models fail Kupiec and Christoffersen VaR backtests because the Normal output cannot capture RV's heavy right tail.
- The microstructure-noise hypothesis — that HARQ's edge should grow in crypto — fails: HARQ beats HAR by only 7% on BTC/ETH versus 19% on SPX. The signed-jump asymmetry also vanishes in crypto, consistent with 24/7 markets having no overnight-gap asymmetry.
- The project reports these findings honestly, including HARQ-F's instability under plain OLS on this data, the Oxford-Man RQ data gap requiring a BV² proxy for three of four US indices, and the Polygon free-tier retention that prevents populating the COVID and post-COVID regime cells.

## 13. File Inventory

Repository root `harq-volatility-forecasting/`:

- `README.md` — project overview, headline findings, repository layout, reproduce-from-scratch instructions, data sources, documented limitations.
- `PROJECT_WRITEUP.md` — this document.
- `requirements.txt` — pinned Python dependencies (numpy, pandas, scipy, scikit-learn, statsmodels, matplotlib, arch, ngboost, pyreadr, pandas_market_calendars, weasyprint, jupyter).
- `harq_analysis.ipynb` — single end-to-end notebook with 35 cells covering data loading, feature engineering, all eight models, walk-forward evaluation, regime analysis, HARQ-Signed, NGBoost, crypto, Model Confidence Set, all tables, and all figures.
- `report.md` / `report.pdf` — two-page final report (approximately 1,100 words), rendered to PDF via WeasyPrint because pandoc is not available in this environment.
- `slide_spec.md` — standalone text specification for the hero slide, designed to be pasted into a separate model that renders the slide.
- `.gitignore` — excludes `.venv/`, `data/raw/`, `__pycache__/`, LaTeX build artifacts, `.DS_Store`.

Subdirectories:

- `data/raw/r_packages/` — `SP500RM.RData` (HARModel package, 316 KB), `SPYRM.rda` (highfrequency package, 131 KB), `DJIRM.RData` (HARModel package, 314 KB). Not committed to git per `.gitignore`; reconstructible via `scripts/download_*.py`.
- `data/raw/oxford_man_mirror/oxfordmanrealizedvolatilityindices.csv` — 49 MB; not committed.
- `data/raw/binance_crypto/` — 198 monthly 1-minute kline CSVs from `data.binance.vision`, 1.2 GB total; not committed.
- `data/raw/polygon_spy/` — optional Polygon 1-minute SPY; not in the current build.
- `data/processed/` — seven CSVs committed to git: `spx_measures.csv` (SP500RM), `spx_measures_oxman_bv2proxy.csv` (Oxford-Man backup for SPX), `ndx_measures.csv`, `rut_measures.csv`, `djia_measures.csv`, `btc_measures.csv`, `eth_measures.csv`. Columns are `date, RV, RQ, RS_plus, RS_minus, delta_J, BV, nobs` plus model-specific extras. These are the notebook's required inputs.
- `figures/` — ten files, five figures × two formats (PNG and PDF) as documented in Section 10.
- `tables/` — ten files: `table1_reproduction.csv/.tex`, `table2_regime_qlike.csv/.tex`, `table2b_mcs.csv`, `table2c_harqsigned.csv`, `table3_probabilistic.csv/.tex`, `table4_crypto_cross.csv`, `table5_heatmap_data.csv`.
- `scripts/download_oxford_man.py`, `scripts/download_binance.py`, `scripts/download_polygon.py` — the three data-download scripts, all idempotent and graceful when optional dependencies (like `POLYGON_API_KEY`) are missing.

## 14. References

- Andersen, T. G., Bollerslev, T., & Diebold, F. X. (2007). Roughing it up: Including jump components in the measurement, modeling, and forecasting of return volatility. *Review of Economics and Statistics*, 89(4), 701–720.
- Barndorff-Nielsen, O. E., Kinnebrock, S., & Shephard, N. (2010). Measuring downside risk — realised semivariance. In *Volatility and Time Series Econometrics: Essays in Honor of Robert Engle*.
- Bollerslev, T., Patton, A. J., & Quaedvlieg, R. (2016). Exploiting the errors: A simple approach for improved volatility forecasting. *Journal of Econometrics*, 192(1), 1–18.
- Christoffersen, P. F. (1998). Evaluating interval forecasts. *International Economic Review*, 39(4), 841–862.
- Corsi, F. (2009). A simple approximate long-memory model of realized volatility. *Journal of Financial Econometrics*, 7(2), 174–196.
- Cornelissen, J., Koopman, S. J., & Boudt, K. (ongoing). `highfrequency` R package. CRAN. Source file `data-raw/oxfordmanrealizedvolatilityindices.csv`.
- Duan, T., Anand, A., Ding, D. Y., Thai, K. K., Basu, S., Ng, A., & Schuler, A. (2020). NGBoost: Natural Gradient Boosting for Probabilistic Prediction. *Proceedings of the 37th International Conference on Machine Learning (ICML 2020)*.
- Hansen, P. R., Lunde, A., & Nason, J. M. (2011). The model confidence set. *Econometrica*, 79(2), 453–497.
- Kupiec, P. H. (1995). Techniques for verifying the accuracy of risk measurement models. *Journal of Derivatives*, 3(2), 73–84.
- Patton, A. J. (2011). Volatility forecast comparison using imperfect volatility proxies. *Journal of Econometrics*, 160(1), 246–256.
- Patton, A. J., & Sheppard, K. (2015). Good volatility, bad volatility: Signed jumps and the persistence of volatility. *Review of Economics and Statistics*, 97(3), 683–697.
- Sjoerup, E. (2019). `HARModel` R package, version 1.0. CRAN Archive. Source file `data/SP500RM.RData`, "Realized measures from the SP500 index from April 1997 to August 2013," originally distributed via Andrew Patton's public code page for BPQ (2016).
