from __future__ import annotations

"""Strategy-independent charging-adequacy metrics consistent with the DES energy model."""

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from simulation.final_wpt import physical_efficiency_values
from v2_runner import generate_common, task_energy, task_time


@dataclass(frozen=True, slots=True)
class AdequacyResult:
    rho_analytical: float
    rho_simulation_based: float
    mean_task_energy_kwh: float
    analytical_demand_kw: float
    simulation_demand_kw: float
    charging_supply_kw: float
    mean_eta: float
    mean_task_distance_m: float
    logistics_utilization: float
    detour_energy_included: bool = False


def adequacy_for_scenario(configuration: dict, distances: dict[int, float], seeds: Iterable[int]) -> AdequacyResult:
    """Calculate demand-side rho without any strategy result or charging-detour energy.

    Task energy exactly follows DES ``task_energy``: round-trip travel plus service auxiliary
    energy. Charging-pad detour is excluded because it is a scheduling-dependent consequence,
    not an exogenous fleet task demand.
    """
    ordered_distances = np.array(list(distances.values()), dtype=float)
    mean_task_energy = float(np.mean([task_energy(configuration, float(distance)) for distance in ordered_distances]))
    mean_task_distance = float(ordered_distances.mean())
    eta_values = physical_efficiency_values(configuration)
    mean_eta = float(np.mean(eta_values))
    supply_kw = float(configuration["n_pads"] * configuration["wpt_power_kw"] * mean_eta)
    analytical_demand_kw = float(configuration["task_arrival_rate_per_h"] * mean_task_energy)

    generated_energy: list[float] = []
    generated_hours: list[float] = []
    for seed in seeds:
        tasks, _ = generate_common(configuration, int(seed), distances=distances, urgent_ratio=float(configuration["urgent_ratio"]))
        generated_energy.append(sum(task_energy(configuration, task.distance_m) for task in tasks))
        generated_hours.append(float(configuration["operation_hours"]))
    simulation_demand_kw = float(sum(generated_energy) / sum(generated_hours))
    service_h = task_time(configuration, mean_task_distance) / 3600.0
    logistics_utilization = float(configuration["task_arrival_rate_per_h"] * service_h / configuration["n_agvs"])
    return AdequacyResult(
        rho_analytical=analytical_demand_kw / supply_kw,
        rho_simulation_based=simulation_demand_kw / supply_kw,
        mean_task_energy_kwh=mean_task_energy,
        analytical_demand_kw=analytical_demand_kw,
        simulation_demand_kw=simulation_demand_kw,
        charging_supply_kw=supply_kw,
        mean_eta=mean_eta,
        mean_task_distance_m=mean_task_distance,
        logistics_utilization=logistics_utilization,
    )


def rho_region(rho: float) -> str:
    if rho < 0.7:
        return "non_binding"
    if rho < 0.9:
        return "near_transition"
    if rho < 1.0:
        return "transition"
    if rho < 1.3:
        return "moderately_constrained"
    return "strongly_constrained"
