# Code

The analytical and modelling code for Problem 11, taken from the research
workspace. Two files were reduced during packaging; everything else is the code
as it ran.

| Path | Role |
|---|---|
| `shared/__init__.py` | Sets the project root from its own file location |
| `shared/config.py` | Every path used by the pipeline, in one place |
| `shared/tables.py` | Cached readers for the raw eloratings and transfermarkt files |
| `shared/catalog.py` | Which source supplies which table |
| `shared/names.py` | Country and team-name normalisation |
| `shared/logutil.py` | Run logging, which writes to `records/` |
| `scripts/models/models_common.py` | The OLS and expanding-window rolling-origin evaluation harness |
| `scripts/eda/pub_common.py` | The two output helpers the EDA scripts call |
| `scripts/features/build_problem1.py` | Builds the national-team panel and the modelling table from the raw sources |
| `scripts/models/problem1_baselines.py` | Models M0–M3, the persistence benchmark, and the market-value snapshot diagnostic |
| `scripts/models/problem1_robustness.py` | Models R1–R4 and their MAE change against persistence |
| `scripts/eda/problem1_eda.py` | Exploratory checks over the built panel |
| `validate_public_package.py` | Standard-library validator for this published package |

## What was changed during packaging

Two files, both reductions only. No model, no feature, no metric, no threshold
and no evaluation rule was altered.

1. **`shared/config.py`** — the Problem 2 constants were removed: `PROBLEM2`,
   `PROCESSED_SHARED`, `TOP5_LEAGUES`, `TOP5_TM_COMPS`, `U23_AGE`, `U21_AGE`,
   `ELITE_DEFINITIONS`, `ANALYSIS_START_SEASON`, and the shared `LAGS` list.
   Nothing Problem 11 imports was among them. `LAGS` is gone because the
   Problem 11 scripts declare their horizons locally as `HORIZONS` and never
   read it; leaving it would have implied a live control that does not exist.
   The five focus countries and their codes are kept: Problem 11 uses them for
   the Germany slice and for team-name normalisation.
2. **`scripts/eda/pub_common.py`** — reduced to `emit` and `standard_md`, the
   two functions Problem 11 actually calls. The citizenship and focus-country
   lookup tables in the workspace copy belong to the club and player analysis.
   Both retained functions are byte-identical to the workspace originals.

A UTF-8 byte-order mark was also stripped from the front of
`scripts/eda/problem1_eda.py`. It was inherited by the copy; Python tolerates it
on import, but it breaks naive tooling and is invisible in an editor.

## What was not published, and why

| Excluded | Reason |
|---|---|
| `quality/*.py` — the workspace's own validators | Internal release QA for the research workspace, including claim checkers tied to the workspace's own output tree. `validate_public_package.py` replaces this for the published package. |
| `reports/*.py` — report and abstract builders | They assemble the long internal experimental report and its chart set, most of which is not published. They import `pypdf`, `reportlab` and `markdown` for a document this repository does not ship. |
| `logs/*.log` | Run logs from the research workspace. Machine-specific, and they name the workspace's own paths. |
| The Problem 2 figure functions | See below. |

The internal figure builder contains `p2_figure_1` and `p2_figure_2`, which draw
figures for a different research problem. They were **not** published rather
than edited, because the whole script exists to produce a document this
repository does not ship. This follows the convention in the companion
Problem 14 repository, which also publishes its figures as paper artifacts
without shipping the internal reporting chart scripts.

## How the project root resolves

Two independent mechanisms agree on the same directory, which is why no script
needed its paths edited:

- `shared/__init__.py` computes `PROJECT_ROOT = Path(__file__).resolve().parents[1]`,
  which from `code/shared/__init__.py` is `code/`.
- Each script under `code/scripts/<group>/` computes
  `REPO_ROOT = Path(__file__).resolve().parents[2]`, which from
  `code/scripts/<group>/<file>.py` is also `code/`.

So `import shared.config` and `from scripts.models.models_common import ...`
both resolve with `code/` on the path, and the raw-data roots that
`shared/tables.py` builds are `code/dataset/raw/...`. An authorised user creates
`code/dataset/` and drops lawful local inputs in; nothing is edited. See
[`../data/README.md`](../data/README.md).

## Running it

Python 3.12. Install the dependencies, then run the builder and the two
modelling scripts in that order:

```
python -m pip install -r ../requirements.txt
python scripts/features/build_problem1.py
python scripts/models/problem1_baselines.py
python scripts/models/problem1_robustness.py
```

Without the inputs the scripts cannot run, which is expected. The published
package can always be checked without them:

```
python validate_public_package.py
```

The validator uses only the standard library.
