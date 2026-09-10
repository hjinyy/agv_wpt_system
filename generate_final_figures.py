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


def _save(figure: plt.Figure, name: str) -> None:
    figure.savefig(FIGURES / f"{name}.png", dpi=300, bbox_inches="tight")
    figure.savefig(FIGURES / f"{name}.pdf", bbox_inches="tight")
    plt.close(figure)


def _mean_ci(frame: pd.DataFrame, metric: str) -> pd.DataFrame:
    grouped = frame.groupby("strategy")[metric].agg(["mean", "std", "count"]).reindex(STRATEGIES)
    grouped["ci95"] = 1.96 * grouped["std"] / np.sqrt(grouped["count"])
    return grouped.reset_index()


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
    figure.suptitle("Final C1-C5 evaluation: Base Case and Primary Challenge")
    figure.tight_layout()
    _save(figure, "Figure1_Final_Base_Primary")


def _tradeoff_figure(primary: pd.DataFrame) -> None:
    summary = primary.groupby("strategy")[["mean_delay", "urgent_on_time_rate", "completion_rate", "wpt_loss"]].mean().reindex(STRATEGIES)
    figure, axis = plt.subplots(figsize=(6.6, 4.8))
    sizes = 50 + 180 * (summary["completion_rate"] - summary["completion_rate"].min()) / max(1e-9, summary["completion_rate"].max() - summary["completion_rate"].min())
    for strategy, row in summary.iterrows():
        axis.scatter(row["mean_delay"], row["urgent_on_time_rate"], s=float(sizes[strategy]), color=COLORS[strategy], edgecolor="black")
        axis.annotate(strategy, (row["mean_delay"], row["urgent_on_time_rate"]), xytext=(5, 5), textcoords="offset points")
    axis.set_xlabel("Mean task delay [min]")
    axis.set_ylabel("Urgent on-time completion [%]")
    axis.set_title("Final Primary Challenge trade-off")
    axis.grid(alpha=0.3)
    _save(figure, "Figure2_Final_Primary_Tradeoff")


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
    figure.suptitle("Final Stress Grid: C4 versus C3")
    _save(figure, "Figure3_Final_Stress_Grid")


def main() -> None:
    FIGURES.mkdir(exist_ok=True)
    base = pd.read_csv(OUT / "base_case_results.csv")
    primary = pd.read_csv(OUT / "primary_challenge_results.csv")
    stress = pd.read_csv(OUT / "stress_grid_results.csv")
    _base_primary_figure(base, primary)
    _tradeoff_figure(primary)
    _stress_figure(stress)


if __name__ == "__main__":
    main()
