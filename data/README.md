# Data

**No football data is distributed in this repository.**

That is a licensing decision, not an oversight. Access to a source is not a
redistribution licence, and the position for the underlying data is not clear
enough to publish it. The source-by-source reasoning is in
[`../NOTICE.md`](../NOTICE.md); the file-level decisions are in
[`../DATA_SOURCES.md`](../DATA_SOURCES.md).

What *is* published is the researcher's own aggregate evidence: the frozen
result tables under [`../results/`](../results/), the two figures under
[`../figures/`](../figures/), and the analytical code under [`../code/`](../code/).

## Inputs, and whether they are published

| Input | Provider | Used for | Published here |
|---|---|---|---|
| National-team Elo ratings, yearly snapshots | eloratings.net, by Kirill Bullygin | The outcome variable, and every feature derived from rating history | **No** — raw series withheld |
| Games, national teams and squad valuations | transfermarkt-datasets, a CC0 mirror of transfermarkt.com data by David Caribou | Tournament history features, and the market-value snapshot | **No** — raw tables withheld |
| Squad market values, club level | SoccerSolver | Supporting club-level value-versus-survival evidence | **No** — not used in any result published here |

The `transfermarkt-datasets` mirror is published by its author as CC0. This
project treats that as **unverified for the underlying valuations**, because
the CC0 declaration covers the mirror rather than clearly the original
opinion-based market values. That is why the row-level cross-section is
withheld even though a permissive licence is claimed upstream.

## Where the code looks for data

`code/shared/tables.py` resolves the two raw roots from its own file location,
so nothing needs editing:

```python
RAW_TM  = <code>/dataset/raw/transfermarkt-datasets
RAW_ELO = <code>/dataset/raw/eloratings
```

`code/shared/config.py` builds every other path from the same project root.
`code/dataset/` and `code/records/` are git-ignored, so a local working copy
does not pollute the repository.

## What a full re-run requires

Reproducing the models end to end is **not possible from this repository
alone**. An authorised user has to assemble the inputs themselves, from sources
they are permitted to use:

```
<work_root>/
└── code/                              # this repository's code/ directory
    ├── shared/
    ├── scripts/
    ├── dataset/                       # <-- create this; git-ignored
    │   ├── raw/
    │   │   ├── eloratings/
    │   │   │   ├── en.teams.tsv       team name -> code
    │   │   │   ├── World.tsv
    │   │   │   └── <year>.tsv         one snapshot per year
    │   │   └── transfermarkt-datasets/
    │   │       ├── games.csv.gz
    │   │       └── national_teams.csv.gz
    │   ├── interim/
    │   │   └── eloratings/
    │   │       └── elo_long.csv       tidy long-format rating history
    │   ├── metadata/
    │   │   └── mappings/
    │   │       └── team_aliases.csv   raw_name, nat_team_name
    │   └── processed/
    │       ├── problem_1/
    │       │   ├── national_team_elo_history.csv
    │       │   ├── national_team_season.csv
    │       │   ├── national_team_match.csv
    │       │   ├── tournament_team.csv
    │       │   └── national_team_squad_value_snapshot.csv
    │       └── modeling/
    │           └── problem1_model_table.csv
    └── records/                       # run logs (git-ignored)
```

`code/scripts/features/build_problem1.py` writes the `processed/problem_1/`
files from the raw inputs. The modelling table at
`processed/modeling/problem1_model_table.csv` is the shared normalised panel
that both the baseline and the robustness scripts read.

## Schemas of the withheld tables

Documented so an authorised user can rebuild them without guesswork. Column
names and row counts are as built, not as described from memory.

### `problem_1/national_team_season.csv` — 10,566 rows, 19 columns

One row per national team per year, rated men's national teams, **1980-2026**.

| Column | Type | Meaning |
|---|---|---|
| `nat_team_code` | str | Canonical national-team code, eloratings.net style |
| `nat_team_name` | str | Team name as published by the source |
| `year` | int | Year label `t` |
| `elo` | float | Elo rating in year `t` |
| `rank` | float | Published rank in year `t` |
| `elo_prev_1` | float | Elo in year `t-1` |
| `elo_change_1y` | float | `elo` minus `elo_prev_1` |
| `elo_centered_3y` | float | `elo` minus the trailing three-year team mean |
| `rank_prev_1` | float | Rank in year `t-1` |
| `rank_change_1y` | float | `rank` minus `rank_prev_1` |
| `target_elo_t1` … `target_elo_t4` | float | Elo at `t+lag` |
| `target_elo_delta_t1` … `_t4` | float | Elo at `t+lag` minus Elo at `t`; the four evaluated horizons |
| `target_label_rise_stable_decline_t1` | str | Three-way label used for the direction analysis |

The panel holds 10,566 team-seasons. The 10,301 figure quoted for the t+1
horizon is the number of rows that remain **evaluable** once the target exists
and features are non-missing, which is why it is smaller.

### `modeling/problem1_model_table.csv` — 10,566 rows, 31 columns

The same panel plus the tournament-history features consumed by model M3:

| Column | Type | Meaning |
|---|---|---|
| `recent_tournament_participated` | int | 1 if the team entered a EURO or FIWC within the recent window |
| `recent_tournament_years_ago` | float | Years since the team's most recent tournament |
| `recent_tournament_round` | float | Round reached, depth-encoded |
| `recent_tournament_champion` | int | 1 if the team won that tournament |
| `recent_tournament_wins` | float | Wins in that tournament |
| `recent_tournament_played` | float | Matches played |
| `recent_tournament_gf`, `recent_tournament_ga` | float | Goals for and against |
| `target_tournament_round_2y`, `_4y` | float | Round reached at the 2-year and 4-year horizon |
| `target_tournament_participated_2y`, `_4y` | int | Participation flags at those horizons |
| `target_tournament_wins_2y`, `_4y` | float | Wins at those horizons |

Tournaments are restricted to `EURO` and `FIWC` in the source, and
`tournament_year` is derived as `season + 1`.

### `problem_1/national_team_squad_value_snapshot.csv` — 124 rows, 9 columns

One snapshot row per national squad, `snapshot_date` recorded as
`2026-08 (transfermarkt-datasets last update)`.

| Column | Type | Meaning |
|---|---|---|
| `nat_team_code`, `nat_team_name` | str | Team identity |
| `squad_size` | int | Players in the snapshot squad |
| `average_age` | float | Mean age |
| `foreigners_number` | int | Foreign players in the squad |
| `total_market_value_eur` | float | Aggregate squad market value, **opinion-based** |
| `fifa_ranking` | int | FIFA ranking |
| `confederation` | str | Confederation |
| `snapshot_date` | str | Snapshot stamp |

The cross-section analysed in the paper has **n = 112**, which is this 124-row
snapshot after the merge to the Elo panel. Aggregates are published in
[`../results/squad_value_snapshot_summary.csv`](../results/squad_value_snapshot_summary.csv);
the rows are not.

## Reproducibility classification: PARTIAL

- **Public:** the analytical code, the aggregate results, the paper figures, and
  a validator that re-checks every published headline number against those
  results.
- **Conditional:** rebuilding the inputs from lawful local copies of the
  sources, then re-running the pipeline under `code/`.
- **Not provided:** the raw data, and the row-level derived tables.

Aggregate verification is not retraining. `code/validate_public_package.py`
confirms that the published numbers are internally consistent and match the
frozen values. It does not re-estimate a single model.
