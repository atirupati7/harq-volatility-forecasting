# Slide specification — paste this into Gemini to generate the hero slide

## Brief

Build a single 16:9 academic presentation slide. Clean, white
background, dark text, sans-serif body with a serif title. No emojis,
no decorative clipart. Aspect ratio 16:9. Intended audience: quant-team
researchers — they want numbers, not logos.

## Title and subtitle

- **Title (large, top-left):** *Exploiting the errors, revisited*
- **Subtitle (one line below, smaller):** HARQ is the unique best
  volatility forecaster post-publication; NGBoost-HARQ delivers
  calibrated predictive intervals.

## Key-finding callout (large, bold, above the chart)

> In 2014–2019 SPX, HARQ reduces QLIKE by 19% vs HAR and is the lone
> model in the 90% Model Confidence Set. NGBoost-HARQ coverage is 97.7%
> at a 95% target; the naive Gaussian baseline is 99.5%.

## Central visual: SPX QLIKE heatmap (7 models × 4 regimes)

Render this as a heatmap with cell values shown. Use a diverging
red-yellow-green palette normalized per column (so green = best in that
regime, red = worst). Cells with no data (COVID onset / Post-COVID)
should be drawn as empty grey.

**Data (paste verbatim into the heatmap):**

|             | Pre-publication (2000-01→2013-12) | Post-pub calm (2014-01→2019-12) | COVID onset (2020-02) | Post-COVID (2021+) |
|-------------|----------------------------------:|--------------------------------:|----------------------:|-------------------:|
| HAR         | 0.2025                            | 0.2809                          | N/A                   | N/A                |
| HARJ        | 0.1912                            | 0.2998                          | N/A                   | N/A                |
| SHAR        | 0.1918                            | 0.2681                          | N/A                   | N/A                |
| HARQ        | 0.2108                            | **0.2273**                      | N/A                   | N/A                |
| HARQ-F      | 0.2231                            | 0.2428                          | N/A                   | N/A                |
| CHAR        | 0.1935                            | 0.3182                          | N/A                   | N/A                |
| HARQ-Signed | 0.1998                            | 0.2224                          | N/A                   | N/A                |

Notes for the renderer:
- Bold the HARQ cell (0.2273) in the post-pub-calm column as the
  headline finding.
- COVID-onset and Post-COVID columns are left empty with a small
  footnote: "Data gap: Oxford-Man ends 2020-02-21; Polygon free tier
  not available for this build."

## Supporting bullets (below the heatmap, three columns)

1. **Reproduction check.** SHAR QLIKE is 5.4% below HAR on SPX
   2002–2013, exactly as Patton–Sheppard (2015) report. HARQ reduces
   MSE by 4.4% on the same window (BPQ direction).
2. **Novel: HARQ-Signed** pairs BPQ's measurement-error correction
   with Patton–Sheppard signed semivariances. In-sample β<sub>−</sub> −
   β<sub>+</sub> = +1.10 (strong bad-vol persistence). Wins +2.2% on
   SPX, +1.5% on DJIA in post-pub calm.
3. **Crypto check fails the hypothesis.** HARQ's edge over HAR is
   19% on SPX but only 7% on BTC / ETH — 24/7 markets have cleaner
   price processes, not noisier. Signed-jump asymmetry also vanishes in
   crypto (no overnight gaps).

## Bottom-right attribution (small)

*Aprameya Tirupati · GTSF IC Quant Mentorship · Spring 2026*

## Design notes for Gemini

- 16:9 aspect ratio; full-bleed white background.
- Title in dark navy (#1a2a44), body in dark grey (#333).
- Heatmap palette: `RdYlGn_r` inverted — best (lowest QLIKE) = dark
  green (#2a9d8f), worst = red (#e76f51), midpoint = pale yellow. Use a
  diverging normalization per column so values are visually comparable
  within a regime, not across.
- Font: "Inter" or "IBM Plex Sans" for body; "Fraunces" or "Georgia"
  for title.
- Keep whitespace generous. Heatmap should occupy roughly 50% of the
  slide's horizontal real estate.
- No page numbers, no slide decorations, no emojis.
