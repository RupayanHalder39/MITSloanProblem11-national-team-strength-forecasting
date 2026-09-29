"""PROBLEM 1 — final robustness: can a transparent persistence-relative model
beat simple Elo persistence on OUT-OF-TIME MAE?

Models (horizon t+1..t+4, outcome = future Elo delta), all OLS via the shared
expanding-window framework, all evaluated against P1-M0 persistence (delta=0):

  P1-R1  volatility-scaled persistence   y ~ [elo_vol_3y]
  P1-R2  mean reversion / Elo decay      y ~ [elo_centered_3y]
  P1-R3  recent trend + volatility       y ~ [elo, elo_change_1y,
                                              elo_centered_3y, elo_vol_3y]
  P1-R4  team-specific change scale      y ~ [elo, elo_change_1y,
                                              elo_meanabs_5y]

Extra features are derived IN THIS SCRIPT (group-by rolling over
elo_change_1y, window computed as-of each row's year — no future leakage) and
are NOT written back to the modeling table.

PRIMARY SUCCESS CRITERION (per mandate): a model is useful only if it improves
OUT-OF-TIME pooled MAE against persistence. Correlation-only gains do not count.

Outputs:
  eda_outputs/modeling/problem_1_robustness/P1_robustness_comparison.csv
  eda_outputs/modeling/problem_1_robustness/P1_robustness_germany.csv
  eda_outputs/modeling/problem_1_robustness/R-P1-01..04 (PNG+CSV+MD triplets)
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
    pooled_metrics,
    rollorigin_predictions,
    pearson,
)
from scripts.eda.pub_common import emit, standard_md  # noqa: E402

log = setup_log("problem1_robustness")
add_file_handler(log, REPO_ROOT / "records" / "problem1_robustness.log")

MODELING = PROCESSED / "modeling"
OUT = EDA_OUTPUTS / "modeling" / "problem_1_robustness"

HORIZONS = [("target_elo_delta_t1", 1), ("target_elo_delta_t2", 2),
            ("target_elo_delta_t3", 3), ("target_elo_delta_t4", 4)]
MIN_TRAIN = 8

MODEL_NAMES = ["P1-M0_persistence", "P1-R1_vol_scaled", "P1-R2_mean_reversion",
               "P1-R3_trend_vol", "P1-R4_team_scale"]
COLORS = {"P1-M0_persistence": "#9ca3af", "P1-R1_vol_scaled": "#2563eb",
          "P1-R2_mean_reversion": "#16a34a", "P1-R3_trend_vol": "#7c3aed",
          "P1-R4_team_scale": "#e11d48"}


def add_historical_volatility(t: pd.DataFrame) -> pd.DataFrame:
    """Derive per-team rolling volatility/scale features (as-of row year).

    Uses only elo_change_1y (changes INTO the row's year), which is known when a
    t+1..t+4 Elo-delta target is set. No future values are used.
    """
    out = t.copy().sort_values(["nat_team_code", "year"])
    g = out.groupby("nat_team_code", sort=False)["elo_change_1y"]
    out["elo_vol_3y"] = g.transform(
        lambda s: s.rolling(3, min_periods=2).std())
    out["elo_meanabs_5y"] = g.transform(
        lambda s: s.rolling(5, min_periods=3).apply(
            lambda w: np.mean(np.abs(w)), raw=False))
    return out


FEATURE_SETS = {
    "P1-R1_vol_scaled": ["elo_vol_3y"],
    "P1-R2_mean_reversion": ["elo_centered_3y"],
    "P1-R3_trend_vol": ["elo", "elo_change_1y", "elo_centered_3y", "elo_vol_3y"],
    "P1-R4_team_scale": ["elo", "elo_change_1y", "elo_meanabs_5y"],
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    t = add_historical_volatility(pd.read_csv(MODELING / "problem1_model_table.csv"))

    rows = []
    preds_store: dict[str, pd.DataFrame] = {}
    for tgt, lag in HORIZONS:
        y = t[tgt].astype(float).dropna()
        pers = pooled_metrics(y, np.zeros(len(y)))
        rows.append({
            "horizon": lag, "model": "P1-M0_persistence",
            "n_test": pers["n"], "mae": pers["mae"], "rmse": pers["rmse"],
            "pearson": 0.0, "spearman": 0.0,
            "delta_mae_vs_persistence": 0.0,
        })
        for name, feats in FEATURE_SETS.items():
            preds = rollorigin_predictions(t, tgt, feats, "year", min_train=MIN_TRAIN)
            preds_store[f"{tgt}__{name}"] = preds
            m = pooled_metrics(preds["actual"], preds["pred"])
            delta = pers["mae"] - m["mae"]
            rows.append({
                "horizon": lag, "model": name, "n_test": m["n"],
                "mae": m["mae"], "rmse": m["rmse"], "pearson": m["pearson"],
                "spearman": m["spearman"], "delta_mae_vs_persistence": delta,
            })
            log.info("P1 %s t+%d mae=%.2f rmse=%.2f r=%.2f delta_mae=%.2f n=%d",
                     name, lag, m["mae"], m["rmse"], m["pearson"], delta, m["n"])
    cmp = pd.DataFrame(rows)
    cmp.to_csv(OUT / "P1_robustness_comparison.csv", index=False)

    # fixed-row evaluation (same test rows across models, per horizon)
    fixed = []
    for tgt, lag in HORIZONS:
        keys = list(preds_store.keys())
        frames = []
        for k in keys:
            if not k.startswith(f"{tgt}__"):
                continue
            p = preds_store[k][["test_time", "year", "nat_team_code", "actual", "pred"]]
            p = p.rename(columns={"pred": k})
            frames.append(p)
        if not frames:
            continue
        joint = frames[0][["test_time", "year", "nat_team_code", "actual"]]
        for k in keys:
            if not k.startswith(f"{tgt}__"):
                continue
            joint = joint.merge(frames[0] if False else
                                preds_store[k][["test_time", "year", "nat_team_code", "actual", "pred"]]
                                .rename(columns={"pred": k})[
                                    ["test_time", "year", "nat_team_code", k]],
                                on=["test_time", "year", "nat_team_code"], how="left")
        fixed.append((lag, joint))

    # Germany-specific robustness
    ger_rows = []
    ger_dfs = {}
    for tgt, lag in HORIZONS:
        g = t[t["nat_team_code"] == "DE"]
        yy = g[tgt].dropna()
        pers_m = pooled_metrics(yy, np.zeros(len(yy)))
        ger_rows.append({"horizon": lag, "model": "P1-M0_persistence",
                         "mae_de": pers_m["mae"], "rmse_de": pers_m["rmse"],
                         "n_de": pers_m["n"], "delta_mae_vs_persistence": 0.0})
        for name in FEATURE_SETS:
            preds = preds_store[f"{tgt}__{name}"]
            gp = preds[(preds["nat_team_code"] == "DE")].copy()
            if gp.empty:
                continue
            m = pooled_metrics(gp["actual"], gp["pred"])
            ger_rows.append({"horizon": lag, "model": name, "mae_de": m["mae"],
                             "rmse_de": m["rmse"], "n_de": m["n"],
                             "delta_mae_vs_persistence": pers_m["mae"] - m["mae"]})
            ger_dfs[f"{tgt}__{name}"] = gp
    ger_df = pd.DataFrame(ger_rows)
    ger_df.to_csv(OUT / "P1_robustness_germany.csv", index=False)

    # ---------------- summary for doc + report ----------------
    best = cmp[cmp.delta_mae_vs_persistence > 0.0]
    if best.empty:
        log.info("NO model improves OOT MAE vs persistence at any horizon.")
    else:
        b = best.sort_values("delta_mae_vs_persistence", ascending=False).iloc[0]
        log.info("best robustness model: %s horizon t+%d delta_mae=%.2f",
                 b["model"], b["horizon"], b["delta_mae_vs_persistence"])

    plot_mae_vs_persistence(cmp)
    plot_delta_mae(cmp)
    plot_ovp(t, preds_store)
    plot_germany(ger_df)

    print("P1 robustness script complete ->", OUT)


# ---------------------------------------------------------------------------
def plot_mae_vs_persistence(cmp: pd.DataFrame) -> None:
    piv = cmp.pivot_table(index="model", columns="horizon", values="mae")
    piv = piv.reindex(index=MODEL_NAMES)
    fig, ax = plt.subplots(figsize=(10, 4.8))
    x = np.arange(len(piv))
    width = 0.16
    for j, col in enumerate(piv.columns):
        color = COLORS["P1-M0_persistence"] if piv.index.isin(
            ["P1-M0_persistence"]).any() else None
        ax.bar(x + (j - 1.5) * width, piv[col], width, label=f"t+{col}",
               color=["#9ca3af", "#2563eb", "#16a34a", "#7c3aed", "#e11d48"][j % 5])
    ax.set_xticks(x)
    ax.set_xticklabels(["Persistence\nM0", "Vol-scaled\nR1", "Mean-revert\nR2",
                        "Trend+vol\nR3", "Team-scale\nR4"], fontsize=8)
    ax.set_ylabel("MAE (future Elo delta)")
    ax.set_title("R-P1-01 — robustness: MAE vs Elo persistence (t+1..t+4)")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(title="horizon", fontsize=8)
    fig.tight_layout()
    emit(OUT, "R-P1-01_mae_vs_persistence", piv.reset_index(), fig,
         standard_md(
             "R-P1-01 MAE vs persistence",
             shows="Expanding-window pooled MAE predicting future Elo delta at "
                   "t+1..t+4 for persistence and the four transparent robustness "
                   "models (volatility-scaled, mean-reversion, trend+volatility, "
                   "team-specific change scale).",
             does_not_show="Any metric other than Elo-delta MAE; nothing "
                           "in-sample; no random splits.",
             supports="If any bar sits below persistence at the same horizon, that "
                      "model beats persistence on OOT MAE at that horizon.",
             weakens="Any model whose bars stay at/above persistence fails the "
                     "primary MAE criterion.",
             alternatives="Elo-decay against a team's longer baseline; "
                          "per-team shrunken means.",
             limitations="Robustness models only; features derived from "
                          "elo_change_1y (no future leakage)."))


def plot_delta_mae(cmp: pd.DataFrame) -> None:
    d = cmp[cmp.model != "P1-M0_persistence"].pivot_table(
        index="model", columns="horizon", values="delta_mae_vs_persistence")
    d = d.reindex(index=MODEL_NAMES[1:])
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    for j, col in enumerate(d.columns):
        ax.plot(d.index, d[col], marker="o", label=f"t+{col}",
                color=["#2563eb", "#16a34a", "#7c3aed", "#e11d48"][j % 4])
    ax.axhline(0, color="0.4", ls="--", lw=1)
    ax.set_ylabel("ΔMAE vs persistence (positive = improves)")
    ax.set_title("R-P1-02 — delta MAE vs persistence by horizon")
    ax.set_xticks(range(len(d)))
    ax.set_xticklabels(d.index.map({"P1-R1_vol_scaled": "R1 vol-scaled",
                                    "P1-R2_mean_reversion": "R2 mean-revert",
                                    "P1-R3_trend_vol": "R3 trend+vol",
                                    "P1-R4_team_scale": "R4 team-scale"}), fontsize=8)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    emit(OUT, "R-P1-02_delta_mae_by_horizon", d.reset_index(), fig,
         standard_md(
             "R-P1-02 delta MAE vs persistence",
             shows="Signed difference MAE(robustness) − MAE(persistence) per "
                   "horizon; positive means the robustness model is better.",
             does_not_show="RMSE or correlation (reported in the CSV).",
             supports="Positive deltas identify genuinely useful robustness models.",
             weakens="Values near zero mean the model merely matches persistence.",
             alternatives="Weighted scoring across horizons.",
             limitations="Same OLS machinery; tiny absolute gains should not be "
                         "over-interpreted at n≈9-10k."))


def plot_ovp(t, preds_store) -> None:
    tgt = "target_elo_delta_t1"
    preds = preds_store[f"{tgt}__P1-R3_trend_vol"]
    a = preds["actual"]
    p = preds["pred"]
    mask = np.isfinite(a) & np.isfinite(p)
    fig, ax = plt.subplots(figsize=(6.8, 6))
    ax.scatter(a[mask], p[mask], s=4, alpha=0.3)
    lim = [min(a[mask].min(), p[mask].min()) - 10,
           max(a[mask].max(), p[mask].max()) + 10]
    ax.plot(lim, lim, ls="--", color="0.4", lw=1)
    r = pearson(a[mask], p[mask])
    ax.set_title(f"R-P1-03 — actual vs predicted Elo delta (R3, t+1, r={r:.2f})")
    ax.set_xlabel("actual future Elo delta")
    ax.set_ylabel("predicted future Elo delta")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    g = preds[["test_time", "year", "nat_team_code", "actual", "pred"]].dropna(
        subset=["actual", "pred"])
    emit(OUT, "R-P1-03_actual_vs_predicted", g, fig,
         standard_md(
             "R-P1-03 actual vs predicted Elo delta",
             shows="Expanding-window actual vs predicted Elo delta for the best "
                   "trend+volatility model at t+1.",
             does_not_show="Future Elo level; multi-horizon detail.",
             supports="A positive (if modest) correlation between prediction and "
                      "actual change.",
             weakens="Wide scatterband — most variance is unpredictable.",
             alternatives="Per-team shrinkage; quantile targets.",
             limitations="OLS; t+1 only."))


def plot_germany(ger_df: pd.DataFrame) -> None:
    piv = ger_df.pivot_table(index="model", columns="horizon", values="mae_de")
    piv = piv.reindex(index=MODEL_NAMES)
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    x = np.arange(len(piv))
    width = 0.16
    for j, col in enumerate(piv.columns):
        ax.bar(x + (j - 1.5) * width, piv[col], width, label=f"t+{col}",
               color=["#9ca3af", "#2563eb", "#16a34a", "#7c3aed", "#e11d48"][j % 5])
    ax.set_xticks(x)
    ax.set_xticklabels(["Persistence\nM0", "Vol-scaled\nR1", "Mean-revert\nR2",
                        "Trend+vol\nR3", "Team-scale\nR4"], fontsize=8)
    ax.set_ylabel("Germany MAE (future Elo delta)")
    ax.set_title("R-P1-04 — Germany robustness comparison (MAE)")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(title="horizon", fontsize=8)
    fig.tight_layout()
    emit(OUT, "R-P1-04_germany_robustness_comparison", piv.reset_index(), fig,
         standard_md(
             "R-P1-04 Germany robustness comparison",
             shows="Germany-specific expanding-window MAE per model and horizon.",
             does_not_show="Why Germany declines (no causal claim anywhere).",
             supports="Any model improving Germany's MAE vs persistence would be a "
                      "Germany-specific robustness gain.",
             weakens="If all Germany bars sit at/above persistence, Germany gains "
                     "nothing from these robustness models.",
             alternatives="Germany-specific parameters (flagged as descriptive "
                          "only).",
             limitations="Single country, small n; only expanding-window OLS."))


if __name__ == "__main__":
    main()