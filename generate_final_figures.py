from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd  # noqa: PANDAS_OK
from matplotlib.colors import TwoSlopeNorm


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results_final"
FIGURES = OUT / "figures"
STRATEGIES = ("C1", "C2", "C3", "C4", "C5")
COLORS = {"C1": "#6c757d", "C2": "#4c78a8", "C3": "#59a14f", "C4": "#e15759", "C5": "#7b3294"}
T_95_DF49 = 2.0096
TABLE_METRICS = (
    ("Mean delay [min]", "mean_delay"),
    ("Urgent on-time [%]", "urgent_on_time_rate"),
    ("Completion [%]", "completion_rate"),
    ("WPT loss [kWh]", "wpt_loss"),
)


def _is_urgent_on_time_applicable(scenario: str) -> bool:
    return scenario != "Base Case"


def _save(figure: plt.Figure, name: str) -> None:
    figure.savefig(FIGURES / f"{name}.png", dpi=300, bbox_inches="tight")
    figure.savefig(FIGURES / f"{name}.pdf", bbox_inches="tight")
    plt.close(figure)


def _mean_ci(frame: pd.DataFrame, metric: str) -> pd.DataFrame:
    grouped = frame.groupby("strategy")[metric].agg(["mean", "std", "count"]).reindex(STRATEGIES)
    grouped["ci95"] = T_95_DF49 * grouped["std"] / np.sqrt(grouped["count"])
    return grouped.reset_index()


def _paired_mean_ci(values: pd.Series) -> tuple[float, float]:
    return float(values.mean()), float(T_95_DF49 * values.std(ddof=1) / np.sqrt(values.count()))


def _write_figure_statistics(base: pd.DataFrame, primary: pd.DataFrame, stress: pd.DataFrame) -> None:
    rows: list[pd.DataFrame] = []
    for scenario, frame in (("Base Case", base), ("Primary Challenge", primary)):
        metrics = ["mean_delay", "completion_rate"]
        if _is_urgent_on_time_applicable(scenario):
            metrics.insert(1, "urgent_on_time_rate")
        for metric in metrics:
            table = _mean_ci(frame, metric)
            table.insert(0, "scenario", scenario)
            table.insert(2, "metric", metric)
            rows.append(table)

    for scenario, group in stress.groupby("scenario"):
        c3 = group[group["strategy"] == "C3"].set_index("replication")
        c4 = group[group["strategy"] == "C4"].set_index("replication")
        for metric, values in (
            ("paired_C3_minus_C4_delay_min", c3["mean_delay"] - c4["mean_delay"]),
            ("paired_C4_minus_C3_urgent_pp", c4["urgent_on_time_rate"] - c3["urgent_on_time_rate"]),
        ):
            mean, ci95 = _paired_mean_ci(values)
            rows.append(pd.DataFrame({"scenario": [scenario], "strategy": ["C4_vs_C3"], "metric": [metric], "mean": [mean], "std": [values.std(ddof=1)], "count": [values.count()], "ci95": [ci95]}))

    pd.concat(rows, ignore_index=True).to_csv(OUT / "figure_statistics.csv", index=False)


def _write_publication_table(base: pd.DataFrame, primary: pd.DataFrame) -> None:
    rows: list[dict[str, object]] = []
    for scenario, frame in (("Base Case", base), ("Primary Challenge", primary)):
        metric_tables = {label: _mean_ci(frame, column).set_index("strategy") for label, column in TABLE_METRICS}
        for strategy in STRATEGIES:
            row: dict[str, object] = {"Scenario": scenario, "Strategy": strategy, "n": 50}
            for label, _ in TABLE_METRICS:
                table = metric_tables[label]
                if label == "Urgent on-time [%]" and not _is_urgent_on_time_applicable(scenario):
                    row[f"{label} mean"] = np.nan
                    row[f"{label} std"] = np.nan
                    row[f"{label} CI95 half-width"] = np.nan
                    row[label] = "N/A"
                else:
                    row[f"{label} mean"] = float(table.loc[strategy, "mean"])
                    row[f"{label} std"] = float(table.loc[strategy, "std"])
                    row[f"{label} CI95 half-width"] = float(table.loc[strategy, "ci95"])
                    row[label] = f"{table.loc[strategy, 'mean']:.2f} ± {table.loc[strategy, 'ci95']:.2f}"
            rows.append(row)

    table = pd.DataFrame(rows)
    table.to_csv(OUT / "Table1_Final_Performance_95CI.csv", index=False)
    display = table[["Scenario", "Strategy", "n", *(label for label, _ in TABLE_METRICS)]]
    headers = list(display.columns)
    markdown_rows = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    markdown_rows.extend("| " + " | ".join(str(row[column]) for column in headers) + " |" for _, row in display.iterrows())
    markdown = "# Table 1. Final DES performance under stochastic task arrivals\n\n" + "\n".join(markdown_rows) + "\n\n"
    markdown += "Note. Values are mean ± two-sided 95% t confidence-interval half-width across n=50 independent replications (df=49; seeds 4007–4056). Base Case uses an urgent-task ratio of 0, so urgent on-time completion is not applicable. Task arrivals follow the Poisson process configured for each scenario. All strategies had zero actual low-SOC stops, infeasible MILP calls, and simulation failures.\n"
    (OUT / "Table1_Final_Performance_95CI.md").write_text(markdown, encoding="utf-8")

    latex_lines = [
        "\\begin{table*}[t]",
        "\\centering",
        "\\caption{Final DES performance under stochastic task arrivals (mean $\\pm$ 95\\% CI; $n=50$).}",
        "\\label{tab:final-performance}",
        "\\small",
        "\\begin{tabular}{llrrrr}",
        "\\toprule",
        "Scenario & Strategy & Delay [min] & Urgent on-time [\\%] & Completion [\\%] & WPT loss [kWh] \\\\",
        "\\midrule",
    ]
    for scenario in ("Base Case", "Primary Challenge"):
        scenario_rows = display[display["Scenario"] == scenario]
        latex_lines.append(f"\\multicolumn{{6}}{{l}}{{\\textit{{{scenario}}}}} \\\\")
        for _, row in scenario_rows.iterrows():
            delay = row["Mean delay [min]"].replace(" ± ", " $\\pm$ ")
            urgent = row["Urgent on-time [%]"].replace(" ± ", " $\\pm$ ")
            completion = row["Completion [%]"].replace(" ± ", " $\\pm$ ")
            loss = row["WPT loss [kWh]"].replace(" ± ", " $\\pm$ ")
            latex_lines.append(f" & {row['Strategy']} & {delay} & {urgent} & {completion} & {loss} \\\\")
    latex_lines.extend([
        "\\bottomrule",
        "\\end{tabular}",
        "\\vspace{2pt}",
        "\\begin{minipage}{0.98\\linewidth}\\footnotesize Base Case uses an urgent-task ratio of 0; urgent on-time completion is therefore not applicable. Task arrivals follow the scenario-specific Poisson process. CIs are two-sided t intervals (df=49). All strategies recorded zero actual low-SOC stops, infeasible MILP calls, and simulation failures.\\end{minipage}",
        "\\end{table*}",
    ])
    (OUT / "Table1_Final_Performance_95CI.tex").write_text("\n".join(latex_lines) + "\n", encoding="utf-8")


def _base_primary_figure(base: pd.DataFrame, primary: pd.DataFrame) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(12.0, 4.2))
    positions = np.arange(len(STRATEGIES))
    base_summary = base.groupby("strategy")["mean_delay"].mean().reindex(STRATEGIES)
    axes[0].bar(positions, base_summary, color=[COLORS[item] for item in STRATEGIES])
    axes[0].set_xticks(positions, STRATEGIES)
    axes[0].set_ylabel("Mean task delay [min]")
    axes[0].set_title("Base Case (urgent on-time: N/A; urgent ratio = 0)")

    primary_summary = primary.groupby("strategy")[["mean_delay", "urgent_on_time_rate"]].mean().reindex(STRATEGIES)
    axes[1].bar(positions, primary_summary["mean_delay"], color=[COLORS[item] for item in STRATEGIES])
    axes[1].set_xticks(positions, STRATEGIES)
    axes[1].set_ylabel("Mean task delay [min]")
    axes[1].set_title("Primary Challenge")
    primary_secondary = axes[1].twinx()
    primary_secondary.plot(positions, primary_summary["urgent_on_time_rate"], color="black", marker="o")
    primary_secondary.set_ylabel("Urgent on-time completion [%]")
    primary_secondary.grid(False)
    figure.suptitle("Figure 1. Base Case and Primary Challenge performance comparison")
    figure.tight_layout()
    _save(figure, "Figure1_Final_Base_Primary")


def _tradeoff_figure(primary: pd.DataFrame) -> None:
    summary = primary.groupby("strategy")[["mean_delay", "urgent_on_time_rate", "completion_rate"]].mean().reindex(STRATEGIES)
    figure, axis = plt.subplots(figsize=(6.6, 4.8))
    sizes = 50 + 180 * (summary["completion_rate"] - summary["completion_rate"].min()) / max(1e-9, summary["completion_rate"].max() - summary["completion_rate"].min())
    for strategy in STRATEGIES:
        axis.scatter(summary.loc[strategy, "mean_delay"], summary.loc[strategy, "urgent_on_time_rate"], s=float(sizes[strategy]), color=COLORS[strategy], edgecolor="black")
        axis.annotate(strategy, (summary.loc[strategy, "mean_delay"], summary.loc[strategy, "urgent_on_time_rate"]), xytext=(5, 5), textcoords="offset points")
    axis.set_xlabel("Mean task delay [min]")
    axis.set_ylabel("Urgent on-time completion [%]")
    axis.set_title("Figure 2. Primary Challenge strategy trade-off")
    axis.grid(alpha=0.3)
    _save(figure, "Figure2_Final_Primary_Tradeoff")


def _c4_diagnostics_figure(diagnostics: pd.DataFrame) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(11.2, 4.1))
    left = diagnostics[["charging_contention_events", "different_decision_rate_C4_vs_C3"]].mean()
    left_axis = axes[0]
    right_axis = left_axis.twinx()
    left_axis.bar([0], [left["charging_contention_events"]], color="#9ecae1", edgecolor="black", width=0.52)
    right_axis.bar([1], [left["different_decision_rate_C4_vs_C3"]], color="#f4a261", edgecolor="black", width=0.52)
    left_axis.set_xticks([0, 1], ["Contention events\nper replication", "C4 differs\nfrom C3 [%]"])
    left_axis.set_ylabel("Contention events")
    right_axis.set_ylabel("Different-decision rate [%]")
    left_axis.set_title("(a) Contention decision diagnostics")
    feature_columns = ("one_minus_soc", "E_next", "T_idle", "eta_WPT", "D")
    feature_names = ("1-SOC", "E_next", "T_idle", "eta_WPT", "D")
    axes[1].bar(feature_names, [diagnostics[f"{column}_std"].mean() for column in feature_columns], color="#bdbdbd", edgecolor="black")
    axes[1].set_ylabel("Mean within-replication feature std. [normalized]")
    axes[1].set_title("(b) C4 candidate-feature variation")
    figure.suptitle("Figure 3. C4 Priority Algorithm behavior verification")
    figure.tight_layout()
    _save(figure, "Figure3_Final_C4_Priority_Diagnostics")


def _stress_figure(stress: pd.DataFrame) -> None:
    rows: list[dict[str, float]] = []
    for label, group in stress.groupby("scenario"):
        c3 = group[group["strategy"] == "C3"]
        c4 = group[group["strategy"] == "C4"]
        workload, pads, power = (int(value) for value in label.removeprefix("stress_w").replace("_p", " ").replace("_kw", " ").split())
        rows.append({"workload": workload, "pads": pads, "power": power, "delay_improvement_pct": (c3["mean_delay"].mean() - c4["mean_delay"].mean()) / abs(c3["mean_delay"].mean()) * 100.0, "urgent_difference_pp": c4["urgent_on_time_rate"].mean() - c3["urgent_on_time_rate"].mean()})
    frame = pd.DataFrame(rows)
    maximum = max(1.0, float(frame["delay_improvement_pct"].abs().max()))
    figure, axes = plt.subplots(1, 3, figsize=(13.0, 4.0), sharey=True, layout="constrained")
    image = None
    for axis, power in zip(axes, (1, 3, 5)):
        subset = frame[frame["power"] == power]
        matrix = subset.pivot(index="pads", columns="workload", values="delay_improvement_pct").sort_index()
        urgent = subset.pivot(index="pads", columns="workload", values="urgent_difference_pp").sort_index()
        image = axis.imshow(matrix.values, cmap="RdBu", norm=TwoSlopeNorm(vmin=-maximum, vcenter=0, vmax=maximum), aspect="auto")
        axis.set_xticks(range(len(matrix.columns)), [str(value) for value in matrix.columns])
        axis.set_yticks(range(len(matrix.index)), [str(value) for value in matrix.index])
        axis.set_xlabel("Workload [tasks/h]")
        axis.set_title(f"Power = {power} kW")
        for row in range(matrix.shape[0]):
            for column in range(matrix.shape[1]):
                axis.text(column, row, f"{matrix.iloc[row, column]:+.1f}%\n({urgent.iloc[row, column]:+.1f} pp)", ha="center", va="center", fontsize=8)
    axes[0].set_ylabel("WPT pads")
    figure.colorbar(image, ax=axes, label="C4 vs C3 delay improvement [%]")
    figure.suptitle("Figure 4. C4 versus C3 Stress Grid")
    _save(figure, "Figure4_Final_C4_vs_C3_Stress_Grid")


def _c5_ablation_figure(ablation: pd.DataFrame) -> None:
    variants = ("Full objective", "No SOC term", "No task term", "No KPI-risk term")
    summary = ablation.groupby("variant")[["mean_delay", "urgent_on_time_rate"]].mean().reindex(variants)
    colors = [COLORS["C5"], "#8da0cb", "#fc8d62", "#66c2a5"]
    figure, axes = plt.subplots(1, 2, figsize=(10.0, 4.3))
    positions = np.arange(len(variants))
    axes[0].bar(positions, summary["mean_delay"], color=colors, edgecolor="black")
    axes[0].set_ylabel("Mean task delay [min]")
    axes[0].set_title("(a) Task delay")
    axes[1].bar(positions, summary["urgent_on_time_rate"], color=colors, edgecolor="black")
    axes[1].set_ylabel("Urgent on-time completion [%]")
    axes[1].set_title("(b) Urgent-task service")
    for axis in axes:
        axis.set_xticks(positions, ["Full", "No SOC", "No task", "No KPI-risk"], rotation=15)
        axis.grid(axis="y", alpha=0.25)
    figure.suptitle("Figure 5. C5 Objective Ablation Analysis")
    figure.tight_layout()
    _save(figure, "Figure5_Final_C5_Objective_Ablation")


def _uncertainty_figure(primary: pd.DataFrame) -> None:
    """Show the complete 50-replication delay distribution, not only its mean/CI."""
    required = {"strategy", "replication", "mean_delay"}
    if not required.issubset(primary.columns):
        raise ValueError(f"Figure 6 requires columns {sorted(required)}")
    counts = primary.groupby("strategy")["replication"].nunique().reindex(STRATEGIES)
    if not (counts == 50).all():
        raise ValueError(f"Figure 6 requires exactly 50 replications per strategy: {counts.to_dict()}")

    plot_data = primary[["strategy", "replication", "mean_delay"]].copy()
    plot_data.to_csv(FIGURES / "Figure6_Final_Replication_Uncertainty_data.csv", index=False)

    figure, axis = plt.subplots(figsize=(8.4, 5.0))
    values = [plot_data.loc[plot_data["strategy"] == strategy, "mean_delay"].to_numpy() for strategy in STRATEGIES]
    box = axis.boxplot(
        values,
        tick_labels=STRATEGIES,
        patch_artist=True,
        widths=0.58,
        medianprops={"color": "black", "linewidth": 1.8},
        whiskerprops={"color": "#444444", "linewidth": 1.1},
        capprops={"color": "#444444", "linewidth": 1.1},
        flierprops={"marker": "o", "markersize": 4.2, "markerfacecolor": "none", "markeredgecolor": "#333333", "alpha": 0.85},
    )
    for patch, strategy in zip(box["boxes"], STRATEGIES):
        patch.set_facecolor(COLORS[strategy])
        patch.set_alpha(0.76)
        patch.set_edgecolor("#333333")
        patch.set_linewidth(1.0)

    rng = np.random.default_rng(4056)
    for position, strategy, observations in zip(range(1, len(STRATEGIES) + 1), STRATEGIES, values):
        jitter = rng.uniform(-0.11, 0.11, len(observations))
        axis.scatter(position + jitter, observations, s=12, color=COLORS[strategy], alpha=0.25, edgecolor="none", zorder=2)

    axis.set_ylabel("Replication-level mean task delay [min]")
    axis.set_title("Figure 6. Primary Challenge delay distribution across 50 replications")
    axis.grid(axis="y", alpha=0.25)
    figure.text(
        0.5,
        0.01,
        "Box: interquartile range; center line: median; whiskers: 1.5×IQR; open circles: outliers; translucent points: individual replications.",
        ha="center",
        fontsize=8.5,
        color="#333333",
    )
    figure.tight_layout(rect=(0, 0.06, 1, 1))
    _save(figure, "Figure6_Final_Replication_Uncertainty")


def main() -> None:
    FIGURES.mkdir(exist_ok=True)
    base = pd.read_csv(OUT / "base_case_results.csv")
    primary = pd.read_csv(OUT / "primary_challenge_results.csv")
    stress = pd.read_csv(OUT / "stress_grid_results.csv")
    c4_diagnostics = pd.read_csv(OUT / "c4_priority_diagnostics.csv")
    c5_ablation = pd.read_csv(OUT / "c5_objective_ablation.csv")
    _write_figure_statistics(base, primary, stress)
    _write_publication_table(base, primary)
    _base_primary_figure(base, primary)
    _tradeoff_figure(primary)
    _c4_diagnostics_figure(c4_diagnostics)
    _stress_figure(stress)
    _c5_ablation_figure(c5_ablation)
    _uncertainty_figure(primary)


if __name__ == "__main__":
    main()
