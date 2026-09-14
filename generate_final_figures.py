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
        for metric in ("mean_delay", "urgent_on_time_rate", "completion_rate"):
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
    markdown += "Note. Values are mean ± two-sided 95% t confidence-interval half-width across n=50 independent replications (df=49; seeds 4007–4056). Task arrivals follow the Poisson process configured for each scenario. All strategies had zero actual low-SOC stops, infeasible MILP calls, and simulation failures.\n"
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
            latex_lines.append(
                f" & {row['Strategy']} & {row['Mean delay [min]'].replace(' ± ', r' $\pm$ ')} & {row['Urgent on-time [%]'].replace(' ± ', r' $\pm$ ')} & {row['Completion [%]'].replace(' ± ', r' $\pm$ ')} & {row['WPT loss [kWh]'].replace(' ± ', r' $\pm$ ')} \\\\")
    latex_lines.extend([
        "\\bottomrule",
        "\\end{tabular}",
        "\\vspace{2pt}",
        "\\begin{minipage}{0.98\\linewidth}\\footnotesize Task arrivals follow the scenario-specific Poisson process. CIs are two-sided t intervals (df=49). All strategies recorded zero actual low-SOC stops, infeasible MILP calls, and simulation failures.\\end{minipage}",
        "\\end{table*}",
    ])
    (OUT / "Table1_Final_Performance_95CI.tex").write_text("\n".join(latex_lines) + "\n", encoding="utf-8")


def _base_primary_figure(base: pd.DataFrame, primary: pd.DataFrame) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(12.0, 4.2))
    for axis, frame, title in ((axes[0], base, "Base Case"), (axes[1], primary, "Primary Challenge")):
        delay = _mean_ci(frame, "mean_delay")
        urgent = _mean_ci(frame, "urgent_on_time_rate")
        positions = np.arange(len(STRATEGIES))
        axis.bar(positions, delay["mean"], yerr=delay["ci95"], capsize=3, color=[COLORS[item] for item in STRATEGIES])
        axis.set_xticks(positions, STRATEGIES)
        axis.set_ylabel("Mean task delay [min]")
        axis.set_title(title)
        secondary = axis.twinx()
        secondary.errorbar(positions, urgent["mean"], yerr=urgent["ci95"], color="black", marker="o", capsize=3)
        secondary.set_ylabel("Urgent on-time completion [%]")
        secondary.grid(False)
    figure.suptitle("Final C1-C5 evaluation: Base Case and Primary Challenge (mean ± 95% CI, n=50)")
    figure.tight_layout()
    _save(figure, "Figure1_Final_Base_Primary")


def _tradeoff_figure(primary: pd.DataFrame) -> None:
    delay = _mean_ci(primary, "mean_delay").set_index("strategy")
    urgent = _mean_ci(primary, "urgent_on_time_rate").set_index("strategy")
    completion = _mean_ci(primary, "completion_rate").set_index("strategy")
    figure, axis = plt.subplots(figsize=(6.6, 4.8))
    sizes = 50 + 180 * (completion["mean"] - completion["mean"].min()) / max(1e-9, completion["mean"].max() - completion["mean"].min())
    for strategy in STRATEGIES:
        axis.errorbar(delay.loc[strategy, "mean"], urgent.loc[strategy, "mean"], xerr=delay.loc[strategy, "ci95"], yerr=urgent.loc[strategy, "ci95"], color=COLORS[strategy], capsize=3, linewidth=1.1, zorder=1)
        axis.scatter(delay.loc[strategy, "mean"], urgent.loc[strategy, "mean"], s=float(sizes[strategy]), color=COLORS[strategy], edgecolor="black", zorder=2)
        axis.annotate(strategy, (delay.loc[strategy, "mean"], urgent.loc[strategy, "mean"]), xytext=(5, 5), textcoords="offset points")
    axis.set_xlabel("Mean task delay [min]")
    axis.set_ylabel("Urgent on-time completion [%]")
    axis.set_title("Final Primary Challenge trade-off (mean ± 95% CI, n=50)")
    axis.grid(alpha=0.3)
    _save(figure, "Figure2_Final_Primary_Tradeoff")


def _c4_diagnostics_figure(primary: pd.DataFrame) -> None:
    c4 = primary[primary["strategy"] == "C4"]
    metrics = (
        ("Charging contention\nevents / replication", "charging_contention_events", "events"),
        ("C4 assignment differs\nfrom C3 [%]", "different_decision_rate_C4_vs_C3", "%"),
    )
    figure, axes = plt.subplots(1, 2, figsize=(9.0, 4.3))
    for axis, (label, column, unit) in zip(axes, metrics):
        mean, ci95 = _paired_mean_ci(c4[column])
        axis.bar([0], [mean], yerr=[ci95], capsize=5, color=COLORS["C4"], edgecolor="black")
        axis.set_xticks([0], [label])
        axis.set_ylabel(unit)
        axis.set_title(f"{mean:.1f} ± {ci95:.1f}")
        axis.grid(axis="y", alpha=0.25)
    figure.suptitle("Figure 3. C4 Priority Algorithm behavior verification (mean ± 95% CI, n=50)")
    figure.tight_layout()
    _save(figure, "Figure3_Final_C4_Priority_Diagnostics")


def _stress_figure(stress: pd.DataFrame) -> None:
    rows: list[dict[str, float]] = []
    for label, group in stress.groupby("scenario"):
        c3 = group[group["strategy"] == "C3"].set_index("replication")
        c4 = group[group["strategy"] == "C4"].set_index("replication")
        workload, pads, power = (int(value) for value in label.removeprefix("stress_w").replace("_p", " ").replace("_kw", " ").split())
        delay_mean, delay_ci = _paired_mean_ci(c3["mean_delay"] - c4["mean_delay"])
        urgent_mean, urgent_ci = _paired_mean_ci(c4["urgent_on_time_rate"] - c3["urgent_on_time_rate"])
        rows.append({"workload": workload, "pads": pads, "power": power, "delay_difference_min": delay_mean, "delay_ci95_min": delay_ci, "urgent_difference_pp": urgent_mean, "urgent_ci95_pp": urgent_ci})
    frame = pd.DataFrame(rows)
    maximum = max(1.0, float(frame["delay_difference_min"].abs().max()))
    figure, axes = plt.subplots(1, 3, figsize=(13.0, 4.0), sharey=True, layout="constrained")
    image = None
    for axis, power in zip(axes, (1, 3, 5)):
        subset = frame[frame["power"] == power]
        matrix = subset.pivot(index="pads", columns="workload", values="delay_difference_min").sort_index()
        delay_ci = subset.pivot(index="pads", columns="workload", values="delay_ci95_min").sort_index()
        urgent = subset.pivot(index="pads", columns="workload", values="urgent_difference_pp").sort_index()
        urgent_ci = subset.pivot(index="pads", columns="workload", values="urgent_ci95_pp").sort_index()
        image = axis.imshow(matrix.values, cmap="RdBu", norm=TwoSlopeNorm(vmin=-maximum, vcenter=0, vmax=maximum), aspect="auto")
        axis.set_xticks(range(len(matrix.columns)), [str(value) for value in matrix.columns])
        axis.set_yticks(range(len(matrix.index)), [str(value) for value in matrix.index])
        axis.set_xlabel("Workload [tasks/h]")
        axis.set_title(f"Power = {power} kW")
        for row in range(matrix.shape[0]):
            for column in range(matrix.shape[1]):
                axis.text(column, row, f"{matrix.iloc[row, column]:+.1f}±{delay_ci.iloc[row, column]:.1f}\n{urgent.iloc[row, column]:+.1f}±{urgent_ci.iloc[row, column]:.1f} pp", ha="center", va="center", fontsize=7)
    axes[0].set_ylabel("WPT pads")
    figure.colorbar(image, ax=axes, label="Paired C3 − C4 delay [min] (positive = C4 lower delay)")
    figure.suptitle("Final Stress Grid: C4 versus C3 (mean ± 95% CI, n=50)")
    _save(figure, "Figure4_Final_C4_vs_C3_Stress_Grid")


def main() -> None:
    FIGURES.mkdir(exist_ok=True)
    base = pd.read_csv(OUT / "base_case_results.csv")
    primary = pd.read_csv(OUT / "primary_challenge_results.csv")
    stress = pd.read_csv(OUT / "stress_grid_results.csv")
    _write_figure_statistics(base, primary, stress)
    _write_publication_table(base, primary)
    _base_primary_figure(base, primary)
    _tradeoff_figure(primary)
    _c4_diagnostics_figure(primary)
    _stress_figure(stress)


if __name__ == "__main__":
    main()
