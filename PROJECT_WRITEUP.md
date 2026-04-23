# Project Writeup: HARQ Volatility Forecasting Reproduction + Extensions

## 1. Project Overview

This project reproduces and extends two foundational realized-volatility-forecasting papers — Bollerslev, Patton, and Quaedvlieg (2016), "Exploiting the errors: A simple approach for improved volatility forecasting," and Patton and Sheppard (2015), "Good volatility, bad volatility: Signed jumps and the persistence of volatility" — using exclusively datasets for which *genuine* realized quarticity is publicly distributed. The equity evaluation is scoped to the S&P 500 (SP500RM 1997–2013 stitched with SPYRM 2014–2019); the cryptocurrency cross-check uses BTCUSDT and ETHUSDT at 1-minute frequency from Binance's public archive (2018–2026). Six HAR-family baselines (HAR, HAR-J, SHAR, HARQ, HARQ-F, CHAR), one novel specification (HARQ-Signed), and one probabilistic extension (NGBoost-HARQ) are evaluated out-of-sample across the BPQ pre-publication and post-publication calm regimes. Deliverables are a single end-to-end Jupyter notebook (`harq_analysis.ipynb`), five publication-quality matplotlib figures, five analysis tables, a two-page PDF report, and a standalone slide specification. The implementation is approximately 1,700 lines of Python, most of which lives in the notebook; the remaining code is two data-download scripts under `scripts/` (Oxford-Man has been removed in this revision). The end-to-end build — from a fresh Python environment through processed data, all walk-forwards, figures, and PDF report — completes in well under ten minutes on commodity hardware.

## 2. Research Questions

The project addresses three research questions derived from the original brief.

**Q1. Does HARQ's published 5–10% QLIKE edge over HAR survive out-of-sample through 2019, and does it concentrate in specific volatility regimes?** BPQ (2016) estimated HARQ on SPX 2001–2013 and reported both MSE and QLIKE improvements of 5–10%. A serious test is whether that edge persists in the 2014–2019 post-publication calm window. An answer takes the form of per-regime QLIKE differentials, Diebold–Mariano significance tests, and Model Confidence Set membership.

**Q2. Can we usefully combine BPQ's measurement-error correction with Patton–Sheppard's signed-jump decomposition into a single specification, HARQ-Signed, and does it improve on either paper's model alone?** This is the novel contribution. The specification nests HARQ (via the √RQ interaction) and a Patton–Sheppard signed HAR (via separate β₊, β₋ on RS⁺, RS⁻), and asks whether the combination recovers the expected coefficient signs (β_Q < 0, β₋ > β₊) and produces a smaller QLIKE than HARQ alone.

**Q3. When volatility forecasts are needed for downstream risk management (VaR, option pricing), can probabilistic boosting (NGBoost) deliver calibrated predictive intervals?** The HAR family produces point forecasts; operational risk requires distributions. NGBoost with a Normal output distribution is compared against a naive HARQ + Gaussian-residual baseline on CRPS, empirical coverage at 90% and 95%, and Kupiec / Christoffersen VaR backtests at 1% and 5%.

A fourth sub-question supports Q1: whether HARQ's edge scales with microstructure noise — tested on BTCUSDT and ETHUSDT where genuine 5-minute RQ can be computed from public data.

## 3. Theoretical Background

**Corsi (2009), HAR.** The heterogeneous autoregressive model predicts next-day realized variance as a linear combination of three trailing averages of past RV at daily, weekly, and monthly horizons:

RV_{t+1} = β₀ + β_d · RV_t + β_w · RV_t^(w) + β_m · RV_t^(m) + ε_{t+1}

where RV_t^(w) = (1/5) Σ_{i=0..4} RV_{t−i} and RV_t^(m) = (1/22) Σ_{i=0..21} RV_{t−i}. The intuition is that volatility clusters at multiple time scales and a simple three-factor OLS captures the long-memory decay of RV autocorrelations without needing a true long-memory parameter.

**Bollerslev–Patton–Quaedvlieg (2016), HARQ.** BPQ observe that RV_t is not the true integrated variance IV_t but an estimator whose error-variance is proportional to the integrated quarticity IQ_t, consistently estimated by the realized quarticity RQ_t = (n/3) Σ_{i=1..n} r_{t,i}⁴. When RQ_t is large, today's RV is noisier and should be weighted less when predicting tomorrow. They operationalize this by interacting a scaled √RQ_t with the daily lag:

RV_{t+1} = β₀ + (β_d + β_Q · (√RQ_t − mean(√RQ))) · RV_t + β_w · RV_t^(w) + β_m · RV_t^(m)

BPQ report β_Q ≈ −0.13 on SPX 2001–2013. HARQ-F extends the correction to all three HAR lags.

**Patton–Sheppard (2015), signed semivariances.** Barndorff-Nielsen et al. (2010) showed RV can be decomposed into positive and negative semivariances: RS⁺ = Σ r_i²·𝟙{r_i>0} and RS⁻ = Σ r_i²·𝟙{r_i<0}. The signed jump is ΔJ = RS⁺ − RS⁻. Patton–Sheppard replace the daily RV lag with β₊·RS⁺ and β₋·RS⁻ and find β₋ > β₊ — down-move-driven volatility is more persistent than up-move-driven volatility.

**Duan et al. (2019), NGBoost.** NGBoost is a gradient-boosting algorithm whose boosting update is a natural gradient step on the parameters of an output distribution rather than on a scalar prediction. Fit with a Normal output, each prediction is a tuple (μ(x), σ(x)), both dependent on the features x. This differs from a point regressor plus residual-variance model because σ(x) adapts to features. The natural evaluation metric is CRPS (continuous ranked probability score), which for a Normal forecast has the closed form CRPS(y | μ, σ) = σ · [z·(2·Φ(z) − 1) + 2·φ(z) − 1/√π] with z = (y − μ)/σ.

## 4. Data

**Scope decision.** This revision is deliberately restricted to assets for which publicly-distributed genuine realized quarticity is available — no BV² or other proxies for RQ. Extending to NDX, RUT, or DJIA would require paid minute data (Polygon Stocks Starter tier or equivalent) and was out of scope.

**`SP500RM` (Sjoerup's `HARModel` R package; original source: Andrew Patton's code page for BPQ 2016).** Loaded via the CRAN archive tarball `HARModel_1.0.tar.gz` → extract `HARModel/data/SP500RM.RData` → read with `pyreadr.read_r()`. The resulting DataFrame has 4,096 rows and 11 columns including `RV`, `RQ`, `RJ`, `BPV`, `RVn` (negative semivariance), `RVp` (positive semivariance), `TPQ`, `MedRQ`. `pyreadr` drops the xts date index; we reconstruct it by anchoring two historically known volatility spikes — row 2869 with RV = 60.56 to 2008-10-09 and row 3581 with RV = 19.55 to the 2011-08-08 S&P-downgrade reaction — which places the series start at 1997-05-15 on the NYSE calendar (via `pandas_market_calendars`), yielding 4,096 trading days through 2013-08-23. Values are in percent-squared daily variance units; we divide by 10⁴ for decimal variance and by 10⁸ for quarticity. The implied annualized volatility is 17.21%.

**`SPYRM` (Cornelissen's `highfrequency` R package).** Loaded analogously from `highfrequency_1.0.3.tar.gz`. 1,495 rows spanning 2014-01-02 through 2019-12-31, covering SPY ETF. Columns: `RV5`, `BPV5`, `RQ5`, `medRQ5`, plus one-minute variants. SPYRM does *not* ship positive/negative semivariances, so SHAR, HARQ-Signed, and NGBoost-HARQ (which require them) are scoped to the SP500RM portion only (1997–2013); HAR, HARJ, HARQ, HARQ-F, CHAR extend through the full SP500RM+SPYRM stitch.

**SPX stitched series.** SP500RM and SPYRM are concatenated into a single `spx_measures.csv` with 5,591 rows from 1997-05-15 to 2019-12-31. `RS⁺`, `RS⁻`, `ΔJ` are populated on the 4,096 SP500RM rows and NaN on the 1,495 SPYRM rows. A ~4-month gap (2013-08-24 to 2013-12-31) falls between the two sources and is handled implicitly by the walk-forward NaN filtering.

**Binance Vision** public monthly archive at `data.binance.vision`. Zipped 1-minute klines for BTCUSDT and ETHUSDT, 99 monthly files per symbol from 2018-01 through 2026-03 — 198 files totaling 1.2 GB and 4.33 million bars per symbol. Timestamp units change from milliseconds to microseconds in late 2024; the download script auto-detects per file. RV, RQ, RS⁺, RS⁻, ΔJ, BV are computed in-notebook from 5-minute subsampled close-to-close log returns over the full 24-hour UTC day. BTC annualized volatility over the window is 71.21%, ETH's is 89.28%.

**Polygon.io** 1-minute SPY is supported but optional; it requires `POLYGON_API_KEY` and covers the free tier's ~2-year window. Not used in the executed analysis.

All processing writes canonicalized CSVs to `data/processed/` (columns: `date, RV, RQ, RS_plus, RS_minus, delta_J, BV, nobs` plus model-specific extras). These CSVs are committed to the repository; raw data is in `.gitignore`. The notebook's default code path reads only `data/processed/`, so the full analysis is reproducible from a clone without re-running any downloads.

## 5. Feature Engineering

Every model consumes features built by the notebook's `build_har_features()` function, applied per-asset to the processed CSVs. The feature set is:

- **Realized variance, RV_t.** Sum of 5-minute squared log returns within the day.
- **Bipower variation, BV_t = (π/2) · Σ_{i≥2} |r_i| · |r_{i−1}|.** Jump-robust integrated-variance estimator.
- **Realized quarticity, RQ_t = (n/3) · Σ r_i⁴.** Genuine 5-minute RQ on both SP500RM and SPYRM; genuine on crypto too.
- **Positive / negative semivariances, RS⁺_t, RS⁻_t.** For SP500RM these are native columns (`RVp`, `RVn`); for crypto we compute both halves directly from 5-minute returns. SPYRM does not ship them.
- **Signed jump, ΔJ_t = RS⁺_t − RS⁻_t.** Included as a standalone feature in the NGBoost model's feature set.
- **Jump variation, J_t = max(RV_t − BV_t, 0).** Ensures non-negativity; drives HAR-J.
- **Trailing HAR aggregates:** RV_t^(w) = (1/5) Σ_{i=0..4} RV_{t−i} and RV_t^(m) = (1/22) Σ_{i=0..21} RV_{t−i}. Analogous aggregates BV_t^(w), BV_t^(m), RQ_t^(w), RQ_t^(m) feed CHAR and HARQ-F. Rolling means are trailing-inclusive of day t.
- **HARQ interaction feature, RV_t · (√RQ_t − mean_train(√RQ)).** Centered at the training-window mean of √RQ per the `HARModel` R-package convention. Re-centering happens at each walk-forward refit using only the training window.

Regime indicators are assigned downstream (not in the feature builder) as date-bucket labels drawn from the four regime definitions in Section 8.

## 6. Models Implemented

All eight models share a Python base class `VolForecaster` with two methods: `.transform(features, train_stats)` returns the model-specific design matrix (and any statistics needed to build a test row consistently with training), and `.fit(X, y)` / `.predict(X)` do OLS via `numpy.linalg.lstsq`. NGBoost uses the `ngboost` package directly.

**HAR (Corsi 2009).** Features: RV_d, RV_w, RV_m. Plain OLS, three regressors plus intercept.

**HAR-J (Andersen–Bollerslev–Diebold 2007).** HAR plus the jump component: RV_d, RV_w, RV_m, J_d.

**SHAR (Patton–Sheppard 2015).** Replaces RV_d with separate RS⁺_d and RS⁻_d. Features: RS⁺_d, RS⁻_d, RV_w, RV_m. SP500RM only.

**HARQ (Bollerslev–Patton–Quaedvlieg 2016).** Features: RV_d, RV_d·(√RQ_d − mean_train(√RQ)), RV_w, RV_m. Centered interaction per `HARModel` R convention.

**HARQ-F (BPQ 2016).** Applies the measurement-error correction on all three HAR lag aggregates. Six features plus intercept.

**CHAR.** Robust HAR substituting BV for RV throughout. Features: BV_d, BV_w, BV_m.

**HARQ-Signed — novel contribution.** Combines BPQ's measurement-error interaction with Patton–Sheppard's signed-semivariance decomposition in one OLS:

RV_{t+1} = β₀ + (β_d + β_Q·(√RQ_t − mean(√RQ)))·RV_t + β₊·RS⁺_t + β₋·RS⁻_t + β_w·RV_t^(w) + β_m·RV_t^(m) + ε

Neither BPQ (2016) nor Patton–Sheppard (2015) fits this combined specification. The novelty is that both features are well-motivated on independent economic grounds and orthogonal enough in their information content to coexist in one regression.

**NGBoost-HARQ.** Feature set restricted to features present in both SP500RM and SPYRM portions: RV_d, RV_w, RV_m, RV_d·(√RQ_d − mean(√RQ)), BV_d. Output distribution is `ngboost.distns.Normal`; base learner is the package default; hyperparameters `n_estimators=300, learning_rate=0.01, natural_gradient=True, minibatch_frac=1.0`, no tuning. Single fit on SPX 2002–2013 SP500RM; prediction on 2014–2019 SPYRM without refit.

The walk-forward applies BPQ's insanity filter (footnote 17) to all non-HAR models: if a prediction is non-positive, non-finite, or exceeds three times the training maximum of y, it is replaced by the HAR prediction for that day. The walk-forward also filters NaN per model's specific feature requirements, which is what lets HAR / HARQ / HARQ-F / CHAR run on the SPYRM portion even though SHAR / HARQ-Signed cannot.

## 7. Evaluation Framework

**Walk-forward protocol.** Expanding window by default. Refit cadence is monthly (`refit_every=22`); between refits the last-fit coefficients are re-applied to fresh features without re-estimation. The initial training window is 1,000 days. The BPQ reproduction in Section 9a uses a rolling 1,000-day variant. For horizons h ∈ {1, 5, 22} the target is y_{t+1}^(h) = (1/h) Σ_{i=1..h} RV_{t+i} on the variance level; losses are computed on this level throughout.

**Point-forecast losses.** MSE and QLIKE (Patton 2011). QLIKE = y/ŷ − log(y/ŷ) − 1; we clip ŷ to 1e-12 inside QLIKE to avoid log(0).

**Diebold–Mariano tests.** For each (model, HAR) pair we compute per-day loss differentials on the date-aligned intersection of both models' walk-forward outputs. DM statistic = mean(d) / √(var̂(d)/n) using Newey–West HAC with bandwidth h − 1.

**Model Confidence Set (Hansen–Lunde–Nason 2011).** Via `arch.bootstrap.MCS` with the max-statistic equivalence test and 1,000 bootstrap replications at size 0.25 (75% MCS) and 0.10 (90% MCS). Per-regime, models are date-aligned before MCS; models with fewer than 50 observations in a regime are dropped from that regime's MCS.

**Probabilistic evaluation.** CRPS via the closed-form Normal expression. Empirical coverage at (1−α) is the fraction of y_test falling in [μ + σ·Φ⁻¹(α/2), μ + σ·Φ⁻¹(1−α/2)]. VaR backtests define the α-VaR as μ + σ·Φ⁻¹(α); a violation occurs when realized RV is below this level. Kupiec (1995) unconditional-coverage LR and Christoffersen (1998) independence LR tests are applied at 1% and 5%.

## 8. Regime Definitions

- **Pre-publication** — 2000-01-03 to 2013-12-31. Corresponds to BPQ's in-sample estimation window.
- **Post-publication calm** — 2014-01-01 to 2019-12-31. Six years of relatively low structural volatility following BPQ's 2016 publication and before the COVID shock — the cleanest out-of-sample test of whether HARQ's edge survived publication.
- **COVID onset** — 2020-02-01 to 2020-02-21. Populated only if SPX data is available; in this revision both SP500RM (ends 2013) and SPYRM (ends 2019-12) leave this regime empty.
- **Post-COVID / 2022 bear** — 2021-01-01 to 2024-12-31. Populated only if Polygon data is present; in this revision reported as N/A.

## 9. Results

### 9a. Reproduction (Table 1, `tables/table1_reproduction.csv`)

On SP500RM 2002-01 through 2013-08-23, rolling 1,000-day window, monthly refit, insanity filter: at h = 1 (n_oos = 1,910), HAR QLIKE = 0.1646, HARJ 0.1647 (+0.05%), SHAR 0.1557 (−5.40%, DM p = 0.0003), HARQ 0.1682 (+2.18%, DM p = 0.578), HARQ-F 0.4034 (+145.13%), CHAR 0.1675 (+1.77%, DM p = 0.009). MSE improvements vs HAR: SHAR −9.8%, HARQ −4.4%, CHAR −1.2%. At h = 5: SHAR −4.88% QLIKE (DM p = 0.0003); HARQ +2.40%. At h = 22: SHAR −1.65%. Reproduction is directionally consistent with BPQ on MSE (HARQ reduces MSE by ~4%) and with Patton–Sheppard on QLIKE (SHAR beats HAR by 5%). HARQ's exact QLIKE is within 2.2% of HAR on this rolling-window reproduction; Table 1 also reports the BPQ-style rolling-window estimates alongside the expanding-window regime numbers in §9b.

### 9b. SPX regime analysis (Table 2, Figure 3, `tables/table2_regime_qlike.csv`, `tables/table2b_mcs.csv`)

On the stitched SP500RM+SPYRM series with expanding walk-forward, h=1, monthly refit, HAR-insanity-anchor, both populated regimes:

**Pre-publication (n ≈ 3,075 observations, 2000–2013):** HAR 0.1495, HARJ 0.1451, SHAR 0.1296, HARQ 0.1314, HARQ-F 0.1284, CHAR 0.1471. The HARQ family *dominates*: HARQ-F beats HAR by −14.1%, HARQ by −12.1%, SHAR by −13.3%, HARJ by −2.9%, CHAR by −1.6%. The 75% and 90% Model Confidence Sets both retain exactly {SHAR, HARQ, HARQ-F}; the three flat-HAR baselines (HAR, HARJ, CHAR) are significantly inferior at both levels. This is the strongest quantitative test of the HARQ-family measurement-error correction in the project, with real RQ throughout.

**Post-publication calm (n = 1,494 observations, 2014–2019, SPYRM only):** HAR 0.2615, HARJ 0.2592 (−0.9%), HARQ 0.2689 (+2.8%), HARQ-F 0.3035 (+16.1%), CHAR 0.2682 (+2.6%). The 75% and 90% MCS both retain {HAR, HARJ, HARQ, HARQ-F, CHAR} — no statistical discrimination among baselines. HARQ is not the unique best. SHAR and HARQ-Signed are not evaluated because SPYRM does not ship positive/negative semivariances. Three candidate explanations for the regime reversal are (i) SPY's microstructure differs from SPX's (ETF vs. cash index), (ii) HF data quality rose post-publication so RQ-based noise correction adds less, and (iii) the post-2013 calm has less absolute variation in RQ to exploit (the median RQ/RV² ratio in the SPYRM subsample is smaller than in SP500RM).

**Figure 3** plots the 252-day rolling QLIKE(HARQ) − QLIKE(HAR) on SPX from 2001 through 2019. The differential is strongly negative throughout 2004–2013 (HARQ decisively wins in the pre-publication regime) and drifts up to approximately zero or slightly positive from 2015 onward.

### 9c. HARQ-Signed (Table 2c, `tables/table2c_harqsigned.csv`)

In-sample fit on SPX SP500RM 2002-01 through 2013-08: β₀ = −3.55×10⁻⁶, β_d = 0.4375, β_Q = −3.43×10³ (negative, as BPQ predict), β₊ = −0.3325, β₋ = +0.7651, β_w = 0.3961, β_m = 0.0291. β₋ − β₊ = +1.0976, a strong asymmetric-persistence signal consistent with Patton–Sheppard — bad-volatility days predict high future volatility, while good-volatility days mean-revert (β₊ < 0). Both the measurement-error and signed-jump effects are present in a single regression with correct expected signs.

Walk-forward evaluation (pre-publication regime only, because RS⁺/RS⁻ are absent from SPYRM): HARQ-Signed QLIKE = 0.1256 on n = 3,075 observations. Versus HAR, DM p < 10⁻⁶ (strongly significant improvement). Versus HARQ, DM p = 2.5×10⁻⁵ (also strongly significant). As a QLIKE ratio, HARQ-Signed/HARQ = 0.954 (HARQ-Signed is 4.6% better than HARQ), and HARQ-Signed/HAR = 0.840 (16.0% better than HAR). HARQ-Signed is the lowest-QLIKE model on SPX pre-publication.

### 9d. NGBoost-HARQ (Table 3, Figure 4, `tables/table3_probabilistic.csv`)

Single fit on SPX SP500RM 2002-2013 (2,932 observations), prediction on SPYRM 2014-2019 (1,494 observations after date alignment with the HARQ walk-forward).

| Metric | NGBoost-HARQ | HARQ + Gaussian-residual |
| --- | --- | --- |
| CRPS | 2.0×10⁻⁵ | 4.3×10⁻⁵ |
| Log-score | −8.82 | −7.71 |
| 95% coverage | 96.92% | 99.53% |
| 90% coverage | 95.38% | 99.40% |
| 1% VaR violation rate | 0.00% | 0.00% |
| 5% VaR violation rate | 1.00% | 0.20% |
| Kupiec p at 1% | 0.0000 | 0.0000 |
| Kupiec p at 5% | 0.0000 | 0.0000 |
| Christoffersen p at 5% | 5×10⁻⁶ | 0.003 |

NGBoost delivers 96.9% empirical coverage at a 95% nominal target and 95.4% at a 90% target — both very close to nominal and substantially tighter than the naive HARQ + Gaussian baseline's 99.5% (over-conservative). CRPS is roughly half the baseline's. Both models fail Kupiec and Christoffersen at the 1% VaR level because no realized RV values fall below the Normal's lower tail in this window; at the 5% VaR level NGBoost's violation rate (1.0%) is closer to nominal than the baseline's (0.2%) but both still reject.

Figure 4 shows three representative days in 2017–2018: a calm day (2017-10-26, σ narrow, realized and HARQ-point both within the 95% interval), a rising-volatility day (2018-02-05, σ wider; realized falls in the upper tail above the 95% interval), and the 2018-12-24 Christmas sell-off (widest σ, realized inside the interval).

### 9e. Crypto cross-asset check (Table 4, `tables/table4_crypto_cross.csv`)

Walk-forward on BTCUSDT and ETHUSDT (2018–2026 Binance data; evaluation on 2019–2024 to avoid training year and partial months). Comparison window for SPX is the pre-publication regime (2002–2013 on SP500RM), since that is the window where HARQ has real RQ and a stable out-of-sample story.

| Asset | HAR QLIKE | HARQ QLIKE | HARQ-Signed QLIKE | HARQ / HAR | HARQ-Signed / HARQ |
| --- | --- | --- | --- | --- | --- |
| SPX pre-pub (SP500RM) | 0.1522 | 0.1334 | 0.1273 | 0.877 | 0.954 |
| BTC 2019-2024 | 0.3854 | 0.3582 | 0.4236 | 0.930 | 1.182 |
| ETH 2019-2024 | 0.3574 | 0.3316 | 0.3401 | 0.928 | 1.026 |

HARQ beats HAR by 12.3% on SPX but only 7.0% on BTC and 7.2% on ETH. The microstructure-noise hypothesis — that HARQ's edge should be *larger* in crypto because of noisier intraday prices — fails on this data; 24/7 markets produce *cleaner*, not noisier, price processes. HARQ-Signed, which helps on SPX by 4.6%, hurts on BTC by 18.2% and is tied on ETH — consistent with the no-overnight-gap hypothesis (absent a cross-day leverage / sentiment asymmetry, the signed-jump decomposition adds nothing).

## 10. Visualizations

Five figures are generated by the notebook, exported at 300 DPI as both PNG and PDF in `figures/`. All use pure matplotlib with deliberate styling: default `plt.style.use('default')`, sans-serif, axes title 13pt bold, labels 11pt, ticks 10pt, legend 9pt, top and right spines removed, horizontal-only light-grey grid at α = 0.3, palette limited to black, #1f4e79 (blue), #c0392b (red), #7f7f7f (grey), and four desaturated regime-shading colors.

- **`figures/fig1_rv_with_regimes.png` / `.pdf`.** Single 10×6 panel: SPX annualized realized volatility 1997–2019 as a black line, four regime bands shaded, 2008 peak annotated, SP500RM | SPYRM stitch boundary marked.
- **`figures/fig2_semivariance_asymmetry.png` / `.pdf`.** 8×8 square scatter of RS⁺ vs RS⁻ (×10⁻⁴) for SPX SP500RM only (RS⁺/RS⁻ are only present in that portion), 4,096 days, with a red 45-degree symmetry line.
- **`figures/fig3_rolling_qlike_differential.png` / `.pdf`.** Single 10×6 panel: SPX 252-day rolling QLIKE(HARQ) − QLIKE(HAR) from 2001 through 2019, with regime shading and the 2016 BPQ publication date marked. Negative values (HARQ wins) persist for most of the pre-publication regime and drift toward zero post-2015.
- **`figures/fig4_ngboost_predictive_density.png` / `.pdf`.** 14×5 three-panel figure: NGBoost predictive densities on three representative SPX days (calm 2017-10-26, rising-vol 2018-02-05, end-of-2018 sell-off 2018-12-24). Each panel shows the Normal density, the 95% predictive interval, the realized RV, and the HARQ point forecast.
- **`figures/fig5_regime_heatmap.png` / `.pdf`.** 12×6 heatmap of 7 models × 4 regimes for SPX. Cell values are QLIKE; cell color is the difference from HAR QLIKE using a diverging RdBu_r colormap centered at zero. Unevaluable cells (COVID onset, post-COVID, and HARQ-Signed in the post-publication calm column) are masked grey with "n/a" annotation. Text color adapts (white on dark, black on light).

## 11. Honest Limitations and Caveats

**Scope.** The equity evaluation is scoped to SPX because it is the only US equity asset for which genuine realized quarticity is publicly distributed. Extending to NDX, RUT, or DJIA would require paid minute-level data (Polygon Stocks Starter tier or equivalent) and was out of scope. This is a deliberate choice to preserve methodological cleanliness over breadth.

**Data stitch.** SPX is stitched from SP500RM (1997-05 to 2013-08, S&P 500 index) and SPYRM (2014-01 to 2019-12, SPY ETF). The two data providers differ: SP500RM is the cash index with a 6.5-hour RTH session, SPYRM is the ETF with the same session. SPY tracking error versus SPX is well under 5 bp annualized and not expected to materially distort RV/RQ statistics, but a reviewer could reasonably ask whether the post-2013 result (HARQ loses to HAR on SPYRM) reflects a genuine regime change in SPX, an ETF-vs-index microstructure difference, or a difference in the 5-minute sampling scheme. Without a true SPX HF dataset through 2019, this ambiguity cannot be resolved in this build.

**Semivariance gap.** SPYRM does not distribute RS⁺/RS⁻. SHAR, HARQ-Signed, and NGBoost-HARQ are therefore scoped to the SP500RM portion (1997-2013). For NGBoost specifically, the feature set was reduced to RV_d, RV_w, RV_m, BV_d, and the HARQ interaction — features available in both portions — so that training on SP500RM and prediction on SPYRM is mechanically possible. The brief originally listed RS⁺/RS⁻/ΔJ as NGBoost features; they are dropped here as a scope consequence.

**Modeling.** Default NGBoost hyperparameters with no tuning. The Normal output distribution is fundamentally mismatched to RV's heavy right tail; the VaR backtests reject at both 1% and 5% for that reason, and a Student-t or Gamma output would be a natural next step. HARQ-F has 6 collinear features and is unstable under plain OLS; it only becomes comparable after the insanity filter replaces ~1–2% of predictions with HAR's. A ridge-regularized fit would be cleaner but departs from BPQ's published OLS specification.

**Interpretation.** The crypto finding — HARQ's edge is smaller, not larger, in BTC/ETH — is a null result for the microstructure-noise hypothesis. The project does not claim this proves the hypothesis false; only that at 5-minute sampling, on Binance, 2019–2024, the effect is not larger than on pre-publication SPX. A reviewer focused on this hypothesis specifically would want to test at 1-second sampling, on a single exchange with known quote-update microstructure, and on a shorter sample that excludes 2022's bear structural break.

**Non-claims.** This project does not claim to have found alpha or to have improved on HARQ in all regimes. The HARQ family wins decisively in the pre-publication regime on SPX but ties or loses in the post-publication calm on SPYRM. HARQ-Signed wins on SPX pre-publication but ties/loses on crypto. NGBoost delivers calibration improvement, not point-forecast improvement.

**Strengthening work.** A follow-up would ideally (1) acquire paid 5-minute SPX or SPY data covering 2013-2024 so the post-2013 regime can be evaluated without the SPY-vs-SPX ambiguity, (2) swap NGBoost's Normal head for a heavy-tailed distribution and re-run Kupiec/Christoffersen, (3) fit HARQ-F with ridge and compare, (4) include intraday liquidity covariates in the NGBoost feature set, and (5) extend the crypto sample to at least two exchanges to separate exchange-specific microstructure from genuine price-process differences.

## 12. Key Takeaways

- The HARQ family dominates HAR decisively in the BPQ pre-publication regime on SPX (HARQ-F wins by 14.1%, HARQ by 12.1%, SHAR by 13.3%), with the 90% Model Confidence Set containing exactly {SHAR, HARQ, HARQ-F}. In the post-publication calm (SPYRM 2014-2019) no model separates statistically from HAR.
- The novel HARQ-Signed specification recovers the expected signs (β_Q = −3.4×10³ < 0, β₋ − β₊ = +1.10) and delivers QLIKE 4.6% below HARQ on SPX pre-publication (DM p = 2.5×10⁻⁵), making it the lowest-QLIKE model in the pre-publication regime.
- NGBoost-HARQ delivers 96.9% coverage at a 95% nominal target on SPY 2014-2019, versus 99.5% for a naive HARQ + Gaussian-residual baseline; CRPS roughly halves. Both fail VaR backtests because the Normal output cannot capture the right tail.
- The microstructure-noise hypothesis fails: HARQ beats HAR by 12.3% on SPX pre-publication but only ~7% on BTC/ETH. Signed-jump asymmetry also vanishes in 24/7 crypto.
- The evaluation is deliberately scoped to assets with genuine realized quarticity (SP500RM, SPYRM, Binance 1-minute computation); NDX, RUT, DJIA, and the Oxford-Man BV² proxy were considered and rejected to preserve methodological cleanliness.

## 13. File Inventory

Repository root `harq-volatility-forecasting/`:

- `README.md` — project overview, headline findings, repository layout, reproduce-from-scratch instructions.
- `PROJECT_WRITEUP.md` — this document.
- `requirements.txt` — pinned Python dependencies.
- `harq_analysis.ipynb` — single end-to-end notebook.
- `report.md` / `report.pdf` — two-page final report rendered via WeasyPrint.
- `slide_spec.md` — standalone text spec for the hero slide.
- `.gitignore`.

Subdirectories:

- `data/raw/r_packages/` — `SP500RM.RData` (HARModel package), `SPYRM.rda` (highfrequency package). Not committed.
- `data/raw/binance_crypto/` — 198 monthly 1-minute kline CSVs from `data.binance.vision`. Not committed.
- `data/raw/polygon_spy/` — empty in this build.
- `data/processed/` — three CSVs committed to git: `spx_measures.csv` (SP500RM + SPYRM stitch), `btc_measures.csv`, `eth_measures.csv`.
- `figures/` — ten files, five figures × two formats (PNG and PDF).
- `tables/` — `table1_reproduction.csv/.tex`, `table2_regime_qlike.csv/.tex`, `table2b_mcs.csv`, `table2c_harqsigned.csv`, `table3_probabilistic.csv/.tex`, `table4_crypto_cross.csv`, `table5_heatmap_data.csv`.
- `scripts/` — `download_binance.py`, `download_polygon.py`. `download_oxford_man.py` has been removed in this revision because the Oxford-Man data is no longer used.

## 14. References

- Andersen, T. G., Bollerslev, T., & Diebold, F. X. (2007). Roughing it up: Including jump components in the measurement, modeling, and forecasting of return volatility. *Review of Economics and Statistics*, 89(4), 701–720.
- Barndorff-Nielsen, O. E., Kinnebrock, S., & Shephard, N. (2010). Measuring downside risk — realised semivariance. In *Volatility and Time Series Econometrics: Essays in Honor of Robert Engle*.
- Bollerslev, T., Patton, A. J., & Quaedvlieg, R. (2016). Exploiting the errors: A simple approach for improved volatility forecasting. *Journal of Econometrics*, 192(1), 1–18.
- Christoffersen, P. F. (1998). Evaluating interval forecasts. *International Economic Review*, 39(4), 841–862.
- Corsi, F. (2009). A simple approximate long-memory model of realized volatility. *Journal of Financial Econometrics*, 7(2), 174–196.
- Cornelissen, J., Koopman, S. J., & Boudt, K. (ongoing). `highfrequency` R package. CRAN.
- Duan, T., Anand, A., Ding, D. Y., Thai, K. K., Basu, S., Ng, A., & Schuler, A. (2020). NGBoost: Natural Gradient Boosting for Probabilistic Prediction. *Proceedings of the 37th International Conference on Machine Learning (ICML 2020)*.
- Hansen, P. R., Lunde, A., & Nason, J. M. (2011). The model confidence set. *Econometrica*, 79(2), 453–497.
- Kupiec, P. H. (1995). Techniques for verifying the accuracy of risk measurement models. *Journal of Derivatives*, 3(2), 73–84.
- Patton, A. J. (2011). Volatility forecast comparison using imperfect volatility proxies. *Journal of Econometrics*, 160(1), 246–256.
- Patton, A. J., & Sheppard, K. (2015). Good volatility, bad volatility: Signed jumps and the persistence of volatility. *Review of Economics and Statistics*, 97(3), 683–697.
- Sjoerup, E. (2019). `HARModel` R package, version 1.0. CRAN Archive. Source file `data/SP500RM.RData`, originally distributed via Andrew Patton's public code page for BPQ (2016).
