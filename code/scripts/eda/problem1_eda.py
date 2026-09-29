"""EDA charts for PROBLEM 1 (national team health/decline).

Descriptive only: Elo trajectories, tournament results, label diagnostics.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

matplotlib.use("Agg")

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from shared.config import EDA_OUTPUTS, PROBLEM1  # noqa: E402


def main() -> None:
    EDA_OUTPUTS.mkdir(parents=True, exist_ok=True)

    nts = pd.read_csv(PROBLEM1 / "national_team_season.csv")
    elo = pd.read_csv(PROBLEM1 / "national_team_elo_history.csv")
    tour = pd.read_csv(PROBLEM1 / "tournament_team.csv")
    snap = pd.read_csv(PROBLEM1 / "national_team_squad_value_snapshot.csv")

    # Elo trajectory: focus nations + a couple of reference teams
    focus = ["DE", "EN", "ES", "IT", "FR", "BR", "AR"]
    ss = elo[elo["code"].isin(focus)].copy()
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for code, grp in ss.groupby("code"):
        ax.plot(grp["year"], grp["elo"], linewidth=2.0, label=code)
    ax.set_title("Elo rating history of focus national teams (1901-2026)")
    ax.set_xlabel("year"); ax.set_ylabel("Elo")
    ax.grid(alpha=0.3); ax.legend(ncol=2, fontsize=9)
    fig.tight_layout(); fig.savefig(EDA_OUTPUTS / "p1_elo_trajectories.png", dpi=140)
    plt.close(fig)

    # Label distribution
    lab = nts["target_label_rise_stable_decline_t1"].dropna().map(str).value_counts()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(lab.index.astype(str), lab.values, color="#4472c4")
    ax.set_title("Distribution of target label (1-year change in Elo, ||<=30 stable)")
    ax.set_ylabel("national-team-seasons"); ax.grid(alpha=0.3, axis="y")
    fig.tight_layout(); fig.savefig(EDA_OUTPUTS / "p1_label_distribution.png", dpi=140)
    plt.close(fig)

    # Tournament finishes: round distribution over time
    rank = tour["round_reached"] if "round_reached" in tour else tour["round_depth"]
    rv = tour["round_reached"].value_counts()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.barh(rv.index, rv.values, color="#70ad47")
    ax.set_title("Tournament appearances by highest round reached (focus teams)")
    ax.set_xlabel("team-tournament appearances")
    fig.tight_layout(); fig.savefig(EDA_OUTPUTS / "p1_tournament_rounds.png", dpi=140)
    plt.close(fig)

    # Current snapshot: value vs fifa ranking (cross-section, no causality)
    s = snap.dropna(subset=["total_market_value_eur", "fifa_ranking"])
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(s["fifa_ranking"], s["total_market_value_eur"] / 1e6, alpha=0.7, s=40)
    ax.set_title("2025/26 snapshot: squad market value vs FIFA ranking (association only)")
    ax.set_xlabel("FIFA ranking (higher = worse position)")
    ax.set_ylabel("squad market value (EUR m)")
    ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(EDA_OUTPUTS / "p1_value_vs_fifa_ranking_snapshot.png", dpi=140)
    plt.close(fig)

    print("wrote p1 EDA charts to %s" % EDA_OUTPUTS)


if __name__ == "__main__":
    main()