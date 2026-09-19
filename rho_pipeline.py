from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final
import time

import numpy as np
import yaml

from simulation.final_wpt import load_final_wpt_configuration
from simulation.charging_adequacy import adequacy_for_scenario, rho_region
from v2_runner import task_energy, task_time
from v3_runner import V3Sim

ROOT: Final = Path(__file__).resolve().parent
CONFIG_PATH: Final = ROOT / "config" / "rho_redesign.yaml"
FEATURES: Final = ("soc", "next_task_energy", "idle", "deadline")


@dataclass(frozen=True, slots=True)
class Scenario:
    name: str
    role: str
    n_agvs: int
    n_pads: int
    task_arrival_rate_per_h: float
    wpt_power_kw: float
    distances_m: tuple[float, ...]
    urgent_ratio: float

    @property
    def distances(self) -> dict[int, float]:
        return {index + 1: value for index, value in enumerate(self.distances_m)}


def load_experiment_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def tuning_seeds(data: dict | None = None) -> tuple[int, ...]:
    data = load_experiment_config() if data is None else data
    seeds = data["seeds"]
    return tuple(range(int(seeds["tuning_start"]), int(seeds["tuning_end"]) + 1))


def scenarios(data: dict | None = None) -> dict[str, Scenario]:
    data = load_experiment_config() if data is None else data
    return {
        name: Scenario(name=name, role=str(raw["role"]), n_agvs=int(raw["n_agvs"]), n_pads=int(raw["n_pads"]),
                       task_arrival_rate_per_h=float(raw["task_arrival_rate_per_h"]), wpt_power_kw=float(raw["wpt_power_kw"]),
                       distances_m=tuple(float(value) for value in raw["distances_m"]), urgent_ratio=float(raw["urgent_ratio"]))
        for name, raw in data["scenarios"].items()
    }


def configuration_for(scenario: Scenario, weights: dict[str, float]) -> dict:
    configuration = dict(load_final_wpt_configuration())
    configuration.update({
        "n_agvs": scenario.n_agvs, "n_pads": scenario.n_pads,
        "task_arrival_rate_per_h": scenario.task_arrival_rate_per_h,
        "wpt_power_kw": scenario.wpt_power_kw, "urgent_ratio": scenario.urgent_ratio,
        "c4_four_feature_weights": deepcopy(weights),
    })
    return configuration


class FourFeatureC4Sim(V3Sim):
    """C4 with fleet/logistics features only; WPT eta remains in SOC and loss physics."""

    def four_features(self, agv, t: float, next_task) -> dict[str, float]:
        energy = task_energy(self.cfg, next_task.distance_m)
        duration = task_time(self.cfg, next_task.distance_m)
        quantum = self.cfg["opportunity_quantum_s"]
        detour = 2 * self.cfg["zone_pad_distance_m"] / self.cfg["agv_speed_mps"]
        expected_wait = self.cfg.get("_expected_contention_wait_s", 0.0)
        projected = max(t + detour + quantum + expected_wait, next_task.arrival) + duration
        delay = max(0.0, projected - next_task.deadline)
        idle = max(0.0, t - agv.last_job_end)
        f_soc = float(np.clip((self.cfg["max_soc"] - agv.soc) / (self.cfg["max_soc"] - self.cfg["min_soc"]), 0, 1))
        emin, emax = task_energy(self.cfg, min(self.current_distances)), task_energy(self.cfg, max(self.current_distances))
        f_energy = 0.0 if emax <= emin else float(np.clip((energy - emin) / (emax - emin), 0, 1))
        f_idle = float(np.clip(idle / 1800.0, 0, 1))
        f_deadline = float(np.clip(delay / 600.0, 0, 1))
        weights = self.cfg["c4_four_feature_weights"]
        score = weights["soc"] * f_soc + weights["next_task_energy"] * f_energy + weights["idle"] * f_idle - weights["deadline"] * f_deadline
        return {"f_SOC": f_soc, "f_E": f_energy, "f_idle": f_idle, "f_D": f_deadline, "score": score,
                "raw_E_next_kwh": energy, "raw_D_s": delay, "raw_idle_s": idle}

    def features(self, agv, t: float, next_task, eta: float | None = None) -> dict[str, float]:
        """Compatibility hook: diagnostics and scheduling both use the same four-feature score."""
        return self.four_features(agv, t, next_task)

    def __init__(self, *args, current_distances: tuple[float, ...], **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.current_distances = current_distances
        self._priority_latencies_s: list[float] = []

    def metrics(self):
        metrics = super().metrics()
        latencies = np.asarray(self._priority_latencies_s, dtype=float)
        metrics["priority_decisions"] = int(len(latencies))
        metrics["total_priority_computation_time_s"] = float(latencies.sum())
        metrics["mean_decision_latency_ms"] = float(latencies.mean() * 1000.0) if len(latencies) else 0.0
        metrics["p95_decision_latency_ms"] = float(np.quantile(latencies, 0.95) * 1000.0) if len(latencies) else 0.0
        metrics["max_decision_latency_ms"] = float(latencies.max() * 1000.0) if len(latencies) else 0.0
        return metrics

    def choose(self, cands, t, next_task, avail_pads):
        """Instrument C4 priority selection without changing ranking or selected actions."""
        tic = time.perf_counter()
        try:
            return self._choose_four_feature(cands, t, next_task, avail_pads)
        finally:
            if self.strategy == "C4":
                self._priority_latencies_s.append(time.perf_counter() - tic)

    def _choose_four_feature(self, cands, t, next_task, avail_pads):
        if self.strategy != "C4":
            return super().choose(cands, t, next_task, avail_pads)
        preview = self.preview_task_map(cands, t, next_task)
        def agv_task(agv): return preview.get(agv.agv_id, next_task)
        def slack(agv):
            task = agv_task(agv)
            return task.deadline - (t + task_time(self.cfg, task.distance_m))
        critical = [agv for agv in cands if agv.soc <= self.cfg["critical_soc"]]
        if critical:
            return sorted(critical, key=lambda agv: (agv.soc, slack(agv), agv.agv_id))[:avail_pads], "critical"
        scored = []
        for agv in cands:
            task = agv_task(agv)
            row = self.four_features(agv, t, task)
            row.update({"scenario": self.label, "strategy": "C4", "replication": self.seed, "agv_id": agv.agv_id,
                        "task_id": task.task_id, "preview_rank_task": task.task_id})
            self.feature_rows.append(row)
            scored.append((row["score"], agv))
        return [agv for _, agv in sorted(scored, key=lambda item: (-item[0], item[1].agv_id))[:avail_pads]], "C4-4feature"


def scenario_catalog_rows(data: dict | None = None) -> list[dict[str, object]]:
    data = load_experiment_config() if data is None else data
    seeds = tuning_seeds(data)
    rows: list[dict[str, object]] = []
    for scenario in scenarios(data).values():
        config = configuration_for(scenario, {feature: 0.25 for feature in FEATURES})
        adequacy = adequacy_for_scenario(config, scenario.distances, seeds)
        rows.append({"scenario": scenario.name, "role": scenario.role, "n_agvs": scenario.n_agvs, "n_pads": scenario.n_pads,
                     "task_arrival_rate_per_h": scenario.task_arrival_rate_per_h, "wpt_power_kw": scenario.wpt_power_kw,
                     "distances_m": "|".join(str(int(value)) for value in scenario.distances_m), "urgent_ratio": scenario.urgent_ratio,
                     **asdict(adequacy), "rho_region": rho_region(adequacy.rho_analytical)})
    return rows
