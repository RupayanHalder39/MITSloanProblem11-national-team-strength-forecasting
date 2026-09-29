"""Build PROCESSED datasets for PROBLEM 1 (national-team success & decline).

Inputs:  interim/eloratings/*, raw transfermarkt games/national_teams.
Outputs (dataset/processed/problem_1/):
  national_team_elo_history.csv   per (team, year) elo & rank
  national_team_season.csv        yearly features + explicit FUTURE targets
  national_team_match.csv         tournament matches (WC/EURO editions present in data)
  tournament_team.csv             per (team, tournament) stage reached + results
  national_team_squad_value_snapshot.csv  current-snapshot squad value (LIMITED)

Design notes on leakage:
  * All features for year t use only ratings available at the end of year t.
  * Every future outcome is in a column prefixed `target_`; anyone modelling
    must never use them as features at time t.
  * tournament_year for WC/EURO rows derived as season+1 (data convention).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from shared.config import PROBLEM1  # noqa: E402
from shared.catalog import sha256_file as _sh  # noqa: E402 (unused import guard)
from shared.logutil import add_file_handler, setup_log  # noqa: E402
from shared.names import canonical_country_code  # noqa: E402
from shared.tables import elo_team_names, tm  # noqa: E402

log = setup_log("nti.problem1")
add_file_handler(log, REPO_ROOT / "records" / "build_problem1.log")

INTERIM = REPO_ROOT / "dataset" / "interim"

# Elo change thresholds for rise/stable/decline label at +1y (documented baseline
# choice; sensitivity analysis is a next step).
RISE_DELTA = 30.0
DECLINE_DELTA = -30.0

TOURNAMENTS = {"EURO": "Euro", "FIWC": "World Cup"}

# Round depth used to compute stage reached (project convention).
def round_depth(s: str | None) -> float | None:
    if not s or pd.isna(s):
        return None
    rs = str(s)
    if rs.startswith("Group"):
        return 0.0
    if rs == "Round of 32":
        return 1.0
    if rs in ("Round of 16", "Eighth-finals"):
        return 2.0
    if rs == "Quarter-Finals":
        return 3.0
    if rs == "Third Place Play-Off":
        return 3.1
    if rs == "Semi-Finals":
        return 4.0
    if rs == "Final":
        return 5.0
    return None


def load_elo() -> pd.DataFrame:
    df = pd.read_csv(INTERIM / "eloratings" / "elo_long.csv")
    df = df.dropna(subset=["elo"])
    df["elo"] = df["elo"].astype(int)
    df["rank"] = pd.to_numeric(df["rank"], errors="coerce")
    return df


def build_team_season(elo: pd.DataFrame) -> pd.DataFrame:
    first = 1980  # start features from 1980 for a longer history tail
    rows = []
    for code, g in elo.groupby("code"):
        g = g[g["year"] >= first].sort_values("year")
        for i, r in g.iterrows():
            y = int(r["year"])
            rows.append({
                "nat_team_code": code,
                "nat_team_name": r.get("nat_team_name", ""),
                "year": y,
                "elo": int(r["elo"]),
                "rank": r["rank"],
            })
    df = pd.DataFrame(rows)
    df = df.sort_values(["nat_team_code", "year"]).reset_index(drop=True)

    # FEATURES (strictly available at end of year t)
    df["elo_prev_1"] = df.groupby("nat_team_code")["elo"].shift(1)
    df["elo_change_1y"] = df["elo"] - df["elo_prev_1"]
    df["elo_centered_3y"] = (
        df["elo_prev_1"] + df["elo"].shift(2) + df["elo"].shift(3)
    ) / 3  # trailing 3-year average ending before season t
    df["rank_prev_1"] = df.groupby("nat_team_code")["rank"].shift(1)
    df["rank_change_1y"] = df["rank_prev_1"] - df["rank"]  # negative = improvement

    # TARGETS (future, clearly labelled)
    for lag in (1, 2, 3, 4):
        df[f"target_elo_t{lag}"] = df.groupby("nat_team_code")["elo"].shift(-lag)
        df[f"target_elo_delta_t{lag}"] = (
            df[f"target_elo_t{lag}"] - df["elo"]
        )
    df["target_label_rise_stable_decline_t1"] = df["target_elo_delta_t1"].apply(
        lambda d: "rise" if pd.notna(d) and d >= RISE_DELTA else (
            "decline" if pd.notna(d) and d <= DECLINE_DELTA else
            ("stable" if pd.notna(d) else None)))
    return df


def resolve_tm_team(resolver: dict[int, str], names: dict[str, str],
                    aliases: dict[str, str], tm_id: object, display: str) -> tuple[str, str]:
    """Map a tournament game's team to (nat_team_code, resolved_name)."""
    if pd.notna(tm_id) and int(tm_id) in resolver:
        code = resolver[int(tm_id)]
        return code, names.get(code, code)
    name = str(display)
    if name in aliases:
        code = aliases[name]
        return code, names.get(code, code) or name
    return "", name


def build_tournaments() -> tuple[pd.DataFrame, pd.DataFrame]:
    games = tm("games")
    national_teams = tm("national_teams")
    names = elo_team_names()
    inv_names = {v: k for k, v in names.items()}
    map_tm = {}
    for _, r in national_teams.iterrows():
        nm = str(r["name"])
        code = inv_names.get(nm) or canonical_country_code(nm)
        if code:
            map_tm[int(r["national_team_id"])] = code

    nat = games[games["competition_id"].isin(["EURO", "FIWC"])].copy()
    nat["tournament_year"] = nat["season"].astype(int) + 1
    nat["tournament"] = nat["competition_id"].map(TOURNAMENTS)

    # Aliases for team names not present in the tm snapshot (format as for elo names).
    aliases = {}
    for _, r in pd.read_csv(REPO_ROOT / "dataset" / "metadata" / "mappings" / "team_aliases.csv").iterrows():
        raw, can = r["raw_name"], r["nat_team_name"]
        # canonical name -> eloratings code via names reverse lookup
        inv = {v: k for k, v in names.items()}
        code = inv.get(can) or canonical_country_code(can)
        if code:
            aliases[str(raw)] = code

    match_rows = []
    for _, row in nat.iterrows():
        for side, club_id, club_name, gf_key, ga_key in (
            ("home", row["home_club_id"], row["home_club_name"], "home_club_goals", "away_club_goals"),
            ("away", row["away_club_id"], row["away_club_name"], "away_club_goals", "home_club_goals")):
            code, resolved = resolve_tm_team(map_tm, names, aliases, club_id, club_name)
            match_rows.append({
                "tournament": row["tournament"], "tournament_year": int(row["tournament_year"]),
                "match_id": int(row["game_id"]), "round": row["round"],
                "date": row["date"], "nat_team_code": code, "team_name": resolved,
                "opponent": club_name if side == "home" else row["home_club_name"],
                "goals_for": row[gf_key], "goals_against": row[ga_key],
            })
    matches = pd.DataFrame(match_rows)
    log.info("tournament matches: %d (resolved codes: %d/%d)",
             len(matches), matches["nat_team_code"].ne("").sum(), len(matches))

    # tournament-team aggregation
    tourn = []
    for key, sub in matches.groupby(["nat_team_code", "tournament", "tournament_year"]):
        code, tname, tyear = key
        wins = (sub["goals_for"] > sub["goals_against"]).sum()
        loss = (sub["goals_for"] < sub["goals_against"]).sum()
        draws = len(sub) - wins - loss
        depth = sub["round"].map(round_depth)
        max_round = sub.loc[depth.idxmax(), "round"] if len(sub) else ""
        # champion flag: reached Final and won the last match of the tournament for that team
        last = sub.sort_values("date").iloc[-1]
        champion = int(max_round == "Final" and last["goals_for"] > last["goals_against"])
        tourn.append({
            "nat_team_code": code, "tournament": tname, "tournament_year": tyear,
            "team_name": sub.iloc[0]["team_name"], "round_reached": max_round,
            "played": len(sub), "wins": int(wins), "draws": int(draws),
            "losses": int(loss), "goals_for": int(sub["goals_for"].sum()),
            "goals_against": int(sub["goals_against"].sum()),
            "champion": champion,
            "matches": ",".join(map(str, sub["match_id"])),
        })
    teams = pd.DataFrame(tourn).sort_values(
        ["tournament", "tournament_year", "nat_team_code"])
    return matches, teams


def build_squad_value_snapshot() -> pd.DataFrame:
    nt = tm("national_teams")
    names = elo_team_names()
    inv = {v: k for k, v in names.items()}
    rows = []
    for _, r in nt.iterrows():
        code = str(r.get("team_code") or "")
        if not code:
            code = inv.get(str(r["name"]), canonical_country_code(str(r["name"])))
        rows.append({
            "nat_team_code": code,
            "nat_team_name": str(r["name"]),
            "squad_size": r.get("squad_size"),
            "average_age": r.get("average_age"),
            "foreigners_number": r.get("foreigners_number"),
            "total_market_value_eur": r.get("total_market_value"),
            "fifa_ranking": r.get("fifa_ranking"),
            "confederation": str(r.get("confederation") or ""),
            "snapshot_date": "2026-08 (transfermarkt-datasets last update)",
        })
    return pd.DataFrame(rows)


def main() -> None:
    PROBLEM1.mkdir(parents=True, exist_ok=True)
    elo = load_elo()
    elo.to_csv(PROBLEM1 / "national_team_elo_history.csv", index=False)
    log.info("elo history: %d rows", len(elo))

    ts = build_team_season(elo)
    ts.to_csv(PROBLEM1 / "national_team_season.csv", index=False)
    log.info("national_team_season: %d rows, teams %d, years %d-%d",
             len(ts), ts["nat_team_code"].nunique(), ts["year"].min(), ts["year"].max())

    matches, teams = build_tournaments()
    matches.to_csv(PROBLEM1 / "national_team_match.csv", index=False)
    teams.to_csv(PROBLEM1 / "tournament_team.csv", index=False)
    log.info("tournament_team: %d rows; champion resolution example rows:\n%s",
             len(teams), teams[teams["champion"] == 1][
                ["nat_team_code", "tournament", "tournament_year"]].head(12).to_string(index=False))

    sv = build_squad_value_snapshot()
    sv.to_csv(PROBLEM1 / "national_team_squad_value_snapshot.csv", index=False)
    log.info("squad value snapshot: %d rows (LIMITED: current snapshot only)", len(sv))


if __name__ == "__main__":
    main()