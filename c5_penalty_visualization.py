from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


SCALE_VALUES = (0.5, 1.0, 2.0)


def write_stage1_heatmaps(results: list[Mapping[str, float]], output: Path) -> None:
    for lambda_soc in SCALE_VALUES:
        subset = [result for result in results if np.isclose(result["lambda_soc"], lambda_soc)]
        for attribute, title, unit in (("mean_delay", "Mean task delay", "min"), ("urgent_on_time_rate", "Urgent on-time rate", "%")):
            matrix = np.full((3, 3), np.nan)
            for result in subset:
                row = SCALE_VALUES.index(result["lambda_kpi"])
                column = SCALE_VALUES.index(result["lambda_task"])
                matrix[row, column] = result[attribute]
            figure, axis = plt.subplots(figsize=(6.2, 5.0))
            image = axis.imshow(matrix, origin="lower", cmap="viridis", aspect="auto")
            axis.set_xticks(range(3), [str(value) for value in SCALE_VALUES])
            axis.set_yticks(range(3), [str(value) for value in SCALE_VALUES])
            axis.set_xlabel("lambda_task")
            axis.set_ylabel("lambda_kpi")
            axis.set_title(f"C5 Stage 1 {title} (lambda_soc={lambda_soc})")
            for row in range(3):
                for column in range(3):
                    axis.text(column, row, f"{matrix[row, column]:.2f}", ha="center", va="center", color="white")
            figure.colorbar(image, ax=axis, label=unit)
            figure.tight_layout()
            figure.savefig(output / f"c5_stage1_lambda_soc_{lambda_soc}_{attribute}.png", dpi=300, bbox_inches="tight")
            plt.close(figure)


def write_stage2_scatter(results: list[Mapping[str, float]], pareto_keys: set[tuple[float, float, float]], output: Path) -> None:
    figure, axis = plt.subplots(figsize=(7.0, 5.2))
    for index, result in enumerate(results):
        key = (result["lambda_soc"], result["lambda_task"], result["lambda_kpi"])
        color = "#d62728" if key in pareto_keys else "#4c78a8"
        axis.scatter(result["mean_delay"], result["urgent_on_time_rate"], color=color, s=70)
        axis.annotate(f"({key[0]:g},{key[1]:g},{key[2]:g})", (result["mean_delay"], result["urgent_on_time_rate"]), xytext=(4, 4 + 12 * (index % 3)), textcoords="offset points", fontsize=8)
    axis.set_xlabel("Mean task delay [min]")
    axis.set_ylabel("Urgent on-time rate [%]")
    axis.set_title("C5 Stage 2 finalists (red: Pareto-optimal safety-feasible)")
    axis.grid(alpha=0.3)
    figure.tight_layout()
    figure.savefig(output / "c5_stage2_finalists_pareto.png", dpi=300, bbox_inches="tight")
    plt.close(figure)
