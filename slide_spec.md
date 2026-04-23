# Slide specification — paste this into Gemini to generate the hero slide

## Brief

Build a single 16:9 academic presentation slide. Clean, white background, dark text, sans-serif body with a serif title. No emojis, no decorative clipart. Aspect ratio 16:9. Audience: quant-team researchers — they want numbers, not logos.

## Title and subtitle

- **Title (large, top-left):** *Exploiting the errors, revisited*
- **Subtitle (one line below, smaller):** On genuine realized quarticity (no BV² proxy), the HARQ family dominates HAR in BPQ's pre-publication regime and the novel HARQ-Signed delivers the lowest QLIKE on SPX 2002-2013.

## Key-finding callout (large, bold, above the chart)

> On SPX 2002-2013 with real RQ, HARQ-F reduces QLIKE by 14.1% vs HAR, HARQ-Signed by 16.0%, and the 90% Model Confidence Set retains only {SHAR, HARQ, HARQ-F}. NGBoost-HARQ on SPY 2014-2019 delivers 96.9% coverage at a 95% target.

## Central visual: SPX QLIKE heatmap (7 models × 4 regimes)

Render this as a heatmap with cell values shown. Use a diverging red-blue palette centered on HAR's QLIKE per column, so blue = beats HAR, red = loses to HAR, empty-grey = unevaluable. Annotate each populated cell with the QLIKE value (four decimals).

**Data (paste verbatim into the heatmap; all values from `tables/table5_heatmap_data.csv`):**

|                 | Pre-publication (n = 3,075) | Post-pub calm (n = 1,494) | COVID onset | Post-COVID 2022+ |
|-----------------|----------------------------:|--------------------------:|------------:|-----------------:|
| HAR             | 0.1495                      | 0.2615                    | n/a         | n/a              |
| HARJ            | 0.1451                      | 0.2592                    | n/a         | n/a              |
| SHAR            | 0.1296                      | n/a                       | n/a         | n/a              |
| HARQ            | 0.1314                      | 0.2689                    | n/a         | n/a              |
| HARQ-F          | 0.1284                      | 0.3035                    | n/a         | n/a              |
| CHAR            | 0.1471                      | 0.2682                    | n/a         | n/a              |
| HARQ-Signed     | **0.1256**                  | n/a                       | n/a         | n/a              |

Notes for the renderer:

- Bold the HARQ-Signed pre-publication cell (0.1256) as the headline: it is the lowest QLIKE in the figure.
- COVID and Post-COVID columns are left empty with a small footnote: "Data gap: SPYRM ends 2019-12-31; filling these regimes requires paid minute data, out of scope."
- Post-pub calm column SHAR and HARQ-Signed cells are marked n/a because SPYRM does not ship positive/negative semivariances.
- The post-publication-calm column shows HAR is the best available model in that regime — include this honestly in the legend or as a small caption underneath.

## Supporting bullets (below the heatmap, three columns)

1. **Reproduction check.** SHAR QLIKE is 5.4% below HAR on SPX 2002-2013 rolling 1,000-day window (DM p = 0.0003), matching Patton–Sheppard (2015). HARQ reduces MSE by 4.4% on the same window, matching BPQ direction.
2. **Novel: HARQ-Signed.** Combines BPQ's √RQ interaction and Patton–Sheppard signed semivariances. In-sample β_Q = −3.4×10³, β₋ − β₊ = +1.10 (bad-vol persistence). Walk-forward on SPX pre-publication: 4.6% below HARQ, DM p = 2.5×10⁻⁵.
3. **NGBoost-HARQ probabilistic forecast.** Normal-output NGBoost on the HARQ feature set delivers 96.9% coverage at a 95% target on SPY 2014-2019 — versus 99.5% for a naive HARQ + Gaussian-residual baseline — and roughly halves CRPS. Calibration is usable for VaR, even though the heavy right tail rejects Normal in 1% Kupiec/Christoffersen tests.

## Bottom-right attribution (small)

*Aprameya Tirupati · GTSF IC Quant Mentorship · Spring 2026*

## Design notes for Gemini

- 16:9 aspect ratio; full-bleed white background.
- Title in dark navy (#1a2a44), body in dark grey (#333).
- Heatmap palette: diverging blue-red (`RdBu_r`), blue = beats HAR, red = loses to HAR, colorbar label "QLIKE − QLIKE(HAR)". Cell text: white on dark cells, black on light.
- Font: "Inter" or "IBM Plex Sans" for body; "Fraunces" or "Georgia" for title.
- Whitespace generous. Heatmap ≈ 50% of horizontal space.
- No page numbers, no slide decorations, no emojis.
