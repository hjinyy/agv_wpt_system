from __future__ import annotations

from typing import Literal, TypedDict, cast

import v2_runner
import v3_runner
from parameter_refinement_analysis import C4Parameters, C5Parameters, ReplicaMetrics
from run_physical_wpt_experiments import load_physical_wpt_cfg, physical_efficiency_values
from v2_runner import generate_common
from v3_runner import V3Sim


PRIMARY_DISTANCES = {1: 20, 2: 25, 3: 30, 4: 35, 5: 40}
C4_OLD = C4Parameters(0.60, 0.10, 0.06, 0.04, 0.20)


class SimulationConfig(TypedDict, total=False):
    weights: dict[str, float]
    c5_lambda_soc: float
    c5_lambda_task: float
    c5_lambda_kpi: float


def _configure(parameters: C4Parameters | C5Parameters) -> SimulationConfig:
    v2_runner.eta_values = physical_efficiency_values
    v3_runner.eta_values = physical_efficiency_values
    cfg = load_physical_wpt_cfg()
    cfg.update({"n_agvs": 5, "n_pads": 1, "task_arrival_rate_per_h": 90, "wpt_power_kw": 3})
    cfg["weights"] = C4_OLD.weights if isinstance(parameters, C5Parameters) else parameters.weights
    if isinstance(parameters, C5Parameters):
        cfg["c5_lambda_soc"] = parameters.lambda_soc
        cfg["c5_lambda_task"] = parameters.lambda_task
        cfg["c5_lambda_kpi"] = parameters.lambda_kpi
    return cast(SimulationConfig, cfg)


def _critical_soc_events(simulation: V3Sim) -> int:
    threshold = float(simulation.cfg["critical_soc"])
    events = 0
    for agv in simulation.agvs:
        previous_soc = 1.0
        for _, soc in agv.trace:
            if soc <= threshold and previous_soc > threshold:
                events += 1
            previous_soc = soc
    return events


def _run_replica(
    parameters: C4Parameters | C5Parameters,
    seed: int,
    strategy: Literal["C4", "C5"],
) -> ReplicaMetrics:
    cfg = _configure(parameters)
    tasks, initial_soc = generate_common(cfg, seed, distances=PRIMARY_DISTANCES, urgent_ratio=0.2)
    lookup = {task.task_id: index for index, task in enumerate(tasks)}
    simulation = V3Sim(
        cfg,
        strategy,
        seed,
        tasks,
        initial_soc,
        "v3_primary_challenge",
        variable_eta=True,
        task_index_lookup=lookup,
        predicted_eta_mode="variable",
        realized_eta_mode="variable",
    )
    metrics = simulation.run()
    return ReplicaMetrics(
        seed=seed,
        mean_delay=float(metrics["mean_delay"]),
        urgent_on_time_rate=float(metrics["urgent_on_time_rate"]),
        completion_rate=float(metrics["completion_rate"]),
        wpt_loss_kwh=float(metrics["wpt_loss"]),
        fleet_min_soc=float(metrics["fleet_min_soc"]),
        critical_soc_event_count=_critical_soc_events(simulation),
        safety_violation_count=int(metrics["low_soc_stops"]),
        mean_solver_time=float(metrics.get("solver_mean_time_s", 0.0)),
        max_solver_time=float(metrics.get("solver_max_time_s", 0.0)),
        solver_calls=int(metrics["solver_calls"]),
        infeasible_count=int(metrics.get("solver_infeasible_calls", 0)),
        simulation_failure_count=0,
    )


def run_c4_replications(parameters: C4Parameters, seeds: tuple[int, ...]) -> list[ReplicaMetrics]:
    return [_run_replica(parameters, seed, "C4") for seed in seeds]


def run_c5_replications(parameters: C5Parameters, seeds: tuple[int, ...]) -> list[ReplicaMetrics]:
    return [_run_replica(parameters, seed, "C5") for seed in seeds]
