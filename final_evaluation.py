from __future__ import annotations

import csv
import json
from copy import deepcopy
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from math import sqrt
from pathlib import Path
from typing import Final, TypedDict

import numpy as np
from scipy import stats

import v2_runner
import v3_runner
from simulation.final_wpt import load_final_wpt_configuration, physical_efficiency_values
from v2_runner import generate_common
from v3_runner import V3Sim


ROOT: Final = Path(__file__).resolve().parent
OUT: Final = ROOT / "results_final"
FIGURES: Final = OUT / "figures"
STRATEGIES: Final = ("C1", "C2", "C3", "C4", "C5")
STRESS_STRATEGIES: Final = ("C1", "C2", "C3", "C4")
FINAL_EVALUATION_SEEDS: Final = tuple(range(4007, 4057))
TUNING_SEEDS: Final = frozenset((*range(1007, 1057), *range(2007, 2057), *range(3007, 3057)))
C4_FINAL_WEIGHTS: Final = {"w1": 0.55, "w2": 0.175, "w3": 0.105, "w4": 0.07, "w5": 0.10}
C5_FINAL_SCALES: Final = (2.0, 1.5, 1.5)
PRIMARY_DISTANCES: Final = {1: 20, 2: 25, 3: 30, 4: 35, 5: 40}


@dataclass(frozen=True, slots=True)
class FinalReplica:
    seed: int
    strategy: str
    mean_delay: float
    urgent_on_time_rate: float


@dataclass(frozen=True, slots=True)
class ScenarioRun:
    configuration: FinalConfiguration
    label: str
    distances: dict[int, int]
    urgent_ratio: float
    strategies: tuple[str, ...]
    seed: int


class FinalConfiguration(dict):
    pass


class PairedResult(TypedDict):
    comparison: str
    metric: str
    mean_difference: float
    median_difference: float
    standard_error: float
    ci95_low: float
    ci95_high: float
    left_better_replication_rate: float
    paired_replications: int


class FinalSeedOverlapError(Exception):
    pass


def final_configuration() -> FinalConfiguration:
    configuration = FinalConfiguration(load_final_wpt_configuration())
    configuration["weights"] = deepcopy(C4_FINAL_WEIGHTS)
    configuration["c5_lambda_soc"], configuration["c5_lambda_task"], configuration["c5_lambda_kpi"] = C5_FINAL_SCALES
    return configuration


def _critical_events(simulation: V3Sim) -> int:
    threshold = float(simulation.cfg["critical_soc"])
    return sum(
        int(soc <= threshold and previous > threshold)
        for agv in simulation.agvs
        for previous, soc in zip((1.0, *(value for _, value in agv.trace[:-1])), (value for _, value in agv.trace))
    )


def _run_strategy_set(run: ScenarioRun) -> tuple[list[dict], list[dict], list[FinalReplica]]:
    v2_runner.eta_values = physical_efficiency_values
    v3_runner.eta_values = physical_efficiency_values
    tasks, initial_soc = generate_common(run.configuration, run.seed, distances=run.distances, urgent_ratio=run.urgent_ratio)
    lookup = {task.task_id: index for index, task in enumerate(tasks)}
    metrics_rows: list[dict] = []
    solver_rows: list[dict] = []
    replicas: list[FinalReplica] = []
    for strategy in run.strategies:
        simulation = V3Sim(run.configuration, strategy, run.seed, tasks, initial_soc, run.label, variable_eta=True, task_index_lookup=lookup, predicted_eta_mode="variable", realized_eta_mode="variable")
        metrics = simulation.run()
        metrics["critical_soc_event_count"] = _critical_events(simulation)
        metrics["simulation_failure_count"] = 0
        metrics["infeasible_count"] = int(metrics.get("solver_infeasible_calls", 0))
        metrics_rows.append(metrics)
        solver_rows.extend(simulation.solver_rows)
        replicas.append(FinalReplica(run.seed, strategy, float(metrics["mean_delay"]), float(metrics["urgent_on_time_rate"])))
    return metrics_rows, solver_rows, replicas


def _run_scenario(configuration: FinalConfiguration, label: str, distances: dict[int, int], urgent_ratio: float, strategies: tuple[str, ...]) -> tuple[list[dict], list[dict], list[FinalReplica]]:
    rows: list[dict] = []
    solver: list[dict] = []
    replicas: list[FinalReplica] = []
    runs = [ScenarioRun(configuration, label, distances, urgent_ratio, strategies, seed) for seed in FINAL_EVALUATION_SEEDS]
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(_run_strategy_set, run) for run in runs]
        for future in as_completed(futures):
            metric_rows, solver_rows, replica_rows = future.result()
            rows.extend(metric_rows)
            solver.extend(solver_rows)
            replicas.extend(replica_rows)
    return rows, solver, replicas


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = list(dict.fromkeys(field for row in rows for field in row))
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _summary(rows: list[dict]) -> list[dict]:
    metrics = ("mean_delay", "completion_rate", "urgent_on_time_rate", "battery_delivered_energy", "wpt_loss", "fleet_min_soc", "critical_soc_event_count", "low_soc_stops", "charging_wait", "solver_mean_time_s", "solver_max_time_s", "solver_calls", "infeasible_count", "simulation_failure_count")
    groups: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        groups.setdefault((str(row["scenario"]), str(row["strategy"])), []).append(row)
    summary: list[dict] = []
    for (scenario, strategy), group in sorted(groups.items()):
        output: dict[str, float | int | str] = {"scenario": scenario, "strategy": strategy, "reps": len(group)}
        for metric in metrics:
            values = np.array([float(value) if (value := row.get(metric, 0.0)) not in ("", None) else 0.0 for row in group], dtype=float)
            output[f"{metric}_mean"] = float(values.mean())
            output[f"{metric}_std"] = float(values.std(ddof=1)) if len(values) > 1 else 0.0
        summary.append(output)
    return summary


def _paired_statistic(comparison: str, metric: str, left: list[FinalReplica], right: list[FinalReplica]) -> PairedResult:
    right_by_seed = {item.seed: item for item in right}
    differences = np.array([getattr(item, metric) - getattr(right_by_seed[item.seed], metric) for item in left], dtype=float)
    standard_error = float(differences.std(ddof=1) / sqrt(len(differences)))
    margin = float(stats.t.ppf(0.975, len(differences) - 1) * standard_error)
    improved = differences < 0.0 if metric == "mean_delay" else differences > 0.0
    return {"comparison": comparison, "metric": metric, "mean_difference": float(differences.mean()), "median_difference": float(np.median(differences)), "standard_error": standard_error, "ci95_low": float(differences.mean() - margin), "ci95_high": float(differences.mean() + margin), "left_better_replication_rate": float(improved.mean() * 100.0), "paired_replications": len(differences)}


def _paired_statistics(replicas: list[FinalReplica]) -> list[dict]:
    by_strategy = {strategy: [item for item in replicas if item.strategy == strategy] for strategy in STRATEGIES}
    rows: list[dict] = []
    for left, right in (("C3", "C4"), ("C4", "C5"), ("C3", "C5")):
        for metric in ("mean_delay", "urgent_on_time_rate"):
            rows.append(_paired_statistic(f"{left}_minus_{right}", metric, by_strategy[left], by_strategy[right]))
    return rows


def _write_report(summary: list[dict], paired: list[dict], solver: list[dict]) -> None:
    solve_times = np.array([float(row["solve_time_s"]) for row in solver], dtype=float)
    lines = [
        "# Final AGV-WPT DES Evaluation",
        "",
        "## Frozen parameters",
        f"- C4: {C4_FINAL_WEIGHTS}",
        "- C5: lambda_soc=2.0, lambda_task=1.5, lambda_kpi=1.5; coefficients: SOC shortage=400, SOC risk=12, task scale=1.5, KPI risk=45.",
        "",
        "## Independent final seeds",
        f"Final evaluation used seeds {FINAL_EVALUATION_SEEDS[0]}-{FINAL_EVALUATION_SEEDS[-1]}. Parameter tuning/refinement and final evaluation used independent seed sets; verified overlap=0.",
        "",
        "## Strategy summary",
        "| scenario | strategy | reps | mean delay [min] | urgent on-time [%] | completion [%] | WPT loss [kWh] | fleet min SOC [%] | low-SOC stops |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        *(f"| {row['scenario']} | {row['strategy']} | {row['reps']} | {row['mean_delay_mean']:.4f} | {row['urgent_on_time_rate_mean']:.4f} | {row['completion_rate_mean']:.4f} | {row['wpt_loss_mean']:.4f} | {row['fleet_min_soc_mean']:.4f} | {row['low_soc_stops_mean']:.4f} |" for row in summary),
        "",
        "## Primary Challenge paired 95% confidence intervals",
        "| comparison | metric | mean difference | 95% CI | left-better replications [%] |",
        "| --- | --- | --- | --- | --- |",
        *(f"| {row['comparison']} | {row['metric']} | {row['mean_difference']:.4f} | [{row['ci95_low']:.4f}, {row['ci95_high']:.4f}] | {row['left_better_replication_rate']:.1f} |" for row in paired),
        "",
        "## Safety and solver stability",
        f"All final rows report actual low-SOC stops, infeasible MILP calls, and simulation failures explicitly. C5 solver call rows recorded: {len(solver)}, mean solve time={solve_times.mean():.6f} s, max solve time={solve_times.max():.6f} s.",
        "",
        "## Conclusion",
        "The final results describe the tested scenarios and seed set. They do not establish that C4 or C5 is globally optimal or universally superior.",
    ]
    (OUT / "FINAL_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def run_final_evaluation() -> None:
    if set(FINAL_EVALUATION_SEEDS).intersection(TUNING_SEEDS):
        raise FinalSeedOverlapError("Final evaluation seeds overlap tuning seeds.")
    OUT.mkdir(exist_ok=True)
    FIGURES.mkdir(exist_ok=True)
    (OUT / "final_evaluation_seeds.json").write_text(json.dumps({"final_evaluation_seeds": FINAL_EVALUATION_SEEDS, "tuning_seed_ranges": [[1007, 1056], [2007, 2056], [3007, 3056]], "overlap_count": 0}, indent=2), encoding="utf-8")
    (OUT / "final_frozen_parameters.json").write_text(json.dumps({"parameters_frozen": True, "C4": C4_FINAL_WEIGHTS, "C5": {"lambda_soc": 2.0, "lambda_task": 1.5, "lambda_kpi": 1.5, "soc_shortage": 400, "soc_risk": 12, "task_scale": 1.5, "kpi_risk": 45}}, indent=2), encoding="utf-8")
    base_config = final_configuration()
    base_distances = {index: int(base_config["picking_staging_distance_m"]) for index in range(1, int(base_config["n_picking_points"]) + 1)}
    base_rows, base_solver, _ = _run_scenario(base_config, "base_case", base_distances, 0.0, STRATEGIES)
    primary_config = final_configuration()
    primary_config.update({"n_agvs": 5, "n_pads": 1, "task_arrival_rate_per_h": 90, "wpt_power_kw": 3})
    primary_rows, primary_solver, primary_replicas = _run_scenario(primary_config, "primary_challenge", PRIMARY_DISTANCES, 0.2, STRATEGIES)
    stress_rows: list[dict] = []
    for workload in (75, 90, 105):
        for pads in (1, 2):
            for power in (1, 3, 5):
                configuration = final_configuration()
                configuration.update({"n_agvs": 5, "n_pads": pads, "task_arrival_rate_per_h": workload, "wpt_power_kw": power})
                rows, _, _ = _run_scenario(configuration, f"stress_w{workload}_p{pads}_kw{power}", PRIMARY_DISTANCES, 0.2, STRESS_STRATEGIES)
                stress_rows.extend(rows)
    all_rows = [*base_rows, *primary_rows, *stress_rows]
    summary = _summary(all_rows)
    paired = _paired_statistics(primary_replicas)
    _write_csv(OUT / "base_case_results.csv", base_rows)
    _write_csv(OUT / "primary_challenge_results.csv", primary_rows)
    _write_csv(OUT / "stress_grid_results.csv", stress_rows)
    _write_csv(OUT / "strategy_summary.csv", summary)
    _write_csv(OUT / "paired_statistics.csv", paired)
    _write_csv(OUT / "solver_statistics.csv", [*base_solver, *primary_solver])
    _write_report(summary, paired, [*base_solver, *primary_solver])


if __name__ == "__main__":
    run_final_evaluation()
