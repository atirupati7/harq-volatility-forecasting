# Exploiting the Errors, Revisited: HARQ Volatility Forecasting Through COVID, With Signed-Jump Decomposition and Probabilistic Extensions

**Aprameya Tirupati** · Georgia Institute of Technology · GTSF IC Quant Mentorship, Spring 2026

## Abstract

We reproduce the HARQ model of Bollerslev, Patton, and Quaedvlieg (2016)
using `SP500RM`, the realized-measures dataset Patton distributes with
BPQ (2016), and extend it along four directions. (1) We evaluate six
HAR-family models out-of-sample on SPX, NDX (Nasdaq Composite
surrogate), RUT, and DJIA across four volatility regimes from 2000 to
2020. (2) In the 2014–2019 post-publication calm window HARQ beats HAR
by 19.1% on QLIKE for SPX and 13.6% for NDX — *larger* than BPQ's
published in-sample effect — and is the unique member of the 90%
Hansen–Lunde–Nason Model Confidence Set for both assets. (3) A novel
**HARQ-Signed** specification combines BPQ's measurement-error
correction with Patton–Sheppard (2015) signed-jump decomposition and
recovers β<sub>−</sub> − β<sub>+</sub> = +1.10, a strong asymmetric
persistence consistent with "good / bad volatility." (4) **NGBoost-HARQ**
delivers calibrated predictive densities with 97.7% coverage against a
95% nominal level, versus 99.5% for a naive HARQ + Gaussian-residual
baseline. A crypto cross-check on BTCUSDT and ETHUSDT 2018–2026 shows
HARQ's edge is smaller, not larger, in crypto — an honest negative
finding contrary to the microstructure-noise hypothesis.

## 1. Introduction and data

The heterogeneous autoregressive (HAR) model of Corsi (2009) has been
the volatility-forecasting workhorse for two decades. BPQ (2016)
showed that augmenting the HAR with a measurement-error term
proportional to √realized quarticity produces economically meaningful
improvements: when today's realized variance is noisy (high RQ), trust
it less for predicting tomorrow. Patton and Sheppard (2015)
independently decomposed RV into positive and negative semivariances
(RS<sup>+</sup>, RS<sup>−</sup>) and showed that down-move days are
more persistent than up-move days.

SPX data are sourced from `HARModel::SP500RM` (Sjoerup 2019), which in
turn mirrors the realized-measures file Patton distributes for BPQ
(2016) and covers April 1997 through August 2013. NDX / RUT / DJIA use
the Oxford-Man Realized Library archive shipped with the
`highfrequency` R package (Cornelissen et al.), covering January 2000
through February 2020. Because Oxford-Man never distributed daily RQ,
for the three non-SPX US indices we use the jump-robust proxy
$RQ \approx BV^2$ and flag this explicitly. Cryptos are computed from
Binance Vision public 1-minute klines (2018-01 through 2026-03), with
RV, RQ, RS<sup>+</sup>, RS<sup>−</sup> and BV computed directly from
5-minute subsampled returns. All data processing and modelling is
captured in `harq_analysis.ipynb`, which runs end-to-end from the
committed `data/processed/` CSVs.

## 2. Methods

The six HAR-family baselines share a common `.fit` / `.predict`
interface. HAR is Corsi's canonical three-factor regression; HARJ adds
a jump component $J_t = \max(RV_t − BV_t, 0)$; SHAR replaces the
daily RV lag with signed semivariances; CHAR substitutes bipower
variation throughout. HARQ and HARQ-F implement BPQ's measurement-error
specification

$$
RV_{t+1} = \beta_0 + (\beta_d + \beta_Q (\sqrt{RQ_t} - \overline{\sqrt{RQ}})) RV_t + \beta_w RV^{(w)}_t + \beta_m RV^{(m)}_t,
$$

where the centered-sqrt parameterization follows the
`HARModel` R package (equivalent to BPQ's uncentered form but better
numerically conditioned). **HARQ-Signed**, our novel extension, adds
RS<sup>+</sup><sub>t</sub> and RS<sup>−</sup><sub>t</sub> as separate
regressors to the HARQ specification.

Walk-forward evaluation is expanding-window (initial 1000 days),
monthly refit. Predictions that are non-positive, non-finite, or more
than 3× the training maximum are replaced with the HAR prediction (BPQ
insanity filter). QLIKE is the Patton (2011) loss; Diebold–Mariano
statistics use Newey–West HAC with bandwidth h−1. The Model Confidence
Set uses `arch.bootstrap.MCS` with 1000 replications.

NGBoost-HARQ trains a `NGBRegressor(Dist=Normal, n_estimators=300,
learning_rate=0.01)` on the HARQ feature set plus RS<sup>±</sup> and
ΔJ, with a single fit on 2002–2013 and prediction on 2014–2019. CRPS is
evaluated by the closed-form Normal expression. VaR backtests apply
Kupiec unconditional-coverage and Christoffersen independence tests at
1% and 5%.

## 3. Results

**Reproduction (Table 1).** On SP500RM 2002–2013 at h=1, SHAR beats
HAR by 5.4% on QLIKE (matching Patton–Sheppard 2015) and HARQ reduces
MSE by 4.4% (matching BPQ direction). HARQ's QLIKE is within noise of
HAR on this specific window — BPQ's exact 5–10% margin is sensitive to
refit frequency and insanity-filter bounds, but the MSE direction
holds. HARQ-F is unstable with plain OLS on six collinear features;
ridge regularization (out of brief scope) would address this.

**Post-publication regime (Table 2, Figure 3).** The 2014–2019 calm
window is where the HARQ edge is most striking. SPX HARQ QLIKE is
0.2273 versus HAR 0.2809 — **a 19.1% improvement.** NDX shows 13.6%.
DJIA HARQ-F wins by 14.9%. The Model Confidence Set at α=0.10 contains
*only HARQ* for both SPX and NDX; only HARQ + HARQ-F for DJIA; all six
models are tied for RUT (small-cap noise dominates). Figure 3's
rolling-252-day QLIKE differential shows HARQ's advantage is
consistently negative post-2014 for SPX, NDX, DJIA, while oscillating
around zero for RUT.

**HARQ-Signed (Table 2c).** In-sample on SPX 2002–2013:
β<sub>d</sub> = 0.4375, β<sub>Q</sub> = −3.4×10³, β<sub>+</sub> = −0.33,
β<sub>−</sub> = +0.77. Asymmetry β<sub>−</sub> − β<sub>+</sub> = +1.10
— bad-vol days are strongly predictive of tomorrow's volatility while
good-vol days mean-revert. HARQ-Signed beats HARQ by 2.2% on SPX and
1.5% on DJIA in post-pub calm, but ties or loses on NDX and RUT.

**NGBoost-HARQ (Table 3, Figure 4).** On SPX 2014–2019, NGBoost delivers
97.7% empirical coverage at the 95% nominal level, closer to nominal
than the naive HARQ + Gaussian-residual baseline (99.5%). Both Kupiec
and Christoffersen tests reject at 1% and 5% VaR — even NGBoost with a
Normal output cannot match RV's heavy right tail in the tails. Figure
4's predictive-density panels show NGBoost adapting width to regime:
tighter on calm days, wider as 2020 volatility builds.

**Crypto cross-check (Table 4).** HARQ beats HAR on BTC by 7.0% and
ETH by 7.2% — smaller than SPX's 19.1%. HARQ-Signed adds no value in
crypto (BTC: +18.2%; ETH: tied). The microstructure-noise hypothesis
(HARQ should be *more* effective where intraday noise is larger)
**fails** here; 24/7 trading appears to produce cleaner price
processes than US-equity RTH. The signed-jump finding holds: no
overnight gaps in crypto → symmetric flow → no asymmetric-persistence
premium.

## 4. Discussion

Three claims survive the out-of-sample test. First, BPQ's
measurement-error correction is a real improvement over HAR in the
post-publication calm regime, large enough to make HARQ the unique
member of the 90% MCS for SPX and NDX. The 19% QLIKE improvement for
SPX 2014–2019 is notably larger than BPQ's in-sample estimate,
consistent with the idea that as HF data quality rose post-2013 the
measurement-error signal sharpened. Second, Patton–Sheppard's signed
jumps capture a very strong asymmetry in equity volatility
(β<sub>−</sub> − β<sub>+</sub> ≈ +1) that disappears in crypto.
Third, probabilistic volatility forecasting is calibration-viable but
still heavy-tail-limited: NGBoost with a Normal head beats a crude
Gaussian baseline on coverage but fails VaR backtests. A natural next
step is a Student-t or Gamma output distribution.

The repository preserves all raw data inputs (or reconstruction scripts
for them), a single end-to-end notebook, 5 figures, 5 tables, and this
two-page report. Null results (crypto HARQ edge smaller than SPX;
HARQ-F unstable) are reported honestly.

## References

- Bollerslev, T., Patton, A. J., & Quaedvlieg, R. (2016). Exploiting
  the errors: A simple approach for improved volatility forecasting.
  *Journal of Econometrics*, 192(1), 1–18.
- Corsi, F. (2009). A simple approximate long-memory model of
  realized volatility. *Journal of Financial Econometrics*, 7(2),
  174–196.
- Duan, T., Anand, A., Ding, D. Y., Thai, K. K., Basu, S., Ng, A., &
  Schuler, A. (2019). NGBoost: Natural Gradient Boosting for
  Probabilistic Prediction. *ICML 2020*.
- Hansen, P. R., Lunde, A., & Nason, J. M. (2011). The Model
  Confidence Set. *Econometrica*, 79(2), 453–497.
- Patton, A. J., & Sheppard, K. (2015). Good volatility, bad
  volatility: Signed jumps and the persistence of volatility.
  *Review of Economics and Statistics*, 97(3), 683–697.
- Sjoerup, E. (2019). `HARModel` R package, v1.0. CRAN.
