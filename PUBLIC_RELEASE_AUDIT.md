# Public release audit

What went into this repository, what was deliberately left out, and why. Written
so that a reader can disagree with the packaging decisions rather than having to
reverse-engineer them.

Verify the package at any time with:

```
python code/validate_public_package.py
```

---

## 1. The paper

| Decision | Detail |
|---|---|
| Published | Yes, one PDF, in `paper/` |
| How | Byte-for-byte copy of the approved artifact |
| SHA-256 | `c05fdba8a00ef0abbdd3747eebc17a8eecba1ae7e391911abcd8824968e4eeed` |
| Modified | **No.** Not re-saved, re-compressed, re-paginated or edited |
| Placeholders | Two retained deliberately; see below |

The PDF was verified to be the **revised** paper, not the pre-review draft. Its
text carries the corrected panel (1980-2026, 10,301 team-seasons at t+1),
"reference benchmark" rather than a hard-ceiling claim, the
`LEVEL != CHANGE` framing, the in-sample labelling of the market-value
diagnostic, and the qualification that raw MAE is not read as a paired effect
where evaluation rows differ.

### The two retained placeholders

1. `Soccer Paper ID: [To be assigned]`
2. `Open-source repository: [PUBLIC ANONYMIZED GITHUB URL REQUIRED BEFORE SUBMISSION]`

Both were left in place. Filling in the first would mean inventing an
identifier. Filling in the second would mean editing the approved artifact, and
the wording shows the venue's anonymisation requirement is still an open
question. Both are documented in `paper/README.md` and listed in the root
README. **Neither affects any result published here.**

### Excluded from `paper/`

| Excluded | Reason |
|---|---|
| The annotated submission archive (`.docx.zip`) | Carries the reviewer's four comments as author footnotes. Not a publishable artifact. |
| The extracted HTML rendering of that archive | Same reason. |
| The intermediate reviewer-resolution DOCX and its abstract | Superseded by the approved PDF. |
| The earlier abstract package (`abstract.md`/`.html`/`.pdf`) | Superseded, and carries the pre-review framing. |
| `ABSTRACT_VALIDATION.md` | Internal validation notes. |

---

## 2. Figures

**Published:** the two figures, and only the two, that appear in the approved
paper.

They were extracted losslessly from the PDF's embedded image streams — a Flate
decode of the exact image data, re-wrapped as PNG — rather than copied from the
workspace's draft figure files, because **the paper's figures are not the same
files as `Figure_1.png` and `Figure_2.png`**. The embedded images are 2046x1500
and 2046x1009; the workspace drafts are 2157x1784 and 2178x1209. Different
dimensions, so the paper's versions are authoritative and were the ones
published.

Neither figure was redrawn, restyled, rescaled or regenerated.

**Excluded:** roughly sixty other chart images in the workspace, across five
subfolders. They were excluded because they were mostly byte-identical
duplicates of each other under different names, and because a substantial
number were built around a single-country case study the approved paper
deliberately does not use as its narrative. Publishing them would have
introduced both duplication and a second, conflicting story.

**Verification note:** the figures were confirmed by lossless extraction and by
their order in the PDF content stream relative to the two captions. A visual
pixel-level comparison against the approved page layout was not performed
during packaging. The image data is unmodified.

### Figure code

The workspace's figure builder contains `p2_figure_1` and `p2_figure_2`, which
draw figures for a different research problem. The **whole script was excluded
rather than edited**, because it exists to assemble a document this repository
does not publish. The published figures are paper artifacts, which matches the
companion Problem 14 repository's convention.

---

## 3. Results

Five aggregate tables, one canonical copy of each. The workspace held four
byte-identical copies of each source table; only one was taken.

| Published | Rows | Source |
|---|---|---|
| `baseline_model_comparison.csv` | 16 | `results/tables/P1_baseline_comparison.csv` |
| `robustness_comparison.csv` | 20 | `results/tables/P1_robustness_comparison.csv` |
| `robustness_germany.csv` | 20 | `results/tables/P1_robustness_germany.csv` |
| `per_team_mae.csv` | 65 | `results/modeling/P1_per_team_mae.csv` |
| `squad_value_snapshot_summary.csv` | 7 | transcribed from the approved paper |

**Line endings were normalised from CRLF to LF.** The parsed values are
unchanged, and the transformation is verified: each published file is
byte-identical to its source after LF normalisation. No number was recomputed,
re-estimated or re-rounded.

`squad_value_snapshot_summary.csv` is a transcription of the aggregates **stated
in the approved paper**, kept as a table so the README's claims are checkable
against a file. It is not new analysis. The row-level cross-section it
summarises is not published.

### Excluded results

| Excluded | Reason |
|---|---|
| `P1_M4_value_cross_section.csv` | 112 rows of per-team Transfermarkt squad market values. Row-level third-party data; licensing unresolved. |
| `P1_counterexample_rows.csv` | Row-level tournament and Elo detail. |
| `P1_germany_errors.csv` | Superseded by `robustness_germany.csv`, which is a strict superset. |
| `S05_relegation_probability_curves.csv` | A Problem 2 relic; club relegation curves, not used in any Problem 11 result. |
| `M-P1-*`, `R-P1-*`, `P1-0*` figure/table/markdown pairs | Duplicates of the canonical tables or of each other. |
| `modeling/*.png` | Duplicate figure copies. |

---

## 4. Data

**No football data is published.** Reasoning in `NOTICE.md`, file-level
decisions in `DATA_SOURCES.md`, rebuild instructions and schemas in
`data/README.md`.

| Withheld | Why |
|---|---|
| `national_team_elo_history.csv` | eloratings terms limit redistribution to research excerpts. |
| `national_team_season.csv` | Derived directly from the above. |
| `problem1_model_table.csv` | Derived from both the rating series and the tournament tables. |
| `national_team_match.csv`, `tournament_team.csv` | Derived from the transfermarkt mirror. |
| `national_team_squad_value_snapshot.csv` | Row-level opinion-based market values; licence unresolved. |
| `team_aliases.csv` | The mapping used to join sources. |

The transfermarkt mirror is published as CC0 by its author, but this project
treats that as **unverified for the underlying valuations**, because the
declaration covers the mirror rather than clearly the original data. That is
why the cross-section is withheld despite a permissive upstream claim.

The validator fails if any of these filenames appears anywhere in the published
tree.

---

## 5. Code

Published: `code/shared/`, the four Problem 11 scripts, the shared evaluation
harness, the two output helpers, and the package validator.

### Two files were reduced

1. **`shared/config.py`** — Problem 2 constants removed: `PROBLEM2`,
   `PROCESSED_SHARED`, `TOP5_LEAGUES`, `TOP5_TM_COMPS`, `U23_AGE`, `U21_AGE`,
   `ELITE_DEFINITIONS`, `ANALYSIS_START_SEASON`, and the shared `LAGS`. No
   symbol Problem 11 imports was among them; the validator re-checks that every
   internal import still resolves. `LAGS` was dropped because the Problem 11
   scripts declare horizons locally as `HORIZONS` and never read it, so keeping
   it would have implied a live control that does not exist. The five focus
   countries were kept: Problem 11 uses them for the Germany slice and for
   team-name normalisation.
2. **`scripts/eda/pub_common.py`** — reduced to `emit` and `standard_md`. Both
   retained functions were verified **byte-identical** to the workspace
   originals. The citizenship and focus-country lookup tables in the workspace
   copy belong to the club and player analysis.

**No model, feature, metric, threshold or evaluation rule was changed anywhere.**

A UTF-8 BOM was also stripped from `scripts/eda/problem1_eda.py`. It was
inherited by the copy; Python tolerates it on import, but it breaks naive
tooling and is invisible in an editor.

### Why no path edits were needed

`shared/__init__.py` computes the project root as `parents[1]`, and each script
computes the same directory as `parents[2]`. Both resolve to `code/`, so the
existing relative-path logic already produces `code/dataset/raw/...`. The
workspace layout was preserved rather than rewritten.

### Excluded code

| Excluded | Reason |
|---|---|
| `quality/*.py` | The workspace's own validators, including claim checkers bound to its output tree. `validate_public_package.py` replaces this. |
| `reports/*.py` | Build the long internal report and its chart set, most of which is unpublished. Pull in `pypdf`, `reportlab` and `markdown` for a document this repository does not ship. |
| `logs/*.log` | Workspace run logs; machine-specific, name workspace paths. |
| Problem 2 figure functions | See section 2. |

---

## 6. Documentation

**Written fresh, not copied.** `documentation/methodology.md` and the directory
READMEs were written for this repository.

The workspace's own experimental report, per-experiment READMEs and
model-comparison document were **excluded**, for two reasons:

1. **Superseded framing.** They are organised around an "opportunity
   hypothesis" and a Germany-led case study, both of which the approved paper
   dropped.
2. **Stale numbers.** At least one reports the market-value snapshot with
   different values from the approved paper: Spearman 0.9234 rounded to 0.92,
   and the change-model MAE as "26.3 to 26.1", where the paper states 0.924 and
   26.14/26.28/26.09.

Publishing them would have put two different stories and two different numbers
in one repository. The published claims are traceable to exactly two places: the
frozen tables in `results/`, and the approved paper in `paper/`.

### A discrepancy worth recording

`EXP_README_EXP04_market_value.md` in the workspace describes the market-value
change comparison as using "expanding-window OOT", while the approved paper
describes the same exercise as "an in-sample snapshot diagnostic". **The paper's
characterisation was followed**, because the paper is the approved artifact and
`results/squad_value_snapshot_summary.csv` labels every change estimate
`in-sample snapshot diagnostic`. The validator asserts that labelling. If the
in-sample characterisation turns out to be the wrong one, the paper and this
table both need correcting; nothing else in the package depends on it.

---

## 7. Internal material

`version2/` is the research workspace's internal packaging. It contains the
reviewer audit, the comment-resolution matrix, the GitHub readiness audit, the
handoff note, the annotated submission archive, superseded drafts and the
earlier packaging attempt.

**None of it is published.** It is listed in `.gitignore`, and the validator
fails if any of those filenames appears in the published tree.

`version2/` is nevertheless still present in the staging directory, because the
brief was that the master workspace is read-only apart from the staging
directory itself, and the material is worth keeping. **It is not part of the
repository.** Move it out before publishing if a clean directory is preferred.

---

## 8. Naming and layout

The brief suggested `code/` and `documentation/`. The companion Problem 14
repository uses `src/`, `data/`, `docs/`, `results/`, `figures/`, `paper/`,
`NOTICE.md` and `scripts/validate_public_package.py`.

This package keeps the brief's `code/` and `documentation/` names, and adopts
Problem 14's other conventions: a `data/README.md` that states nothing is
distributed and documents the rebuild, a `NOTICE.md` with the source-by-source
licence position, a public-release audit, `.gitattributes` pinning line
endings, and a standard-library validator.

Adopting Problem 14's `src/` name would have broken the workspace's
`parents[1]` / `parents[2]` root resolution and forced path edits into code that
was otherwise unmodified. Keeping `code/` avoided editing the code at all.

---

## 9. Known limitations of this package

- **Reproducibility is PARTIAL.** The code, the aggregate tables, the figures
  and the validator are public. The raw data, the row-level derived tables and
  therefore any end-to-end re-run are not. Verification of aggregate numbers is
  not retraining, and the validator says so.
- **The validator checks consistency, not correctness of method.** It confirms
  the published numbers match the published tables and match the paper. It
  cannot confirm the modelling choices were the right ones.
- **The figures were not visually diffed** against the approved page layout.
- **Two paper placeholders remain open** and must be resolved before submission.
- **`version2/` still sits in the staging directory**, git-ignored but present.
