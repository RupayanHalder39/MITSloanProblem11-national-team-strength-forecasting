# Results

Five aggregate tables. Every number in them comes from the frozen out-of-time
run; nothing here was recomputed, re-estimated or re-rounded for publication.
The row-level tables and the raw inputs they were built from are not published
— see [`../DATA_SOURCES.md`](../DATA_SOURCES.md).

| File | Rows | What it holds |
|---|---|---|
| `baseline_model_comparison.csv` | 16 | Models M0–M3 by horizon: pooled MAE, RMSE, Pearson, Spearman, and the number of evaluable rows |
| `robustness_comparison.csv` | 20 | Models R1–R4 by horizon, each with its MAE change against persistence |
| `robustness_germany.csv` | 20 | The same four robustness models restricted to Germany, as an illustrative single-country slice |
| `per_team_mae.csv` | 65 | MAE and evaluation-row count per national team, pooled across horizons |
| `squad_value_snapshot_summary.csv` | 7 | The market-value snapshot aggregates, transcribed from the approved paper |

## The headline numbers

Persistence MAE by horizon, from `baseline_model_comparison.csv`:

| Horizon | t+1 | t+2 | t+3 | t+4 |
|---|---|---|---|---|
| Persistence MAE | 28.62 | 41.49 | 49.62 | 56.56 |
| Evaluable rows | 10,301 | 10,038 | 9,776 | 9,517 |

No tested feature family reaches a lower out-of-time MAE at any horizon.

## Read `n_total` before comparing two models

The `n_total` column is not decorative. Feature availability changes how many
rows can be evaluated for a given specification, so the models are **not**
compared on an identical row set:

| Horizon | M0 persistence | M1 Elo only | M2 Elo+trend | M3 Elo+trend+tournament |
|---|---|---|---|---|
| t+1 | 10,301 | 10,112 | 9,847 | 9,847 |
| t+2 | 10,038 | 9,849 | 9,587 | 9,587 |
| t+3 | 9,776 | 9,589 | 9,329 | 9,329 |
| t+4 | 9,517 | 9,331 | 9,072 | 9,072 |

A raw MAE difference between two models with different `n_total` is therefore
**not** a paired effect and should not be read as one. This is the same
qualification the approved paper makes.

## The direction-versus-error split

`robustness_comparison.csv` is where the two questions separate. Model R3,
trend plus volatility, raises directional correlation from 0.073 at t+1 to 0.134
at t+4, while its MAE change against persistence stays negative at every
horizon, that is, worse:

| Horizon | t+1 | t+2 | t+3 | t+4 |
|---|---|---|---|---|
| Pearson | 0.073 | 0.125 | 0.130 | 0.134 |
| MAE change vs persistence | −1.01 | −0.78 | −0.59 | −0.53 |

Additional information about *direction* did not become a more accurate
forecast of the future *level*.

## Market value

`squad_value_snapshot_summary.csv` is a transcription of the figures stated in
the approved paper, kept as a table so the README's claims are checkable
against a file. It is explicitly labelled `in-sample snapshot diagnostic` for
the change estimates. It is **not** out-of-time evidence, and the
row-level cross-section it summarises is not published.

## Provenance

The four `P1_*` tables were each copied from a single canonical location in the
research workspace. The workspace held four byte-identical copies of each; only
one was taken. Line endings were normalised from CRLF to LF; the parsed values
are unchanged and the transformation is verified by
`python code/validate_public_package.py`.
