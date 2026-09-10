from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import assert_never

import numpy as np
from scipy import stats


@dataclass(frozen=True, slots=True)
class C4Parameters:
    w1: float
    w2: float
    w3: float
    w4: float
    w5: float

    @property
    def weights(self) -> dict[str, float]:
        return {"w1": self.w1, "w2": self.w2, "w3": self.w3, "w4": self.w4, "w5": self.w5}


@dataclass(frozen=True, slots=True)
class C5Parameters:
    lambda_soc: float
    lambda_task: float
    lambda_kpi: float


@dataclass(frozen=True, slots=True)
class ReplicaMetrics:
    seed: int
    mean_delay: float
    urgent_on_time_rate: float
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


@dataclass(frozen=True, slots=True)
class Aggregate:
    parameters: C4Parameters | C5Parameters
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


@dataclass(frozen=True, slots=True)
class PairedStatistics:
    comparison: str
    metric: str
    mean_difference: float
    median_difference: float
    standard_error: float
    ci95_low: float
    ci95_high: float
    bootstrap_ci95_low: float
    bootstrap_ci95_high: float
    improved_replication_rate: float
    paired_replications: int


class ParameterFamilyMismatchError(Exception):
    pass


def c4_parameters(w1: float, w5: float) -> C4Parameters:
    remaining = 1.0 - w1 - w5
    return C4Parameters(
        round(w1, 10),
        round(remaining * 0.5, 10),
        round(remaining * 0.3, 10),
        round(remaining * 0.2, 10),
        round(w5, 10),
    )


def c4_local_parameters() -> list[C4Parameters]:
    parameters = [c4_parameters(w1, w5) for w1 in (0.50, 0.55, 0.60, 0.65, 0.70) for w5 in (0.10, 0.15, 0.20, 0.25, 0.30) if w1 + w5 <= 0.90 + 1e-12]
    return parameters


def c4_adaptive_parameters() -> list[C4Parameters]:
    return [c4_parameters(w1, w5) for w1 in (0.75, 0.80) for w5 in (0.10, 0.15, 0.20, 0.25, 0.30) if w1 + w5 <= 0.90 + 1e-12]


def c5_common_parameters(alphas: tuple[float, ...]) -> list[C5Parameters]:
    return [C5Parameters(alpha, alpha, alpha) for alpha in alphas]


def c5_oat_parameters(alpha: float) -> list[C5Parameters]:
    values = tuple(value for value in (alpha - 0.5, alpha, alpha + 0.5) if value > 0.0)
    parameters = {C5Parameters(value, alpha, alpha) for value in values}
    parameters |= {C5Parameters(alpha, value, alpha) for value in values}
    parameters |= {C5Parameters(alpha, alpha, value) for value in values}
    return sorted(parameters, key=lambda item: (item.lambda_soc, item.lambda_task, item.lambda_kpi))


def aggregate(parameters: C4Parameters | C5Parameters, rows: list[ReplicaMetrics]) -> Aggregate:
    delays = np.array([row.mean_delay for row in rows], dtype=float)
    urgent = np.array([row.urgent_on_time_rate for row in rows], dtype=float)
    return Aggregate(
        parameters, float(delays.mean()), float(delays.std(ddof=1)), float(urgent.mean()), float(urgent.std(ddof=1)),
        float(np.mean([row.completion_rate for row in rows])), float(np.mean([row.wpt_loss_kwh for row in rows])),
        float(np.mean([row.fleet_min_soc for row in rows])), sum(row.critical_soc_event_count for row in rows),
        sum(row.safety_violation_count for row in rows), float(np.mean([row.mean_solver_time for row in rows])),
        float(np.max([row.max_solver_time for row in rows])), sum(row.solver_calls for row in rows),
        sum(row.infeasible_count for row in rows), sum(row.simulation_failure_count for row in rows),
    )


def is_safe(result: Aggregate) -> bool:
    return result.infeasible_count == 0 and result.simulation_failure_count == 0 and result.safety_violation_count == 0


def pareto(results: list[Aggregate]) -> list[Aggregate]:
    return [candidate for candidate in results if not any(other.mean_delay <= candidate.mean_delay and other.urgent_on_time_rate >= candidate.urgent_on_time_rate and (other.mean_delay < candidate.mean_delay or other.urgent_on_time_rate > candidate.urgent_on_time_rate) for other in results)]


def is_joint_kpi_leader(candidate: Aggregate, results: list[Aggregate]) -> bool:
    return is_safe(candidate) and candidate.mean_delay <= min(result.mean_delay for result in results if is_safe(result)) and candidate.urgent_on_time_rate >= max(result.urgent_on_time_rate for result in results if is_safe(result))


def choose_refined(results: list[Aggregate], reference: C4Parameters | C5Parameters) -> Aggregate:
    safe_frontier = pareto([result for result in results if is_safe(result)])
    if len(safe_frontier) == 1:
        return safe_frontier[0]
    reference_result = next(result for result in safe_frontier if result.parameters == reference) if any(result.parameters == reference for result in safe_frontier) else None
    if reference_result is not None:
        near = [result for result in safe_frontier if result.mean_delay <= reference_result.mean_delay + reference_result.mean_delay_std / sqrt(50) and result.urgent_on_time_rate >= reference_result.urgent_on_time_rate - reference_result.urgent_on_time_std / sqrt(50)]
        if near:
            return min(near, key=lambda result: (parameter_distance(result.parameters, reference), result.mean_delay, -result.urgent_on_time_rate))
    return min(safe_frontier, key=lambda result: (result.mean_delay, -result.urgent_on_time_rate, parameter_distance(result.parameters, reference)))


def parameter_distance(parameters: C4Parameters | C5Parameters, reference: C4Parameters | C5Parameters) -> float:
    match parameters, reference:
        case C4Parameters(w1=a1, w2=a2, w3=a3, w4=a4, w5=a5), C4Parameters(w1=b1, w2=b2, w3=b3, w4=b4, w5=b5):
            return abs(a1 - b1) + abs(a2 - b2) + abs(a3 - b3) + abs(a4 - b4) + abs(a5 - b5)
        case C5Parameters(lambda_soc=a1, lambda_task=a2, lambda_kpi=a3), C5Parameters(lambda_soc=b1, lambda_task=b2, lambda_kpi=b3):
            return abs(a1 - b1) + abs(a2 - b2) + abs(a3 - b3)
        case _:
            assert_never(parameters)
            raise ParameterFamilyMismatchError("Parameter families must match.")


def paired_statistics(comparison: str, metric: str, new: list[ReplicaMetrics], old: list[ReplicaMetrics]) -> PairedStatistics:
    old_by_seed = {row.seed: row for row in old}
    differences = np.array([getattr(row, metric) - getattr(old_by_seed[row.seed], metric) for row in new if row.seed in old_by_seed], dtype=float)
    count = len(differences)
    standard_error = float(differences.std(ddof=1) / sqrt(count))
    critical = float(stats.t.ppf(0.975, count - 1))
    bootstrap = np.random.default_rng(9031).choice(differences, size=(5000, count), replace=True).mean(axis=1)
    improved = differences < 0 if metric == "mean_delay" else differences > 0
    return PairedStatistics(comparison, metric, float(differences.mean()), float(np.median(differences)), standard_error, float(differences.mean() - critical * standard_error), float(differences.mean() + critical * standard_error), float(np.quantile(bootstrap, 0.025)), float(np.quantile(bootstrap, 0.975)), float(improved.mean() * 100.0), count)
