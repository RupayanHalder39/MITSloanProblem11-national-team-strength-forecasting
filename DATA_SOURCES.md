# Data sources

Every source behind the results in [`results/`](results/), what it was used
for, and why it is or is not redistributed here. Source-by-source licence terms
are in [`NOTICE.md`](NOTICE.md); what an authorised user must rebuild is in
[`data/README.md`](data/README.md).

**No source data is published in this repository.** The decisions below are
deliberate.

## Summary

| Source | Used for Problem 11 | Redistribution position | Published here |
|---|---|---|---|
| eloratings.net | The outcome variable, and every rating-history feature | Redistribution limited to research excerpts | No |
| transfermarkt-datasets | Tournament-history features; the market-value snapshot | Mirror declared CC0, but the underlying valuations are opinion-based third-party data | No |
| SoccerSolver dashboard | Club-level supporting evidence only; **not** used in any published result | No licence documented | No |

## 1. eloratings.net — World Football Elo Ratings

- Attribution: **eloratings.net, by Kirill Bullygin**.
- Endpoint patterns: `World.tsv`, `en.teams.tsv`, and one `<year>.tsv` per year.
- Used for: the national-team Elo series, the outcome variable behind every
  published MAE, and the rating-history features (`elo_change_1y`,
  `elo_centered_3y`, and the rolling volatility and scale terms derived in
  `code/scripts/models/problem1_robustness.py`).
- Format caveat carried over from the research workspace: the TSV fields are
  positional. On the yearly files the code is at index 2 and Elo at index 3; on
  `en.teams.tsv` the name is at index 3. Do not rely on header names alone.
- **Not published.** The provider's terms are self-published and limit
  redistribution to research excerpts. The raw series, the derived
  national-team panel, and the row-level modelling table are all withheld.

## 2. transfermarkt-datasets — CC0 mirror by David Caribou

- Attribution: the **transfermarkt-datasets** dataset by **David Caribou**, a
  published CC0 mirror of data originating from transfermarkt.com.
- Used for: `games` and `national_teams`, which supply the EURO and FIWC
  tournament-history features behind model M3, and the squad market-value
  snapshot.
- This project uses the published dataset and **does not scrape
  transfermarkt.com** directly, whose terms forbid it.
- Coverage caveat: the mirror author's automated update was itself paused in
  mid-July 2026, so games end around 2026-06-28 and valuations around
  2026-06-12. The snapshot's `snapshot_date` field records this.
- **Not published, and treated more conservatively than the upstream licence
  suggests.** The mirror is declared CC0 by its author, but that declaration
  covers the mirror, not clearly the underlying opinion-based market values
  published by transfermarkt.com. Because the licence position for the
  valuations themselves is not established, the row-level cross-section, the
  per-team market values, and every table containing them are withheld. The
  derived aggregates are published instead, in
  [`results/squad_value_snapshot_summary.csv`](results/squad_value_snapshot_summary.csv).

## 3. SoccerSolver league-analysis dashboard

- A local, user-provided HTML artifact. No scraping and no network fetch were
  used to obtain it.
- Used for: **club-level** market-value-versus-outcome evidence only, as
  supporting context in the internal research write-up.
- **Not used in any result published in this repository**, and not published
  here. No licence is documented inside the artifact.
- The models in that dashboard are stated by the dashboard itself to be
  **in-sample**. Nothing derived from them appears in the published tables or
  in the approved paper.

## Sources deliberately not used

- **football-data.co.uk** — not used for any published Problem 11 result. No
  independent cross-check of the rating series is claimed anywhere in this
  repository.
- **FBref / Sports Reference** — excluded; scraping is prohibited by their
  terms.
- **StatsBomb** — not downloaded, and **no StatsBomb coverage is claimed**.
- **transfermarkt.com directly** — prohibited by their terms, and not used.

## What this means for the claims

The Elo series has **no independent cross-check** in this work. That is a real
limitation on the results, it is stated in the paper, and it is not papered
over here: the persistence benchmark is a benchmark against the rating
system's own persistence, and Elo compresses match results rather than
measuring football quality.
