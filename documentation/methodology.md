# Methodology

The design behind the published results. Read this before the numbers in
[`../results/`](../results/), because the evaluation protocol determines what
those numbers can support.

## The question

Federations and analysts read recent form, tournament performance, volatility
and squad value as signs that a national team is rising or fading. This study
does not assume those signals are interchangeable. It asks a narrower,
checkable question:

> **When current Elo is already known, does any richer historical signal carry
> additional out-of-time information about future national-team Elo?**

## Three different questions, kept apart

The study's central design decision is that "is this team getting better?" is
not one question but three, and a signal can answer one and fail the others.

| Question | Quantity | Metric |
|---|---|---|
| **LEVEL** | Where does the team stand now? | Cross-sectional association |
| **DIRECTION** | Which way is it moving? | Pearson, Spearman on the change |
| **ERROR** | Does the forecast get better? | Out-of-time MAE |

The results separate these cleanly, and the separation is the finding. Squad
market value is a strong **LEVEL** signal and a weak **CHANGE** signal.
Trend-plus-volatility improves **DIRECTION** correlation and does not improve
**ERROR**. Collapsing the three would have hidden both.

## Sample and panel

A frozen national-team-season modelling panel of rated men's national teams
covering **1980-2026**, with **10,566** team-season rows. Future Elo change is
evaluated at four horizons, **t+1 through t+4**.

The headline evaluable-row figure is **10,301 at t+1**, which is smaller than
the panel because the target must exist and the features must be non-missing.
The count falls further at longer horizons and varies by specification; see the
`n_total` discussion below.

**Future Elo is the forecasting outcome, not a claim about ground-truth
football quality.** Elo is a rating that updates in response to match results.
Forecasting it well is not the same as forecasting football.

## Evaluation protocol

Expanding-window, rolling-origin, **out-of-time** pooling. Each model is fitted
only on strictly earlier data and predicts the next block. There is no random
split anywhere, because a random split across calendar time leaks the future
into the past.

A minimum of 8 training periods is required before a model is evaluated. The
evaluation harness is `code/scripts/models/models_common.py`, and both modelling
scripts use the same one.

**This matters for interpretation.** Because Elo itself updates in response to
match-result surprises, carrying the current rating forward is a *naturally
demanding* benchmark when future Elo is the target. Persistence is not an
arbitrary floor placed under the results; a large part of it is built into the
target's construction. That is why the finding is stated as "no tested feature
family improved out-of-time MAE in this evaluation" and not as a general
ceiling.

## Models

### Baselines, `code/scripts/models/problem1_baselines.py`

| Model | Features |
|---|---|
| M0 persistence | None; the current rating carried forward |
| M1 Elo only | `elo` |
| M2 Elo + trend | `elo`, `elo_change_1y`, `elo_centered_3y` |
| M3 Elo + trend + tournament | M2 plus seven EURO/FIWC tournament-history features |

### Robustness, `code/scripts/models/problem1_robustness.py`

| Model | Features |
|---|---|
| R1 volatility-scaled | `elo_vol_3y` |
| R2 mean reversion | `elo_centered_3y` |
| R3 trend + volatility | `elo`, `elo_change_1y`, `elo_centered_3y`, `elo_vol_3y` |
| R4 team scale | `elo`, `elo_change_1y`, `elo_meanabs_5y` |

The volatility and scale terms are derived inside the robustness script as
per-team rolling statistics computed as-of each row's year, so no future
information enters a feature.

### Market-value snapshot diagnostic

A separate, smaller exercise: one snapshot of 112 national squads, relating
squad market value to **current** Elo, and to the next-step Elo change. It is
reported as an **in-sample snapshot diagnostic**, and it is labelled that way
everywhere it appears. See the limitations below.

## Metrics

- **MAE** measures forecast accuracy and is the headline metric.
- **RMSE** is reported alongside it.
- **Pearson and Spearman** are used only to assess **directional** signal, and
  are never presented as accuracy.

A correlation is not an accuracy gain. A model can identify the sign of a
movement while predicting its magnitude worse than doing nothing.

## The unmatched-rows qualification

Feature availability changes how many rows are evaluable for a given
specification, so the models are **not** compared on an identical row set. At
t+1, persistence is evaluated on 10,301 rows, M1 on 10,112, and M2 and M3 on
9,847.

Raw MAE is therefore reported **without treating an unmatched comparison as a
paired effect**. A MAE difference between two models evaluated on different row
sets is not a clean like-for-like delta, and the published tables keep
`n_total` visible so this cannot be quietly ignored.

## Germany

Germany is reported as an illustrative single-country slice in
[`../results/robustness_germany.csv`](../results/robustness_germany.csv). It is
**not** the study's narrative and no claim rests on it. A five-focus-country
slice is small, and country-level results of this kind are sensitive to which
countries are selected.

## Limitations

- **Not causal.** Everything here is predictive association on observational
  data. No intervention is studied and no policy conclusion is offered.
- **Persistence is partly expected by construction.** See the protocol section.
  The claim is narrow and conditional, not a general ceiling.
- **Elo is the target and Elo is also the main feature.** A rating system that
  updates on results is partly self-predicting. This is a real constraint on
  what the benchmark comparison can show.
- **Elo is not a complete measure of national-team strength.** It compresses
  match results.
- **No independent cross-check of the rating series.** football-data.co.uk was
  unreachable from the research environment and was not bypassed. No FBref or
  StatsBomb data is used and no coverage of either is claimed.
- **Unmatched evaluation rows.** See above.
- **The market-value result is a snapshot, not a time series.** It is
  in-sample, single-snapshot, and cannot establish an out-of-time gain. No
  historical national-team market-value series was available to test it
  properly.
- **Conditional on the tested models, horizons and feature availability.** A
  negative result for this specification set is not a proof that no richer
  signal could ever help.

## What the study does not claim

It does not claim that form, tournament history, volatility or squad value are
useless for national-team analysis. It claims that, **in this evaluation, on
this target, at these horizons**, none of them reduced out-of-time MAE below
persistence — while some of them did carry real directional information. Those
two facts are compatible, and separating them is the point.
