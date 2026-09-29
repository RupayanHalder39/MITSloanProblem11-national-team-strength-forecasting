"""Shared EDA output helpers for Problem 11.

This is the research workspace's `scripts/eda/pub_common.py` reduced to the two
helpers Problem 11 actually calls: `emit` and `standard_md`. The citizenship and
focus-country lookup tables that remain in the workspace copy belong to the
club/player analysis and are not used by any Problem 11 script, so they are not
reproduced here. Neither retained helper was altered.

See `../../PUBLIC_RELEASE_AUDIT.md`.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def emit(folder: Path, name: str, data: pd.DataFrame,
         fig=None, md_text: str | None = None) -> list[Path]:
    """Save .csv (always) and optional .png/.md to `folder`.

    Returns the list of written paths.
    """
    folder.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    if data is not None:
        csv_path = folder / f"{name}.csv"
        data.to_csv(csv_path, index=False)
        written.append(csv_path)
    if fig is not None:
        png_path = folder / f"{name}.png"
        fig.savefig(png_path, dpi=160, bbox_inches="tight")
        plt.close(fig)
        written.append(png_path)
    if md_text is not None:
        md_path = folder / f"{name}.md"
        md_path.write_text(md_text.strip() + "\n", encoding="utf-8")
        written.append(md_path)
    return written


def standard_md(title: str, *, shows: str, does_not_show: str,
                supports: str, weakens: str, alternatives: str,
                limitations: str) -> str:
    """Build the FACT/OBSERVATION/HYPOTHESIS interpretation text block."""
    return f"""# {title}

**FACT (what the data shows).** {shows}

**OBSERVATION (what the graph DOES NOT show).** {does_not_show}

**HYPOTHESIS (descriptive, not causal).** {supports}

**Where this WEAKENS the opportunity hypothesis.** {weakens}

**Alternative explanations.** {alternatives}

**Data limitations.** {limitations}
"""
