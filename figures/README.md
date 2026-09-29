# Figures

Two figures are published here. Both are the **exact images embedded in the
approved paper** in [`../paper/`](../paper/), extracted losslessly from the PDF's
image streams and re-wrapped as PNG. They are not redrawn, restyled, rescaled or
regenerated, and they were not traced back to the older draft figure files.

| File | Paper caption |
|---|---|
| `figure_1_persistence_and_direction_vs_error.png` | **Figure 1.** Persistence benchmark and direction-versus-error robustness: richer models can improve directional correlation while still failing to beat persistence on out-of-time MAE. |
| `figure_2_squad_value_level_vs_change.png` | **Figure 2.** LEVEL != CHANGE: squad market value strongly describes current strength, but adds almost no next-step change information in the available snapshot. |

| Property | Figure 1 | Figure 2 |
|---|---|---|
| Pixels | 2046 x 1500 | 2046 x 1009 |
| Colour | 8-bit RGB, no alpha | 8-bit RGB, no alpha |
| Extraction | lossless Flate decode of the embedded stream | lossless Flate decode of the embedded stream |

## Why these, and not the other figures in the workspace

The research workspace contains roughly sixty chart images from several rounds of
reporting, many of them duplicates of each other under different names, and a
substantial number built around a single-country case study that the approved
paper deliberately does not use as its narrative. Publishing them would have
introduced contradictions with the paper and a large amount of duplication.

Only the two figures the paper actually uses are published. This matches the
convention in the companion Problem 14 repository, which also publishes its
figures as paper artifacts without shipping the internal reporting chart scripts.

## Verification note

The figures were verified by lossless extraction and by their order in the
PDF's content stream relative to the two figure captions. A pixel-level visual
comparison against the approved layout was not performed as part of packaging.
The image data itself is unmodified.
