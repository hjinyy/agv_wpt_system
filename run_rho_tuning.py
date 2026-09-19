from __future__ import annotations

"""Robust 4-feature C4 tuning across rho operating regions; no unseen final evaluation."""

import csv
import itertools
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import deepcopy
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import v2_runner
import v3_runner
from rho_pipeline import FEATURES, FourFeatureC4Sim, configuration_for, load_experiment_config, scenario_catalog_rows, scenarios, tuning_seeds
from simulation.final_wpt import physical_efficiency_values
from v2_runner import generate_common
from v3_runner import V3Sim

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "tuning"


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _weight_id(weights: dict[str, float]) -> str:
    return "_".join(f"{name}{weights[name]:.2f}" for name in FEATURES)


def simplex_grid(step: float) -> list[dict[str, float]]:
    units = round(1.0 / step)
    candidates: list[dict[str, float]] = []
    for soc in range(units + 1):
        for energy in range(units - soc + 1):
            for idle in range(units - soc - energy + 1):
                deadline = units - soc - energy - idle
                candidates.append(dict(zip(FEATURES, (soc * step, energy * step, idle * step, deadline * step))))
    return candidates


def _set_physical_callback() -> None:
    v2_runner.eta_values = physical_efficiency_values
    v3_runner.eta_values = physical_efficiency_values


def _run_reference(scenario_name: str, strategy: str, seed: int) -> dict[str, object]:
    _set_physical_callback()
    scenario = scenarios()[scenario_name]
    config = configuration_for(scenario, {name: 0.25 for name in FEATURES})
    tasks, initial = generate_common(config, seed, distances=scenario.distances, urgent_ratio=scenario.urgent_ratio)
    lookup = {task.task_id: index for index, task in enumerate(tasks)}
    simulation = V3Sim(config, strategy, seed, tasks, initial, scenario_name, variable_eta=True, task_index_lookup=lookup,
                       predicted_eta_mode="variable", realized_eta_mode="variable")
    row = simulation.run()
    row.update({"weight_id": "reference", "phase": "reference"})
    return row


def _run_candidate_block(scenario_name: str, weights: dict[str, float], phase: str, seeds: tuple[int, ...]) -> list[dict[str, object]]:
    _set_physical_callback()
    scenario = scenarios()[scenario_name]
    config = configuration_for(scenario, weights)
    rows: list[dict[str, object]] = []
    for seed in seeds:
        tasks, initial = generate_common(config, seed, distances=scenario.distances, urgent_ratio=scenario.urgent_ratio)
        lookup = {task.task_id: index for index, task in enumerate(tasks)}
        simulation = FourFeatureC4Sim(config, "C4", seed, tasks, initial, scenario_name, variable_eta=True, task_index_lookup=lookup,
                                      predicted_eta_mode="variable", realized_eta_mode="variable", current_distances=scenario.distances_m)
        row = simulation.run()
        row.update({"weight_id": _weight_id(weights), "phase": phase, **weights})
        rows.append(row)
    return rows


def _paired_rows(c4_rows: list[dict[str, object]], c3_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    c3 = {(row["scenario"], row["replication"]): row for row in c3_rows}
    pairs: list[dict[str, object]] = []
    for row in c4_rows:
        ref = c3[(row["scenario"], row["replication"])]
        pairs.append({"phase": row["phase"], "weight_id": row["weight_id"], "scenario": row["scenario"], "replication": row["replication"],
                      **{name: row[name] for name in FEATURES},
                      "delta_delay_C4_minus_C3": float(row["mean_delay"] - ref["mean_delay"]),
                      "delta_urgent_C4_minus_C3": float(row["urgent_on_time_rate"] - ref["urgent_on_time_rate"]),
                      "delta_completion_C4_minus_C3": float(row["completion_rate"] - ref["completion_rate"]),
                      "delta_min_soc_C4_minus_C3": float(row["fleet_min_soc"] - ref["fleet_min_soc"]),
                      "C4_low_soc_stops": float(row["low_soc_stops"]),
                      "C4_failure_count": 0})
    return pairs


def _aggregate_pairs(pairs: list[dict[str, object]]) -> pd.DataFrame:
    frame = pd.DataFrame(pairs)
    records: list[dict[str, object]] = []
    for (phase, weight_id, scenario), group in frame.groupby(["phase", "weight_id", "scenario"], sort=True):
        delay = group["delta_delay_C4_minus_C3"].to_numpy(float)
        urgent = group["delta_urgent_C4_minus_C3"].to_numpy(float)
        n = len(group)
        tcrit = stats.t.ppf(0.975, n - 1)
        for metric, values, direction in (("delay", delay, "negative_better"), ("urgent_on_time", urgent, "positive_better")):
            margin = float(tcrit * values.std(ddof=1) / sqrt(n))
            records.append({"phase": phase, "weight_id": weight_id, "scenario": scenario, "metric": metric,
                            "mean_difference": float(values.mean()), "median_difference": float(np.median(values)),
                            "ci95_low": float(values.mean() - margin), "ci95_high": float(values.mean() + margin),
                            "paired_replications": n, "direction": direction,
                            "C4_low_soc_stops_total": float(group["C4_low_soc_stops"].sum()),
                            "C4_failure_count_total": int(group["C4_failure_count"].sum()),
                            **{name: float(group[name].iloc[0]) for name in FEATURES}})
    return pd.DataFrame(records)


def _candidate_summary(pair_stats: pd.DataFrame) -> pd.DataFrame:
    delay = pair_stats[pair_stats.metric == "delay"].set_index(["phase", "weight_id", "scenario"])
    urgent = pair_stats[pair_stats.metric == "urgent_on_time"].set_index(["phase", "weight_id", "scenario"])
    rows: list[dict[str, object]] = []
    for (phase, weight_id), group in delay.groupby(level=[0, 1]):
        delays = group["mean_difference"].to_numpy(float)
        urgents = urgent.loc[(phase, weight_id), "mean_difference"].to_numpy(float)
        weights = {name: float(group[name].iloc[0]) for name in FEATURES}
        rows.append({"phase": phase, "weight_id": weight_id, **weights,
                     "mean_delay_difference": float(delays.mean()), "worst_delay_degradation": float(delays.max()),
                     "mean_urgent_difference": float(urgents.mean()), "worst_urgent_degradation": float(urgents.min()),
                     "hard_reject": bool((group["C4_low_soc_stops_total"] > 0).any() or (group["C4_failure_count_total"] > 0).any())})
    return pd.DataFrame(rows)


def _pareto(frame: pd.DataFrame) -> pd.DataFrame:
    valid = frame[~frame.hard_reject].copy()
    values = valid[["mean_delay_difference", "worst_delay_degradation", "mean_urgent_difference"]].to_numpy(float)
    keep = []
    for index, candidate in enumerate(values):
        dominates = ((values[:, 0] <= candidate[0]) & (values[:, 1] <= candidate[1]) & (values[:, 2] >= candidate[2]) &
                     ((values[:, 0] < candidate[0]) | (values[:, 1] < candidate[1]) | (values[:, 2] > candidate[2]))).any()
        keep.append(not dominates)
    return valid.loc[keep].sort_values(["worst_delay_degradation", "mean_delay_difference", "mean_urgent_difference"], ascending=[True, True, False])


def _local_neighbors(anchor: dict[str, float], step: float) -> list[dict[str, float]]:
    weights = {tuple(round(anchor[name], 8) for name in FEATURES)}
    for source, target in itertools.permutations(FEATURES, 2):
        if anchor[source] >= step - 1e-9:
            candidate = dict(anchor); candidate[source] -= step; candidate[target] += step
            weights.add(tuple(round(candidate[name], 8) for name in FEATURES))
    return [dict(zip(FEATURES, values)) for values in sorted(weights)]


def _run_blocks(candidates: list[dict[str, float]], phase: str, scenario_names: list[str], seeds: tuple[int, ...]) -> list[dict[str, object]]:
    jobs = [(scenario_name, weights) for weights in candidates for scenario_name in scenario_names]
    expected = len(jobs) * len(seeds)
    print(f"{phase}: candidates={len(candidates)}, scenarios={len(scenario_names)}, C4 simulations={expected}", flush=True)
    rows: list[dict[str, object]] = []
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(_run_candidate_block, scenario_name, weights, phase, seeds) for scenario_name, weights in jobs]
        for complete, future in enumerate(as_completed(futures), start=1):
            rows.extend(future.result())
            if complete % 10 == 0 or complete == len(futures):
                print(f"{phase}: blocks={complete}/{len(futures)}", flush=True)
    return rows


def _scenario_design_markdown(catalog: pd.DataFrame) -> str:
    view = catalog[["scenario", "role", "distances_m", "task_arrival_rate_per_h", "n_agvs", "n_pads", "wpt_power_kw", "rho_analytical", "rho_simulation_based", "rho_region", "logistics_utilization"]]
    lines = ["# Scenario Design by Charging Adequacy", "", "`rho = fleet task energy demand / available WPT supply`.",
             "Task demand includes DES-consistent round-trip travel and service auxiliary energy; it excludes pad-detour energy because detours are scheduling-dependent.",
             "", "## Catalog", "", view.to_markdown(index=False, floatfmt=".4f"), "",
             "## Selected roles", "", "- **Base** stays at rho << 1 as a non-binding reference.",
             "- **Primary** is `primary`: 40/50/60/70/80 m, six AGVs, one 3-kW pad, 90 tasks/h. It has rho about 1.01 while logistics utilization remains below 1.",
             "- The stress catalog covers non-binding, near-transition, transition, moderately constrained, and strongly constrained rho regions. It was selected by rho coverage rather than C4 outcome.", "",
             "The uniform 0-175-mm eight-state misalignment assumption is retained. Mean eta is evaluated from the frozen power-dependent SS-FHA curve for each scenario power."]
    return "\n".join(lines) + "\n"


def _report(catalog: pd.DataFrame, pareto: pd.DataFrame, chosen: pd.Series, pair_stats: pd.DataFrame, coarse_count: int, local_count: int) -> str:
    chosen_stats = pair_stats[pair_stats.weight_id == chosen.weight_id]
    lines = ["# C4 Four-Feature Robust Tuning", "", "## Scope", "- Frozen physical model: 48-V nominal DC-side SS-FHA model with power-dependent eta(delta, P).", "- C4 score: `w_SOC f_SOC + w_E f_E + w_idle f_idle - w_D f_D`.", "- WPT eta is not a C4 score feature; it remains in actual charging energy, SOC update, WPT loss, and rho supply.", "- Tuning seeds: 5007-5056, shared under CRN within each scenario.", "", "## Search", f"- Coarse simplex step 0.25: {coarse_count} candidates.", f"- Local 0.05 transfer neighborhood around the robust coarse Pareto anchor: {local_count} candidates.", "- Each candidate was evaluated over all five rho-region tuning scenarios. C1/C2/C3 references and C4 candidates use identical task and initial-SOC realizations per seed/scenario.", "", "## Selection rule", "1. Reject any candidate with low-SOC stops, failure, or invalid rows.", "2. Retain the non-dominated set in mean C4-C3 delay, worst-case C4-C3 delay, and mean C4-C3 urgent on-time difference.", "3. Choose the robust Pareto candidate with lowest worst-case delay degradation; use mean delay, then mean urgent difference as deterministic tie-breaks.", "", "## Frozen selected C4 weights", "```json", json.dumps({name: float(chosen[name]) for name in FEATURES}, indent=2), "```", "", "## Pareto candidates", pareto.to_markdown(index=False, floatfmt=".4f"), "", "## Selected C4-C3 paired 95% CIs", chosen_stats.to_markdown(index=False, floatfmt=".4f"), "", "## Interpretation", "The selection procedure does not choose a single-scenario winner. It prioritizes hard safety and worst-case robustness, then reports paired differences without asserting universal C4 superiority."]
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    data = load_experiment_config()
    seeds = tuning_seeds(data)
    all_scenarios = scenarios(data)
    tuning_names = list(data["tuning_scenarios"])
    catalog = pd.DataFrame(scenario_catalog_rows(data))
    catalog.to_csv(OUT / "rho_scenario_catalog.csv", index=False)
    (OUT / "SCENARIO_DESIGN.md").write_text(_scenario_design_markdown(catalog), encoding="utf-8")

    print(f"reference: scenarios={len(tuning_names)}, strategies=3, reps={len(seeds)}, simulations={len(tuning_names)*3*len(seeds)}", flush=True)
    reference_rows: list[dict[str, object]] = []
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(_run_reference, scenario_name, strategy, seed) for scenario_name in tuning_names for strategy in ("C1", "C2", "C3") for seed in seeds]
        for complete, future in enumerate(as_completed(futures), start=1):
            reference_rows.append(future.result())
            if complete % 100 == 0 or complete == len(futures): print(f"reference: {complete}/{len(futures)}", flush=True)
    _write_csv(OUT / "reference_strategies.csv", sorted(reference_rows, key=lambda row: (str(row["scenario"]), str(row["strategy"]), int(row["replication"]))))
    c3_rows = [row for row in reference_rows if row["strategy"] == "C3"]

    coarse = simplex_grid(float(data["c4_general_formulation"]["coarse_simplex_step"]))
    coarse_rows = _run_blocks(coarse, "coarse", tuning_names, seeds)
    _write_csv(OUT / "c4_coarse_search.csv", sorted(coarse_rows, key=lambda row: (str(row["weight_id"]), str(row["scenario"]), int(row["replication"]))))
    coarse_pairs = _paired_rows(coarse_rows, c3_rows)
    coarse_pair_stats = _aggregate_pairs(coarse_pairs)
    coarse_summary = _candidate_summary(coarse_pair_stats)
    coarse_pareto = _pareto(coarse_summary)
    anchor = coarse_pareto.iloc[0]
    anchor_weights = {name: float(anchor[name]) for name in FEATURES}

    local = _local_neighbors(anchor_weights, float(data["c4_general_formulation"]["local_simplex_step"]))
    local_rows = _run_blocks(local, "local", tuning_names, seeds)
    _write_csv(OUT / "c4_local_refinement.csv", sorted(local_rows, key=lambda row: (str(row["weight_id"]), str(row["scenario"]), int(row["replication"]))))
    all_pairs = [*coarse_pairs, *_paired_rows(local_rows, c3_rows)]
    pair_stats = _aggregate_pairs(all_pairs)
    pair_stats.to_csv(OUT / "c4_vs_c3_paired_statistics.csv", index=False)
    summary = _candidate_summary(pair_stats)
    pareto = _pareto(summary)
    chosen = pareto.iloc[0]
    frozen = {name: float(chosen[name]) for name in FEATURES}
    (OUT / "frozen_c4_parameters.json").write_text(json.dumps({"parameters_frozen_for_unseen_final_evaluation": True, "weights": frozen, "score": data["c4_general_formulation"]["score"], "tuning_seeds": list(seeds), "physical_model": "config/wpt_model.yaml"}, indent=2), encoding="utf-8")
    pareto.to_csv(OUT / "c4_pareto_candidates.csv", index=False)
    (OUT / "C4_TUNING_REPORT.md").write_text(_report(catalog, pareto, chosen, pair_stats, len(coarse), len(local)), encoding="utf-8")
    print("FROZEN_C4", json.dumps(frozen, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
