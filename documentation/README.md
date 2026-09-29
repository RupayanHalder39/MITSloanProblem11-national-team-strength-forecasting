# Documentation

| File | Contents |
|---|---|
| [`methodology.md`](methodology.md) | The design: question, panel, evaluation protocol, models, metrics, the unmatched-rows qualification, and the limitations |
| [`../DATA_SOURCES.md`](../DATA_SOURCES.md) | Every source, what it was used for, and why it is or is not redistributed |
| [`../NOTICE.md`](../NOTICE.md) | Source-by-source terms, attribution, and image rights |
| [`../data/README.md`](../data/README.md) | What an authorised user must rebuild to re-run the pipeline, with schemas |
| [`../results/README.md`](../results/README.md) | The published tables and how to read them |
| [`../code/README.md`](../code/README.md) | Code layout, what changed during packaging, and what was excluded |

## Why the research workspace's own write-ups are not published here

The workspace contains a long experimental report, per-experiment READMEs and a
model-comparison document. None of them are reproduced in this repository, for
two reasons.

1. **Their framing is superseded.** They are organised around an
   "opportunity hypothesis" and a Germany-led case study. The approved paper
   dropped both, and the negative result is now framed as a narrow,
   persistence-relative claim with Germany as an illustrative slice. Publishing
   the older write-ups would put two different stories in one repository.
2. **Some of their numbers are stale.** At least one of them reports the
   market-value snapshot with different values from the approved paper
   (Spearman 0.9234 rounded to 0.92, and the change-model MAE as
   "26.3 to 26.1"). The approved paper's values are the ones published here and
   the ones in `results/squad_value_snapshot_summary.csv`.

The published claims are therefore traceable to exactly two places: the frozen
tables in `results/`, and the approved paper in `paper/`.
