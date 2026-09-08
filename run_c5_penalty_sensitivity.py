from __future__ import annotations

import argparse
import csv
import json
import math
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from tqdm import tqdm

import v2_runner
from c5_penalty_visualization import write_stage1_heatmaps, write_stage2_scatter
from run_physical_wpt_experiments import load_physical_wpt_cfg, physical_efficiency_values
from v2_runner import generate_common
from v3_runner import V3Sim


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results_c5_penalty_sensitivity"
SCALE_VALUES = (0.5, 1.0, 2.0)
STAGE1_SEEDS = tuple(range(1007, 1017))
STAGE2_SEEDS = tuple(range(2007, 2057))
C4_WEIGHTS = {"w1": 0.60, "w2": 0.10, "w3": 0.06, "w4": 0.04, "w5": 0.20}
DISTANCES = {1: 20, 2: 25, 3: 30, 4: 35, 5: 40}


@dataclass(frozen=True, slots=True)
class C5Parameters:
    lambda_soc: float
    lambda_task: float
    lambda_kpi: float


@dataclass(frozen=True, slots=True)
class C5PenaltyResult:
    lambda_soc: float
    lambda_task: float
    lambda_kpi: float
    effective_soc_shortage_coefficient: float
    effective_soc_risk_coefficient: float
    effective_task_scale: float
    effective_kpi_risk_coefficient: float
    mean_delay: float
    mean_delay_std: float
    urgent_on_time_rate: float
    urgent_on_time_std: float
    completion_rate: float
    wpt_loss_kwh: float
    fleet_min_soc: float
    critical_soc_event_count: int
    safety_violation_count: int
    mean_solver_time: float
    max_solver_time: float
    solver_calls: int
    infeasible_count: int
    simulation_failure_count: int


class NoSafeCandidateError(Exception):
    pass


def effective_coefficients(lambda_soc: float, lambda_task: float, lambda_kpi: float) -> dict[str, float]:
    return {
        "effective_soc_shortage_coefficient": 200.0 * lambda_soc,
        "effective_soc_risk_coefficient": 6.0 * lambda_soc,
        "effective_task_scale": lambda_task,
        "effective_kpi_risk_coefficient": 30.0 * lambda_kpi,
    }


def generate_parameter_combinations() -> list[C5Parameters]:
    return [C5Parameters(soc, task, kpi) for soc in SCALE_VALUES for task in SCALE_VALUES for kpi in SCALE_VALUES]


def _critical_soc_events(simulation: V3Sim) -> int:
    threshold = float(simulation.cfg["critical_soc"])
    events = 0
    for agv in simulation.agvs:
        previous = 1.0
        for _, soc in agv.trace:
            if soc <= threshold and previous > threshold:
                events += 1
            previous = soc
    return events


def _sample_std(values: list[float]) -> float:
    return float(np.std(values, ddof=1)) if len(values) > 1 else 0.0


def _run_combination(parameters: C5Parameters, seeds: tuple[int, ...]) -> C5PenaltyResult:
    v2_runner.eta_values = physical_efficiency_values
    delays: list[float] = []
    urgent_rates: list[float] = []
    completions: list[float] = []
    losses: list[float] = []
    fleet_min_soc: list[float] = []
    mean_solver_times: list[float] = []
    max_solver_times: list[float] = []
    critical_events = 0
    safety_violations = 0
    solver_calls = 0
    infeasible_count = 0
    for seed in seeds:
        cfg = load_physical_wpt_cfg()
        cfg.update({"n_agvs": 5, "n_pads": 1, "task_arrival_rate_per_h": 90, "wpt_power_kw": 3})
        cfg["weights"] = C4_WEIGHTS
        cfg["c5_lambda_soc"] = parameters.lambda_soc
        cfg["c5_lambda_task"] = parameters.lambda_task
        cfg["c5_lambda_kpi"] = parameters.lambda_kpi
        tasks, initial_soc = generate_common(cfg, seed, distances=DISTANCES, urgent_ratio=0.2)
        lookup = {task.task_id: index for index, task in enumerate(tasks)}
        simulation = V3Sim(
            cfg, "C5", seed, tasks, initial_soc, "v3_primary_challenge",
            variable_eta=True, task_index_lookup=lookup,
            predicted_eta_mode="variable", realized_eta_mode="variable",
        )
        metrics = simulation.run()
        delays.append(float(metrics["mean_delay"]))
        urgent_rates.append(float(metrics["urgent_on_time_rate"]))
        completions.append(float(metrics["completion_rate"]))
        losses.append(float(metrics["wpt_loss"]))
        fleet_min_soc.append(float(metrics["fleet_min_soc"]))
        mean_solver_times.append(float(metrics["solver_mean_time_s"]))
        max_solver_times.append(float(metrics["solver_max_time_s"]))
        critical_events += _critical_soc_events(simulation)
        safety_violations += int(metrics["low_soc_stops"])
        solver_calls += int(metrics["solver_calls"])
        infeasible_count += int(metrics["solver_infeasible_calls"])
    coefficients = effective_coefficients(parameters.lambda_soc, parameters.lambda_task, parameters.lambda_kpi)
    return C5PenaltyResult(
        lambda_soc=parameters.lambda_soc,
        lambda_task=parameters.lambda_task,
        lambda_kpi=parameters.lambda_kpi,
        **coefficients,
        mean_delay=float(np.mean(delays)),
        mean_delay_std=_sample_std(delays),
        urgent_on_time_rate=float(np.mean(urgent_rates)),
        urgent_on_time_std=_sample_std(urgent_rates),
        completion_rate=float(np.mean(completions)),
        wpt_loss_kwh=float(np.mean(losses)),
        fleet_min_soc=float(np.mean(fleet_min_soc)),
        critical_soc_event_count=critical_events,
        safety_violation_count=safety_violations,
        mean_solver_time=float(np.mean(mean_solver_times)),
        max_solver_time=float(np.max(max_solver_times)),
        solver_calls=solver_calls,
        infeasible_count=infeasible_count,
        simulation_failure_count=0,
    )


def is_safe(result: C5PenaltyResult) -> bool:
    return result.infeasible_count == 0 and result.simulation_failure_count == 0 and result.safety_violation_count == 0


def pareto_results(results: list[C5PenaltyResult]) -> list[C5PenaltyResult]:
    return [
        candidate for candidate in results
        if not any(
            other.mean_delay <= candidate.mean_delay
            and other.urgent_on_time_rate >= candidate.urgent_on_time_rate
            and (other.mean_delay < candidate.mean_delay or other.urgent_on_time_rate > candidate.urgent_on_time_rate)
            for other in results
        )
    ]


def _rank_key(result: C5PenaltyResult) -> tuple[float, float, float]:
    distance_from_baseline = abs(result.lambda_soc - 1.0) + abs(result.lambda_task - 1.0) + abs(result.lambda_kpi - 1.0)
    return result.mean_delay, -result.urgent_on_time_rate, distance_from_baseline


def select_stage2_candidates(results: list[C5PenaltyResult]) -> list[C5PenaltyResult]:
    safe = [result for result in results if is_safe(result)]
    eligible = [result for result in safe if result.critical_soc_event_count == 0] or safe
    frontier = sorted(pareto_results(eligible), key=_rank_key)
    remainder = sorted([result for result in eligible if result not in frontier], key=_rank_key)
    selected = (frontier + remainder)[:5]
    baseline = next(result for result in results if (result.lambda_soc, result.lambda_task, result.lambda_kpi) == (1.0, 1.0, 1.0))
    if baseline not in selected:
        selected = selected[:4] + [baseline]
    return sorted(selected, key=lambda result: (result.lambda_soc, result.lambda_task, result.lambda_kpi))


def select_final_result(results: list[C5PenaltyResult]) -> C5PenaltyResult:
    safe = [result for result in results if is_safe(result)]
    safe_frontier = sorted(pareto_results([result for result in safe if result.critical_soc_event_count == 0] or safe), key=_rank_key)
    if not safe_frontier:
        raise NoSafeCandidateError()
    baseline = next(result for result in results if (result.lambda_soc, result.lambda_task, result.lambda_kpi) == (1.0, 1.0, 1.0))
    if len(safe_frontier) == 1:
        return safe_frontier[0]
    delay_band = baseline.mean_delay_std / math.sqrt(len(STAGE2_SEEDS))
    urgent_band = baseline.urgent_on_time_std / math.sqrt(len(STAGE2_SEEDS))
    best_delay = min(result.mean_delay for result in safe_frontier)
    best_urgent = max(result.urgent_on_time_rate for result in safe_frontier)
    near_joint_best = [
        result for result in safe_frontier
        if result.mean_delay <= best_delay + delay_band and result.urgent_on_time_rate >= best_urgent - urgent_band
    ]
    return min(near_joint_best or safe_frontier, key=_rank_key)


def _write_csv(path: Path, results: list[C5PenaltyResult]) -> None:
    fieldnames = list(asdict(results[0])) if results else list(C5PenaltyResult.__dataclass_fields__)
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(asdict(result) for result in results)


def _run_stage(parameters: list[C5Parameters], seeds: tuple[int, ...], label: str, workers: int) -> list[C5PenaltyResult]:
    results: list[C5PenaltyResult] = []
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(_run_combination, parameter, seeds) for parameter in parameters]
        for future in tqdm(as_completed(futures), total=len(futures), desc=label):
            results.append(future.result())
    return sorted(results, key=lambda result: (result.lambda_soc, result.lambda_task, result.lambda_kpi))


def main(workers: int | None = None) -> None:
    parameters = generate_parameter_combinations()
    print(f"Generated C5 parameter combinations ({len(parameters)}):")
    for parameter in parameters:
        print(asdict(parameter), effective_coefficients(**asdict(parameter)))
    print("Baseline C5 coefficients:", effective_coefficients(1.0, 1.0, 1.0))
    print("Scale examples:")
    for example in ((0.5, 1.0, 2.0), (1.0, 1.0, 1.0), (2.0, 0.5, 0.5)):
        print(example, effective_coefficients(*example))
    print(f"Stage 1 expected simulation runs: {len(parameters) * len(STAGE1_SEEDS)}")
    OUT.mkdir(exist_ok=True)
    worker_count = workers or min(4, os.cpu_count() or 1)
    stage1 = _run_stage(parameters, STAGE1_SEEDS, "C5 Stage 1", worker_count)
    _write_csv(OUT / "c5_stage1_coarse.csv", stage1)
    _write_csv(OUT / "c5_stage1_pareto.csv", pareto_results([result for result in stage1 if is_safe(result)]))
    write_stage1_heatmaps([asdict(result) for result in stage1], OUT)
    finalists = select_stage2_candidates(stage1)
    print("Stage 2 finalists:", [asdict(result) | {"mean_delay": result.mean_delay, "urgent_on_time_rate": result.urgent_on_time_rate} for result in finalists])
    stage2 = _run_stage([C5Parameters(result.lambda_soc, result.lambda_task, result.lambda_kpi) for result in finalists], STAGE2_SEEDS, "C5 Stage 2", worker_count)
    _write_csv(OUT / "c5_stage2_finalists.csv", stage2)
    frontier_keys = {(result.lambda_soc, result.lambda_task, result.lambda_kpi) for result in pareto_results([result for result in stage2 if is_safe(result)])}
    write_stage2_scatter([asdict(result) for result in stage2], frontier_keys, OUT)
    selected = select_final_result(stage2)
    baseline = next(result for result in stage2 if (result.lambda_soc, result.lambda_task, result.lambda_kpi) == (1.0, 1.0, 1.0))
    selected_row = asdict(selected) | {
        "baseline_mean_delay": baseline.mean_delay,
        "baseline_urgent_on_time_rate": baseline.urgent_on_time_rate,
        "mean_delay_improvement_vs_baseline": baseline.mean_delay - selected.mean_delay,
        "urgent_on_time_rate_improvement_vs_baseline": selected.urgent_on_time_rate - baseline.urgent_on_time_rate,
    }
    with (OUT / "c5_selected_parameters.csv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=list(selected_row), lineterminator="\n")
        writer.writeheader()
        writer.writerow(selected_row)
    metadata = {"stage1_seeds": STAGE1_SEEDS, "stage2_seeds": STAGE2_SEEDS, "c4_weights_frozen": C4_WEIGHTS, "stage1_reps": 10, "stage2_reps": 50, "physical_wpt": "0-175 mm geometry-derived SS-FHA states"}
    (OUT / "c5_penalty_sensitivity_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print("Selected C5 parameters:", selected_row)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="C5 penalty coefficient sensitivity analysis")
    parser.add_argument("--workers", type=int, default=None)
    arguments = parser.parse_args()
    main(workers=arguments.workers)
