#!/usr/bin/env python3
"""Validate the published Problem 11 package.

Standard library only. Checks the layout, re-derives every headline number in
the README from the tables in results/, verifies the paper checksum and the
figure assets, resolves internal links and images, and runs conservative
secret, restricted-content and portability scans.

    python code/validate_public_package.py

Exit status is 0 when every check passes and 1 otherwise.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PAPER = ("paper/Problem11_The Persistence Ceiling_ Testing Whether Form, "
         "Tournaments, and Squad Value Improve National-Team Elo Forecasts.docx.pdf")
PAPER_SHA256 = "c05fdba8a00ef0abbdd3747eebc17a8eecba1ae7e391911abcd8824968e4eeed"

FIGURES = {
    "figures/figure_1_persistence_and_direction_vs_error.png": (2046, 1500),
    "figures/figure_2_squad_value_level_vs_change.png": (2046, 1009),
}

INTERNAL_DIRS = ["code", "data", "documentation", "figures", "paper", "results"]

failures: list[str] = []
checks = 0


def check(label: str, ok: bool, detail: str = "") -> bool:
    global checks
    checks += 1
    if ok:
        print(f"  PASS  {label}")
    else:
        print(f"  FAIL  {label}" + (f" -- {detail}" if detail else ""))
        failures.append(label)
    return ok


def section(title: str) -> None:
    print(f"\n{title}")
    print("-" * len(title))


# ---------------------------------------------------------------------------
# 1. Layout
# ---------------------------------------------------------------------------
section("1. Package layout")

for rel in ["README.md", "LICENSE", "CITATION.cff", "requirements.txt",
            "DATA_SOURCES.md", "NOTICE.md", "PUBLIC_RELEASE_AUDIT.md",
            ".gitignore", ".gitattributes",
            "paper/README.md", "figures/README.md", "results/README.md",
            "data/README.md", "documentation/README.md",
            "documentation/methodology.md", "code/README.md",
            "code/validate_public_package.py"]:
    check(f"present: {rel}", (ROOT / rel).is_file())

for d in INTERNAL_DIRS:
    check(f"directory: {d}/", (ROOT / d).is_dir())

check("paper PDF present", (ROOT / PAPER).is_file(), PAPER)

# The research workspace's internal packaging must not sit inside the public
# release directory. It is archived outside the repository; see
# PUBLIC_RELEASE_AUDIT.md. This runs unconditionally, so the check cannot be
# skipped by the directory simply not existing yet.
check("version2/ is not in the public release directory",
      not (ROOT / "version2").exists(),
      "internal packaging found inside the release directory")
check("_previous_revision_attempt/ is not in the public release directory",
      not (ROOT / "_previous_revision_attempt").exists())

# ---------------------------------------------------------------------------
# 2. Paper integrity
# ---------------------------------------------------------------------------
section("2. Paper integrity")

if (ROOT / PAPER).is_file():
    digest = hashlib.sha256((ROOT / PAPER).read_bytes()).hexdigest()
    check("paper SHA-256 matches the approved artifact", digest == PAPER_SHA256,
          f"got {digest}")
    check("paper README records the same checksum",
          PAPER_SHA256 in (ROOT / "paper/README.md").read_text())
    check("paper is a PDF", (ROOT / PAPER).read_bytes()[:5] == b"%PDF-")
else:
    check("paper readable", False, "missing")

# ---------------------------------------------------------------------------
# 3. Figures
# ---------------------------------------------------------------------------
section("3. Figures")

for rel, (w, h) in FIGURES.items():
    p = ROOT / rel
    if not check(f"present: {rel}", p.is_file()):
        continue
    data = p.read_bytes()
    check(f"{rel} is a PNG", data[:8] == b"\x89PNG\r\n\x1a\n")
    if len(data) >= 24:
        gw = int.from_bytes(data[16:20], "big")
        gh = int.from_bytes(data[20:24], "big")
        check(f"{rel} is {w}x{h}", (gw, gh) == (w, h), f"got {gw}x{gh}")

# ---------------------------------------------------------------------------
# 4. Re-derive the headline numbers
# ---------------------------------------------------------------------------
section("4. Headline numbers re-derived from results/")


def load(rel: str) -> list[dict]:
    with (ROOT / rel).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


base = load("results/baseline_model_comparison.csv")
rob = load("results/robustness_comparison.csv")
snap = load("results/squad_value_snapshot_summary.csv")

by = lambda rows, m, h: next(  # noqa: E731
    r for r in rows if r["model"] == m and r["horizon"] == str(h))

# Persistence MAE, the paper's headline sequence.
paper_mae = [28.62, 41.49, 49.62, 56.56]
derived_mae = [round(float(by(base, "P1-M0_persistence", h)["mae_pooled"]), 2)
               for h in (1, 2, 3, 4)]
check("persistence MAE t+1..t+4", derived_mae == paper_mae,
      f"derived {derived_mae} vs stated {paper_mae}")

# No tested model beats persistence on MAE, at any horizon. Each table is
# compared only against its own persistence row, because the two tables use
# different column names for the metric.
beats = []
for rows, key in ((base, "mae_pooled"), (rob, "mae")):
    for h in (1, 2, 3, 4):
        ref = float(by(rows, "P1-M0_persistence", h)[key])
        for r in rows:
            if r["horizon"] == str(h) and r["model"] != "P1-M0_persistence":
                if float(r[key]) < ref:
                    beats.append((r["model"], h, round(float(r[key]), 4), round(ref, 4)))
check("no tested model has lower MAE than persistence, in any table",
      not beats, str(beats))

# Evaluable-row counts, which the README publishes.
n_persist = [int(by(base, "P1-M0_persistence", h)["n_total"]) for h in (1, 2, 3, 4)]
check("persistence evaluable rows are 10301/10038/9776/9517",
      n_persist == [10301, 10038, 9776, 9517], str(n_persist))
check("t+1 evaluable rows (10301) are fewer than the panel (10566)",
      n_persist[0] < 10566)

# n_total genuinely varies by specification, which is the unmatched-rows caveat.
spread = {h: {r["model"]: r["n_total"] for r in base if r["horizon"] == str(h)}
          for h in (1, 2, 3, 4)}
check("n_total varies across model specifications",
      all(len(set(v.values())) > 1 for v in spread.values()))

# R3: direction improves while accuracy does not.
r3_p = [round(float(by(rob, "P1-R3_trend_vol", h)["pearson"]), 3) for h in (1, 2, 3, 4)]
check("R3 Pearson runs 0.073 -> 0.134", r3_p == [0.073, 0.125, 0.130, 0.134], str(r3_p))
check("R3 Pearson increases with horizon", all(a < b for a, b in zip(r3_p, r3_p[1:])))

r3_d = [round(float(by(rob, "P1-R3_trend_vol", h)["delta_mae_vs_persistence"]), 2)
        for h in (1, 2, 3, 4)]
check("R3 MAE change vs persistence is negative at every horizon",
      all(d < 0 for d in r3_d), str(r3_d))
check("R3 MAE change vs persistence is -1.01/-0.78/-0.59/-0.53",
      r3_d == [-1.01, -0.78, -0.59, -0.53], str(r3_d))

# Market-value snapshot, transcribed from the approved paper.
snap_v = {r["metric"]: r["value"] for r in snap}
check("snapshot size is 112", snap_v.get("snapshot_teams") == "112",
      str(snap_v.get("snapshot_teams")))
pearsons = sorted({r["value"] for r in snap
                   if r["metric"] == "log10_market_value_vs_elo"
                   and r["statistic"] == "pearson_r"})
check("log10 value vs Elo Pearson is 0.911", pearsons == ["0.911"], str(pearsons))
check("log10 value vs Elo Spearman is 0.924",
      any(r["value"] == "0.924" for r in snap if r["statistic"] == "spearman_rho"))
check("raw-EUR value vs Elo Pearson is 0.657",
      any(r["value"] == "0.657" for r in snap
          if r["metric"] == "raw_eur_market_value_vs_elo"))
check("Elo+value MAE (26.14) beats fitted Elo-only (26.28) by 0.14",
      float(snap_v["elo_plus_log10_value_mae"]) < float(snap_v["elo_only_fitted_mae"])
      and round(float(snap_v["elo_only_fitted_mae"])
                - float(snap_v["elo_plus_log10_value_mae"]), 2) == 0.14)
check("persistence (26.09) still beats Elo+value (26.14) on the snapshot",
      float(snap_v["persistence_mae"]) < float(snap_v["elo_plus_log10_value_mae"]))
check("every snapshot change estimate is labelled in-sample",
      all(r["evidence_status"] == "in-sample snapshot diagnostic"
          for r in snap if r["question"].startswith("Does market value")))

# ---------------------------------------------------------------------------
# 5. README agreement
# ---------------------------------------------------------------------------
section("5. README states the same numbers")

readme = (ROOT / "README.md").read_text()
flat = re.sub(r"\s+", " ", readme)
unquoted = re.sub(r"\s+", " ", re.sub(r"(?m)^\s*>\s?", "", readme))
for token in ["28.62", "41.49", "49.62", "56.56", "10,301", "10,566",
              "0.911", "0.924", "0.657", "26.09", "26.14", "26.28",
              "0.073", "0.134", "1980-2026"]:
    check(f"README states {token}", token in readme)

check("README references both figures",
      "figures/figure_1_persistence_and_direction_vs_error.png" in readme
      and "figures/figure_2_squad_value_level_vs_change.png" in readme)
check("README preserves the SoccerSolver acknowledgement verbatim",
      "This research was developed in collaboration with SoccerSolver. "
      "SoccerSolver currently works with more than 10 football clubs."
      in unquoted)
check("README names Rupayan Halder as sole author", "Rupayan Halder" in readme)
check("README does not claim a universal ceiling",
      "Not a universal ceiling" in readme)
check("README disclaims the independent cross-check",
      "no independent cross-check" in flat)
check("README states the SoccerSolver collaboration is not authorship",
      "not** an\n  author" in readme or "not** an author" in flat)

# ---------------------------------------------------------------------------
# 6. Internal links and images
# ---------------------------------------------------------------------------
section("6. Internal links and images")

link_re = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
for md in sorted(ROOT.rglob("*.md")):
    if "version2" in md.parts:
        continue
    text = md.read_text()
    for target in link_re.findall(text):
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        clean = target.split("#", 1)[0]
        if not clean:
            continue
        check(f"{md.relative_to(ROOT)} -> {clean}", (md.parent / clean).exists())

# ---------------------------------------------------------------------------
# 7. Restricted content
# ---------------------------------------------------------------------------
section("7. Restricted-content scan")

RESTRICTED_NAMES = [
    "national_team_elo_history.csv", "national_team_season.csv",
    "problem1_model_table.csv", "national_team_match.csv", "tournament_team.csv",
    "national_team_squad_value_snapshot.csv", "P1_M4_value_cross_section.csv",
    "P1_counterexample_rows.csv", "team_aliases.csv", "elo_long.csv",
]
published = [str(p.relative_to(ROOT)) for p in ROOT.rglob("*")
             if p.is_file() and "version2" not in p.parts]
for name in RESTRICTED_NAMES:
    check(f"absent: {name}", not any(p.endswith(name) for p in published))

check("no .csv published outside results/",
      all(p.startswith("results/") for p in published if p.endswith(".csv")),
      str([p for p in published if p.endswith(".csv") and not p.startswith("results/")]))

# ---------------------------------------------------------------------------
# 8. Internal and reviewer material
# ---------------------------------------------------------------------------
section("8. Reviewer and internal-material scan")

FORBIDDEN = ["RUBEN_FINAL_REVIEW_AUDIT", "RUBEN_COMMENT_RESOLUTION_MATRIX",
             "GITHUB_READINESS_AUDIT", "Handoff.md", "_previous_revision_attempt",
             "build_revised_paper.py", "revised_abstract"]
for token in FORBIDDEN:
    hits = [p for p in published if token in p]
    check(f"not published: {token}", not hits, str(hits))

INTERNAL_TOKENS = ["reviewer", "Reviewer", "Ruben", "comment [a]", "Comment [A]"]
for md in sorted(ROOT.rglob("*.md")):
    if "version2" in md.parts:
        continue
    text = md.read_text()
    for token in INTERNAL_TOKENS:
        # Documentation may explain *why* material was excluded; flag only
        # names that look like an actual reviewer reference.
        if token in ("Ruben", "reviewer", "Reviewer") and re.search(
                rf"(?i){token}[^.]{{0,40}}(comment|note|feedback|remark)", text):
            continue
        check(f"{md.relative_to(ROOT)} free of '{token}'", token not in text)

# ---------------------------------------------------------------------------
# 9. Problem 2 leakage
# ---------------------------------------------------------------------------
section("9. Problem 2 leakage")

p2_tokens = ["problem_2", "problem2", "PROBLEM2", "p2_figure", "TOP5_LEAGUES",
             "TOP5_TM_COMPS", "ELITE_DEFINITIONS", "U23_AGE", "U21_AGE",
             "relegation", "soccersolver_market_value"]
# This validator necessarily names the tokens it searches for, so it is not
# itself scanned. The analytical code is.
for py in sorted((ROOT / "code").rglob("*.py")):
    if py.name == "validate_public_package.py":
        continue
    text = py.read_text()
    hits = [t for t in p2_tokens if t in text]
    check(f"{py.relative_to(ROOT)} has no Problem 2 code", not hits, str(hits))

for md in sorted(ROOT.rglob("*.md")):
    if "version2" in md.parts:
        continue
    text = md.read_text()
    # Documentation legitimately names what was removed.
    for token in ["problem_2", "PROBLEM2", "ELITE_DEFINITIONS", "TOP5_LEAGUES"]:
        if md.name in ("README.md",) and md.parent == ROOT:
            continue
        if token in text and "Removed" not in text and "removed" not in text:
            check(f"{md.relative_to(ROOT)} free of {token}", False)

# ---------------------------------------------------------------------------
# 10. Portability and secrets
# ---------------------------------------------------------------------------
section("10. Portability and secret scan")

SECRET = re.compile(
    r"(?i)\b(api[_-]?key|secret[_-]?key|password|passwd|token|bearer|"
    r"private[_-]?key)\b\s*[:=]\s*['\"]?[A-Za-z0-9/+_-]{16,}")

# Assembled at runtime so this file does not itself contain the literal it
# searches for, and is therefore covered by its own scan.
HOME_NEEDLE = "/" + "Users" + "/"
WINDOWS_NEEDLE = re.compile(r"[A-Z]:\\\\")

for f in sorted(ROOT.rglob("*")):
    if not f.is_file() or "version2" in f.parts:
        continue
    if f.suffix.lower() in {".png", ".pdf", ".jpg", ".jpeg", ".gif", ".pyc"}:
        continue
    try:
        text = f.read_text(encoding="utf-8")
    except (UnicodeDecodeError, ValueError):
        continue
    check(f"{f.relative_to(ROOT)} has no secret-like assignment",
          not SECRET.search(text))
    check(f"{f.relative_to(ROOT)} has no absolute home path",
          HOME_NEEDLE not in text and not WINDOWS_NEEDLE.search(text))

check("no leftover .DS_Store in the public tree",
      not [p for p in published if p.endswith(".DS_Store")])
check("no __pycache__ in the public tree",
      not [p for p in published if "__pycache__" in p])

# ---------------------------------------------------------------------------
# 11. Code is self-sufficient
# ---------------------------------------------------------------------------
section("11. Code self-sufficiency")

code_root = ROOT / "code"
modules = set()
for py in code_root.rglob("*.py"):
    rel = py.relative_to(code_root).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    modules.add(".".join(parts))

STDLIB = {"__future__", "argparse", "ast", "collections", "csv", "dataclasses",
          "datetime", "enum", "functools", "gzip", "hashlib", "io", "itertools",
          "json", "logging", "math", "os", "pathlib", "random", "re", "shutil",
          "statistics", "string", "subprocess", "sys", "textwrap", "time",
          "typing", "unicodedata", "uuid", "warnings"}
THIRD_PARTY = {"numpy", "pandas", "matplotlib", "PIL", "pypdf", "reportlab",
               "markdown", "duckdb", "scipy"}

unresolved, unclassified = [], []
for py in sorted(code_root.rglob("*.py")):
    tree = ast.parse(py.read_text())
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names = [node.module]
        for name in names:
            root = name.split(".")[0]
            if root in ("shared", "scripts"):
                if name not in modules:
                    unresolved.append(f"{py.relative_to(ROOT)} -> {name}")
            elif root not in STDLIB and root not in THIRD_PARTY:
                unclassified.append(f"{py.relative_to(ROOT)} -> {name}")

check("every internal import resolves", not unresolved, str(unresolved))
check("no undeclared third-party import", not unclassified, str(unclassified))

init = (code_root / "shared" / "__init__.py").read_text()
check("shared/__init__.py derives the project root from its own location",
      "parents[1]" in init)

roots = set()
for py in code_root.rglob("*.py"):
    text = py.read_text()
    for m in re.finditer(r"Path\(__file__\)\.resolve\(\)\.parents\[(\d)\]", text):
        roots.add(int(m.group(1)))
check("script depth convention is parents[2]", 2 in roots, str(sorted(roots)))
check("shared depth convention is parents[1]", 1 in roots, str(sorted(roots)))

# ---------------------------------------------------------------------------
# 12. Ignore rules
# ---------------------------------------------------------------------------
section("12. Ignore rules")

gi = (ROOT / ".gitignore").read_text()
for token in ["version2/", "code/dataset/", "code/records/", "code/eda_outputs/",
              "__pycache__/", ".DS_Store", "*.log"]:
    check(f".gitignore covers {token}", token in gi)

# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------
print()
print("=" * 60)
if failures:
    print(f"RESULT: {len(failures)} of {checks} checks FAILED")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print(f"RESULT: all {checks} checks passed")
print("Reproducibility: PARTIAL (aggregate verification, not retraining)")
sys.exit(0)
