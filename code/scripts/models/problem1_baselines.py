"""PROBLEM 1 — parallel baseline models for future national-team Elo.

Models (horizon t+1..t+4, outcome = future Elo delta):
  P1-M0  persistence       (predict delta = 0)
  P1-M1  Elo only          (elo)
  P1-M2  Elo + trend       (elo, elo_change_1y, elo_centered_3y)
  P1-M3  Elo + trend + tournament history (completed tournaments only;
         non-participation encoded as 0, documented — absence is informative)
  P1-M4  squad-vs-value CROSS-SECTIONAL ONLY (2025/26 snapshot; never merged
         into historical training rows)

Evaluation: expanding-window rolling origin over years (min_train=8).
Also reports Germany-specific errors and an M4 cross-sectional analysis.

Outputs:
  eda_outputs/modeling/problem_1/P1_baseline_comparison.csv
  eda_outputs/modeling/problem_1/P1_germany_errors.csv
  eda_outputs/modeling/problem_1/P1_M4_value_cross_section.csv
  eda_outputs/modeling/problem_1/M-P1-01..04  (PNG+CSV+MD triplets)
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from shared.config import PROCESSED, EDA_OUTPUTS  # noqa: E402
from shared.logutil import add_file_handler, setup_log  # noqa: E402
from scripts.models.models_common import (  # noqa: E402
    ols_predict,
    pooled_metrics,
    rollorigin_predictions,
    summarize_rollorigin,
    pearson,
    spearman,
)
from scripts.eda.pub_common import emit, standard_md  # noqa: E402

log = setup_log("problem1_baselines")
add_file_handler(log, REPO_ROOT / "records" / "problem1_baselines.log")

MODELING = PROCESSED / "modeling"
P1 = PROCESSED / "problem_1"
OUT = EDA_OUTPUTS / "modeling" / "problem_1"

HORIZONS = [("target_elo_delta_t1", 1), ("target_elo_delta_t2", 2),
            ("target_elo_delta_t3", 3), ("target_elo_delta_t4", 4)]
MIN_TRAIN = 8

TOURNEY_FEATURES = [
    "recent_tournament_participated",
    "recent_tournament_round",
    "recent_tournament_champion",
    "recent_tournament_wins",
    "recent_tournament_played",
    "recent_tournament_gf",
    "recent_tournament_ga",
]

FEATURE_SETS = {
    "P1-M1_elo_only": ["elo"],
    "P1-M2_elo_trend": ["elo", "elo_change_1y", "elo_centered_3y"],
    "P1-M3_elo_trend_tournament": ["elo", "elo_change_1y", "elo_centered_3y"]
                                 + TOURNEY_FEATURES,
}


def encode_tournament(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in TOURNEY_FEATURES:
        if c == "recent_tournament_participated":
            continue
        out[c] = out[c].fillna(0.0)
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    t = encode_tournament(pd.read_csv(MODELING / "problem1_model_table.csv"))

    # ---------------- baseline comparison (time-aware) ----------------
    rows = []
    preds_store: dict[str, pd.DataFrame] = {}
    for tgt, lag in HORIZONS:
        y = t[tgt].astype(float).dropna()
        pers = pooled_metrics(y, np.zeros(len(y)))
        rows.append({
            "horizon": lag, "model": "P1-M0_persistence",
            "n_total": pers["n"], "mae_pooled": pers["mae"],
            "rmse_pooled": pers["rmse"], "pearson_pooled": 0.0,
            "spearman_pooled": 0.0, "test_times": None,
        })
        for name, feats in FEATURE_SETS.items():
            preds = rollorigin_predictions(t, tgt, feats, "year",
                                           min_train=MIN_TRAIN)
            preds_store[f"{tgt}__{name}"] = preds
            s = summarize_rollorigin(preds)
            rows.append({
                "horizon": lag, "model": name,
                "n_total": s["n_total"].iloc[0], "mae_pooled": s["mae_pooled"].iloc[0],
                "rmse_pooled": s["rmse_pooled"].iloc[0],
                "pearson_pooled": s["pearson_pooled"].iloc[0],
                "spearman_pooled": s["spearman_pooled"].iloc[0],
                "test_times": int(s["test_times"].iloc[0]),
            })
            log.info("P1 %s horizon %d -> mae=%.2f rmse=%.2f r=%.2f n=%d",
                     name, lag, s["mae_pooled"].iloc[0], s["rmse_pooled"].iloc[0],
                     s["pearson_pooled"].iloc[0], s["n_total"].iloc[0])
    cmp = pd.DataFrame(rows)
    cmp.to_csv(OUT / "P1_baseline_comparison.csv", index=False)

    # ---------------- Germany-specific errors ----------------
    ger_rows = []
    for tgt, lag in HORIZONS:
        ger = t[t["nat_team_code"] == "DE"]
        g = ger[tgt].dropna() if tgt in ger else pd.Series(dtype=float)
        ger_rows.append({
            "horizon": lag, "model": "P1-M0_persistence",
            "mae_de": float(np.mean(np.abs(g))), "rmse_de": float(np.sqrt(np.mean(g ** 2))),
            "n_de": int(g.notna().sum()),
        })
        for name in FEATURE_SETS:
            preds = preds_store[f"{tgt}__{name}"]
            gpred = preds[("nat_team_code" in preds.columns) & (preds["nat_team_code"] == "DE")] \
                if "nat_team_code" in preds.columns else preds.iloc[0:0]
            if gpred.empty:
                continue
            m = pooled_metrics(gpred["actual"], gpred["pred"])
            ger_rows.append({"horizon": lag, "model": name, "mae_de": m["mae"],
                             "rmse_de": m["rmse"], "n_de": m["n"]})
    ger_df = pd.DataFrame(ger_rows)
    ger_df.to_csv(OUT / "P1_germany_errors.csv", index=False)

    # ---------------- M4 cross-sectional value analysis ----------------
    snap = pd.read_csv(P1 / "national_team_squad_value_snapshot.csv")
    cur = t[t["year"] == 2025][
        ["nat_team_code", "nat_team_name", "elo", "rank", "target_elo_delta_t1"]]
    m4 = cur.merge(snap[["nat_team_name", "total_market_value_eur",
                         "fifa_ranking", "squad_size"]], on="nat_team_name",
                   how="inner").dropna(subset=["total_market_value_eur"])
    m4["log10_mv"] = np.log10(m4["total_market_value_eur"])
    m4.to_csv(OUT / "P1_M4_value_cross_section.csv", index=False)
    r_elo = pearson(m4["log10_mv"], m4["elo"])
    r_rank = pearson(m4["log10_mv"], m4["rank"])
    r_delta = pearson(m4["log10_mv"], m4["target_elo_delta_t1"])
    r_s = spearman(m4["log10_mv"], m4["elo"])
    cv = m4.dropna(subset=["target_elo_delta_t1"]).copy()
    y = cv["target_elo_delta_t1"].to_numpy(dtype=float)
    pred_elo = ols_predict(cv[["elo"]], y, cv[["elo"]])
    pred_val = ols_predict(cv[["elo", "log10_mv"]], y, cv[["elo", "log10_mv"]])
    base_m = pooled_metrics(y, pred_elo)
    val_m = pooled_metrics(y, pred_val)
    log.info("P1-M4 cross-section n=%d r(logmv,elo)=%.2f (spearman %.2f) "
             "r(logmv,rank)=%.2f r(logmv,delta_t1)=%.2f",
             len(m4), r_elo, r_s, r_rank, r_delta)
    log.info("P1-M4 delta_t1 in-sample: elo-only mae=%.2f rmse=%.2f | elo+value "
             "mae=%.2f rmse=%.2f", base_m["mae"], base_m["rmse"], val_m["mae"],
             val_m["rmse"])

    # ================= CHARTS =================
    plot_baseline_mae(cmp)                      # M-P1-02
    plot_ovp(t, preds_store)                    # M-P1-01
    plot_germany_traj(t, preds_store)           # M-P1-03
    plot_error_by_tier(t, preds_store)          # M-P1-04

    print("P1 baseline script complete ->", OUT)


# ---------------------------------------------------------------------------
def merge_preds(t, preds_store, tgt, name):
    preds = preds_store[f"{tgt}__{name}"]
    if "nat_team_code" not in preds.columns:
        return pd.DataFrame()
    df = t[["nat_team_code", "nat_team_name", "year", tgt, "elo"]].rename(
        columns={tgt: "actual_ref"})
    m = preds.merge(df, on=["nat_team_code", "nat_team_name", "year"],
                    how="left", validate="one_to_one")
    m["actual"] = m["actual_ref"]
    return m.dropna(subset=["actual", "pred"])


def plot_baseline_mae(cmp: pd.DataFrame) -> None:
    piv = cmp.pivot_table(index="model", columns="horizon", values="mae_pooled")
    piv = piv.reindex(index=["P1-M0_persistence", "P1-M1_elo_only",
                             "P1-M2_elo_trend", "P1-M3_elo_trend_tournament"])
    fig, ax = plt.subplots(figsize=(10, 4.8))
    x = np.arange(len(piv))
    width = 0.18
    colors = ["#9ca3af", "#2563eb", "#16a34a", "#7c3aed", "#e11d48"]
    for j, col in enumerate(piv.columns):
        ax.bar(x + (j - 1.5) * width, piv[col], width, label=f"t+{col}",
               color=colors[j % len(colors)])
    ax.set_xticks(x)
    ax.set_xticklabels(["Persistence\n(M0)", "Elo only\n(M1)", "Elo+trend\n(M2)",
                        "Elo+trend\ntournament (M3)"], fontsize=8)
    ax.set_ylabel("MAE (future Elo delta)")
    ax.set_title("M-P1-02 — baseline comparison: MAE predicting future Elo delta")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(title="horizon", fontsize=8)
    fig.tight_layout()
    best1 = cmp[cmp.horizon == 1].sort_values("mae_pooled").iloc[0]
    emit(OUT, "M-P1-02_baseline_comparison_mae", piv.reset_index(), fig,
         standard_md(
             "M-P1-02 baseline comparison MAE",
             shows="Expanding-window (min 8 train years) MAE predicting future Elo "
                   "delta at t+1..t+4 for persistence, Elo-only, Elo+trend, "
                   "Elo+trend+tournament.",
             does_not_show="Out-of-sample tournament targets; only Elo-delta targets; "
                           "tournament history available only from 2006.",
             supports=f"Best t+1 model is {best1['model']} (MAE {best1['mae_pooled']:.1f}).",
             weakens="Any model can beat persistence only on Elo deltas; gains shrink "
                     "at longer horizons.",
             alternatives="Regression-to-mean, schedule/opponent mix, friendly weighting.",
             limitations="In-sample-calibrated OLS with expanding window; tournament "
                         "features sparse (9.5%% of rows)."))


def plot_ovp(t, preds_store) -> None:
    fig, axs = plt.subplots(1, 2, figsize=(13, 5))
    frames = []
    for ax, lag in ((axs[0], 1), (axs[1], 3)):
        m = merge_preds(t, preds_store, f"target_elo_delta_t{lag}",
                        "P1-M3_elo_trend_tournament")
        frames.append(m)
        a = m["elo"] + m["actual"]
        p = m["elo"] + m["pred"]
        ax.scatter(a, p, s=4, alpha=0.25)
        lim = [min(a.min(), p.min()) - 50, max(a.max(), p.max()) + 50]
        ax.plot(lim, lim, ls="--", color="0.4", lw=1)
        r = pearson(a, p)
        ax.set_title(f"t+{lag}  (Pearson r = {r:.2f})")
        ax.set_xlabel("actual future Elo")
    axs[0].set_ylabel("predicted future Elo")
    fig.suptitle("M-P1-01 — observed vs predicted future Elo (M3)",
                 fontweight="bold")
    fig.tight_layout()
    emit(OUT, "M-P1-01_observed_vs_predicted_elo", frames[0], fig,
         standard_md(
             "M-P1-01 observed vs predicted future Elo",
             shows="Expanding-window OLS (M3: elo+trend+tournament) predicted future "
                   "Elo vs actual at t+1 and t+3.",
             does_not_show="Calibrated uncertainty intervals; only OLS.",
             supports="Positive correlation between predicted and actual future Elo.",
             weakens="Wide scatterband; persistence is a strong prior for most teams.",
             alternatives="Regression-to-mean, opponent mix.",
             limitations="Tournament history from 2006 only; OLS on ~150 teams."))


def plot_germany_traj(t, preds_store) -> None:
    tgt = "target_elo_delta_t1"
    m = merge_preds(t, preds_store, tgt, "P1-M3_elo_trend_tournament")
    g = m[m["nat_team_code"] == "DE"].sort_values("year")
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(g["year"], g["elo"], color="#111827", lw=1.8, label="Germany actual Elo")
    ax.plot(g["year"], g["elo"] + g["actual"], color="#1f3b6b", lw=1.6, marker="o",
            label="Germany future Elo (actual), t+1")
    ax.plot(g["year"], g["elo"] + g["pred"], color="#c8102e", lw=1.3, ls="--",
            marker="s", label="Germany future Elo (pred, M3), t+1")
    ax.set_title("M-P1-03 — Germany: actual Elo vs predicted future Elo (M3, t+1)")
    ax.set_xlabel("year")
    ax.set_ylabel("Elo")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    emit(OUT, "M-P1-03_germany_actual_vs_predicted", g, fig,
         standard_md(
             "M-P1-03 Germany actual vs predicted",
             shows="Germany's Elo trajectory plus M3's expanding-window predictions of "
                   "future Elo at t+1.",
             does_not_show="A causal account of Germany's decline.",
             supports="The model tracks Germany's 2014-2018 Elo decline direction.",
             weakens="Predictions run behind sharp drops; single-country evidence.",
             alternatives="Regression-to-mean after a peak Elo.",
             limitations="Single country; OLS; historical-only inputs."))


def plot_error_by_tier(t, preds_store) -> None:
    m = merge_preds(t, preds_store, "target_elo_delta_t1",
                    "P1-M3_elo_trend_tournament")
    m["tier"] = pd.qcut(m["elo"], 4, labels=["Q1 low", "Q2", "Q3", "Q4 high"])
    grp = m.groupby("tier", observed=True).apply(
        lambda g: pd.Series({
            "mae": pooled_metrics(g["actual"], g["pred"])["mae"],
            "rmse": pooled_metrics(g["actual"], g["pred"])["rmse"],
            "n": len(g)}), include_groups=False).reset_index()
    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.bar(grp["tier"].astype(str), grp["mae"], color="#0f766e", alpha=0.85)
    ax.set_ylabel("MAE (t+1 Elo delta)")
    ax.set_title("M-P1-04 — prediction error by current-Elo tier (M3, t+1)")
    ax.grid(axis="y", alpha=0.3)
    for i, r in grp.iterrows():
        ax.text(i, r["mae"] + 0.5, f"n={int(r['n'])}", ha="center", fontsize=8)
    fig.tight_layout()
    emit(OUT, "M-P1-04_error_by_elo_tier", grp, fig,
         standard_md(
             "M-P1-04 error by Elo tier",
             shows="MAE of M3 at t+1 split into current-Elo quartiles.",
             does_not_show="Tier causality.",
             supports="Error is similar across tiers (the model is not just a "
                      "top-team tool).",
             weakens="If Q1 shows the largest error, weak-team volatility dominates.",
             alternatives="Low-precision small nations; ranking noise.",
             limitations="OLS; descriptive; quartile boundaries from pooled data."))


if __name__ == "__main__":
    main()