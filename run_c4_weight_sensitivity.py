from __future__ import annotations

import argparse
import csv
import json
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

import v2_runner
import v3_runner
from run_physical_wpt_experiments import load_physical_wpt_cfg, physical_efficiency_values
from v2_runner import generate_common
from v3_runner import V3Sim


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results_c4_weight_sensitivity"
FIG_OUT = ROOT / "results_c4_weight_sensitivity_figures"
WEIGHT_VALUES = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6)
PRIMARY_DISTANCES = {1: 20, 2: 25, 3: 30, 4: 35, 5: 40}
CSV_FIELDS = (
    "w1", "w2", "w3", "w4", "w5", "mean_delay", "urgent_on_time_rate",
    "mean_delay_std", "urgent_on_time_std",
)


class WeightConfigurationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class WeightCombination:
    w1: float
    w2: float
    w3: float
    w4: float
    w5: float

    @property
    def weights(self) -> dict[str, float]:
        return {"w1": self.w1, "w2": self.w2, "w3": self.w3, "w4": self.w4, "w5": self.w5}


@dataclass(frozen=True, slots=True)
class SensitivityResult:
    w1: float
    w2: float
    w3: float
    w4: float
    w5: float
    mean_delay: float
    urgent_on_time_rate: float
    mean_delay_std: float
    urgent_on_time_std: float


def generate_weight_combinations() -> list[WeightCombination]:
    combinations: list[WeightCombination] = []
    for w1 in WEIGHT_VALUES:
        for w5 in WEIGHT_VALUES:
            if w1 + w5 > 0.8 + 1e-12:
                continue
            remaining = 1.0 - w1 - w5
            combination = WeightCombination(
                w1=w1,
                w2=remaining * 2.5 / 5.0,
                w3=remaining * 1.5 / 5.0,
                w4=remaining * 1.0 / 5.0,
                w5=w5,
            )
            if not np.isclose(sum(combination.weights.values()), 1.0):
                raise WeightConfigurationError(f"Weights do not sum to one: {combination}")
            combinations.append(combination)
    return combinations


def _run_combination(combination: WeightCombination, reps: int) -> SensitivityResult:
    v2_runner.eta_values = physical_efficiency_values
    v3_runner.eta_values = physical_efficiency_values
    cfg = load_physical_wpt_cfg()
    cfg.update({"n_agvs": 5, "n_pads": 1, "task_arrival_rate_per_h": 90, "wpt_power_kw": 3})
    cfg["weights"] = combination.weights
    delays: list[float] = []
    urgent_rates: list[float] = []
    for replication in range(reps):
        seed = int(cfg["seed0"]) + replication
        tasks, initial_soc = generate_common(cfg, seed, distances=PRIMARY_DISTANCES, urgent_ratio=0.2)
        lookup = {task.task_id: index for index, task in enumerate(tasks)}
        simulation = V3Sim(
            cfg, "C4", seed, tasks, initial_soc, "v3_primary_challenge",
            variable_eta=True, task_index_lookup=lookup,
            predicted_eta_mode="variable", realized_eta_mode="variable",
        )
        metrics = simulation.run()
        delays.append(float(metrics["mean_delay"]))
        urgent_rates.append(float(metrics["urgent_on_time_rate"]))
    return SensitivityResult(
        **combination.weights,
        mean_delay=float(np.mean(delays)),
        urgent_on_time_rate=float(np.mean(urgent_rates)),
        mean_delay_std=float(np.std(delays, ddof=1)) if reps > 1 else 0.0,
        urgent_on_time_std=float(np.std(urgent_rates, ddof=1)) if reps > 1 else 0.0,
    )


def pareto_results(results: list[SensitivityResult]) -> list[SensitivityResult]:
    return [
        candidate for candidate in results
        if not any(
            other.mean_delay <= candidate.mean_delay
            and other.urgent_on_time_rate >= candidate.urgent_on_time_rate
            and (other.mean_delay < candidate.mean_delay or other.urgent_on_time_rate > candidate.urgent_on_time_rate)
            for other in results
        )
    ]


def _write_csv(path: Path, results: list[SensitivityResult]) -> None:
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(asdict(result) for result in results)


def _heatmap(results: list[SensitivityResult], attribute: str, title: str, label: str, filename: str) -> None:
    axis_values = np.array(WEIGHT_VALUES)
    matrix = np.full((len(axis_values), len(axis_values)), np.nan)
    for result in results:
        row = int(np.where(np.isclose(axis_values, result.w5))[0][0])
        column = int(np.where(np.isclose(axis_values, result.w1))[0][0])
        matrix[row, column] = getattr(result, attribute)
    figure, axis = plt.subplots(figsize=(7.0, 5.8))
    image = axis.imshow(matrix, origin="lower", cmap="viridis", aspect="auto")
    axis.set_xticks(range(len(axis_values)), [f"{value:.1f}" for value in axis_values])
    axis.set_yticks(range(len(axis_values)), [f"{value:.1f}" for value in axis_values])
    axis.set_xlabel("w1: SOC deficit weight")
    axis.set_ylabel("w5: deadline-risk weight")
    axis.set_title(title)
    for row, w5 in enumerate(axis_values):
        for column, w1 in enumerate(axis_values):
            value = matrix[row, column]
            if not np.isnan(value):
                axis.text(column, row, f"{value:.2f}", ha="center", va="center", color="white", fontsize=8)
    colorbar = figure.colorbar(image, ax=axis)
    colorbar.set_label(label)
    figure.tight_layout()
    figure.savefig(FIG_OUT / f"{filename}.png", dpi=300, bbox_inches="tight")
    figure.savefig(FIG_OUT / f"{filename}.pdf", bbox_inches="tight")
    plt.close(figure)


def write_artifacts(results: list[SensitivityResult], reps: int) -> None:
    OUT.mkdir(exist_ok=True)
    FIG_OUT.mkdir(exist_ok=True)
    ordered = sorted(results, key=lambda result: (result.w1, result.w5))
    _write_csv(OUT / "sensitivity_results_c4.csv", ordered)
    _write_csv(OUT / "sensitivity_results_c4_pareto.csv", pareto_results(ordered))
    _heatmap(ordered, "mean_delay", "C4 weight sensitivity: mean task delay", "Mean task delay [min]", "Figure_C4_Weight_Sensitivity_Delay")
    _heatmap(ordered, "urgent_on_time_rate", "C4 weight sensitivity: urgent on-time rate", "Urgent on-time rate [%]", "Figure_C4_Weight_Sensitivity_Urgent_On_Time")
    metadata = {
        "strategy": "C4 only; C1-C5 logic and safety rules unchanged",
        "scenario": "v3_primary_challenge: 5 AGVs, 1 pad, 90 tasks/h, 3 kW, 20% urgent tasks",
        "reps": reps,
        "common_random_numbers": {"seeds": list(range(int(load_physical_wpt_cfg()["seed0"]), int(load_physical_wpt_cfg()["seed0"]) + reps))},
        "wpt_efficiency_source": "geometry-derived 0-175 mm lateral-misalignment SS-FHA states, uniformly sampled",
        "weight_allocation": "w2:w3:w4 = 2.5:1.5:1.0 after w1 and w5",
    }
    (OUT / "sensitivity_metadata_c4.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def main(reps: int = 50, workers: int | None = None) -> None:
    combinations = generate_weight_combinations()
    print(f"Valid C4 weight combinations: {len(combinations)}")
    print("First five combinations:")
    for combination in combinations[:5]:
        print(combination.weights)
    worker_count = workers or min(4, os.cpu_count() or 1)
    results: list[SensitivityResult] = []
    with ProcessPoolExecutor(max_workers=worker_count) as executor:
        futures = [executor.submit(_run_combination, combination, reps) for combination in combinations]
        for future in tqdm(as_completed(futures), total=len(futures), desc="C4 weight combinations"):
            results.append(future.result())
    write_artifacts(results, reps)
    print(f"Completed {len(results)} combinations x {reps} replications; outputs={OUT}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="C4 priority-weight sensitivity analysis")
    parser.add_argument("--reps", type=int, default=50)
    parser.add_argument("--workers", type=int, default=None)
    arguments = parser.parse_args()
    main(reps=arguments.reps, workers=arguments.workers)
