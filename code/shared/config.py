"""Central path + convention configuration for Problem 11.

Every script should import paths from here so the project layout stays
consistent and easily changeable in one place.

This is the research workspace's `shared/config.py` with the Problem 2
constants removed. Nothing that Problem 11 evaluates was changed: only the
path aliases, the five focus countries and their canonical codes, and the
temporal lags survive. See `../../PUBLIC_RELEASE_AUDIT.md`.
"""

from pathlib import Path

from shared import PROJECT_ROOT

ROOT = PROJECT_ROOT

RAW = ROOT / "dataset" / "raw"
INTERIM = ROOT / "dataset" / "interim"
PROCESSED = ROOT / "dataset" / "processed"
PROBLEM1 = PROCESSED / "problem_1"

METADATA = ROOT / "dataset" / "metadata"
MAPPINGS = METADATA / "mappings"
RECORDS = ROOT / "records"
SCRIPTS = ROOT / "scripts"

# ---------------------------------------------------------------------------
# Research conventions (documented in ../documentation/methodology.md)
# ---------------------------------------------------------------------------

# Focus countries for the national-team work. Codes follow the project's
# canonical national-team codes (eloratings.net style, ISO 3166-1 alpha-2 where
# available). England uses "EN" (not a sovereign-state ISO code).
FOCUS_COUNTRIES = ["Germany", "England", "Spain", "Italy", "France"]
FOCUS_COUNTRY_CODES = ["DE", "EN", "ES", "IT", "FR"]

# The evaluated horizons are t+1..t+4. They are declared locally as `HORIZONS`
# in scripts/models/problem1_baselines.py and problem1_robustness.py rather
# than read from here, so they are deliberately not configured in this module.
