# NOTICE

Source-by-source terms, attribution, and image rights for this repository.
Data-source decisions are in [`DATA_SOURCES.md`](DATA_SOURCES.md).

## What is licensed here

The MIT licence in [`LICENSE`](LICENSE) covers the researcher's own work in
this repository:

- the code under `code/`
- the aggregate result tables under `results/`
- the two figures under `figures/`
- the documentation and the repository metadata files

## What is NOT distributed here

**No football data is redistributed in this repository.** That includes the
raw source files, the normalised panels, the row-level derived tables, and the
per-team market values. The reasoning is per source below and in
[`DATA_SOURCES.md`](DATA_SOURCES.md).

## Attribution

### Elo ratings

**eloratings.net**, by Kirill Bullygin. Used as the outcome variable and as the
basis of the rating-history features. The provider's terms are self-published
and limit redistribution to research excerpts, so **no Elo data is published
here**.

### Club, player, appearance and valuation tables

The **transfermarkt-datasets** dataset by **David Caribou**, a published CC0
mirror of data originating from transfermarkt.com. This project uses the
published dataset and does not scrape transfermarkt.com.

**No data from this source is published here.** The CC0 declaration covers the
mirror; the licence position for the underlying opinion-based market values is
not established, so the conservative position is taken and the row-level
valuations are withheld.

### SoccerSolver

SoccerSolver supplied a local league-analysis artifact used as club-level
supporting context in the internal research write-up. It is not the source of
any result published in this repository, and none of its data is published
here. No licence is documented for that artifact.

## Image rights

The two PNGs under `figures/` are the researcher's own charts, produced for this
research, and are covered by the MIT licence in [`LICENSE`](LICENSE). They were
extracted losslessly from the approved paper; see [`figures/README.md`](figures/README.md).

No third-party photograph, screenshot, club badge, crest or logo is published in
this repository.

## The paper

The PDF under `paper/` is the researcher's own conference paper, included for
identification and citation under the same MIT licence. It contains no
third-party images. It retains two placeholders pending conference submission,
documented in [`paper/README.md`](paper/README.md).

## A note on the research collaboration

> This research was developed in collaboration with SoccerSolver. SoccerSolver
> currently works with more than 10 football clubs.

SoccerSolver is a research collaborator and acknowledgement. It is **not** an
author, and it is not claimed to be a funder, sponsor or owner of this research.
Its name and logo are used for identification only, and its inclusion implies
no endorsement. None of its data is used in any result published here.
