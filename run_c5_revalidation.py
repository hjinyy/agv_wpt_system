from __future__ import annotations

"""C5 OAT robust revalidation for the approved rho catalog; never uses final seeds."""

import csv
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

import v2_runner
import v3_runner
from rho_pipeline import FEATURES, configuration_for, load_experiment_config, scenarios, tuning_seeds
from simulation.final_wpt import physical_efficiency_values
from v2_runner import generate_common
from v3_runner import V3Sim

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "pre_final"


def _physical_callback() -> None:
    v2_runner.eta_values = physical_efficiency_values
    v3_runner.eta_values = physical_efficiency_values


def scale_id(scales: dict[str, float]) -> str:
    return f"soc{scales['lambda_soc']:.1f}_task{scales['lambda_task']:.1f}_kpi{scales['lambda_kpi']:.1f}"


def oat_candidates(data: dict | None = None) -> list[dict[str, float]]:
    data = load_experiment_config() if data is None else data
    old = data["c5_revalidation"]["reference_scales"]
    baseline = dict(zip(("lambda_soc", "lambda_task", "lambda_kpi"), map(float, old)))
    unique = {scale_id(baseline): baseline}
    for name, values in data["c5_revalidation"]["oat_values"].items():
        for value in values:
            candidate = dict(baseline); candidate[name] = float(value)
            unique[scale_id(candidate)] = candidate
    return list(unique.values())


def _run_one(scenario_name: str, scales: dict[str, float], seed: int) -> dict[str, object]:
    _physical_callback()
    scenario = scenarios()[scenario_name]
    config = configuration_for(scenario, {feature: 0.25 for feature in FEATURES})
    config.update({"c5_lambda_soc": scales["lambda_soc"], "c5_lambda_task": scales["lambda_task"], "c5_lambda_kpi": scales["lambda_kpi"]})
    try:
        tasks, initial = generate_common(config, seed, distances=scenario.distances, urgent_ratio=scenario.urgent_ratio)
        lookup = {task.task_id: index for index, task in enumerate(tasks)}
        simulation = V3Sim(config, "C5", seed, tasks, initial, scenario_name, variable_eta=True, task_index_lookup=lookup,
                           predicted_eta_mode="variable", realized_eta_mode="variable")
        result = simulation.run()
        result.update({"scale_id": scale_id(scales), **scales, "simulation_failure": 0, "error": ""})
        return result
    except Exception as exc:  # retained for hard-rejection evidence rather than silently dropping a run
        return {"scenario": scenario_name, "strategy": "C5", "replication": seed, "scale_id": scale_id(scales), **scales,
                "simulation_failure": 1, "error": repr(exc), "low_soc_stops": np.nan, "solver_infeasible_calls": np.nan,
                "mean_delay": np.nan, "urgent_on_time_rate": np.nan, "completion_rate": np.nan, "fleet_min_soc": np.nan,
                "solver_computation_time_s": np.nan, "solver_calls": np.nan}


def _write(path: Path, rows: list[dict[str, object]]) -> None:
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def _summary(rows: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for (sid, scenario), group in rows.groupby(["scale_id", "scenario"], sort=True):
        first = group.iloc[0]
        records.append({"scale_id": sid, "scenario": scenario, **{name: float(first[name]) for name in ("lambda_soc", "lambda_task", "lambda_kpi")},
                        "replications": int(len(group)), "mean_delay_min": float(group.mean_delay.mean()),
                        "urgent_on_time_percent": float(group.urgent_on_time_rate.mean()), "completion_rate_percent": float(group.completion_rate.mean()),
                        "fleet_min_soc": float(group.fleet_min_soc.min()), "mean_solver_time_s": float(group.solver_computation_time_s.mean()),
                        "p95_solver_time_s": float(group.solver_computation_time_s.quantile(.95)), "total_solver_calls": int(group.solver_calls.sum()),
                        "solver_infeasible_calls": int(group.solver_infeasible_calls.sum()), "low_soc_stops": int(group.low_soc_stops.sum()),
                        "simulation_failures": int(group.simulation_failure.sum())})
    return pd.DataFrame(records)


def _candidate_summary(summary: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for sid, group in summary.groupby("scale_id", sort=True):
        first = group.iloc[0]
        records.append({"scale_id": sid, **{name: float(first[name]) for name in ("lambda_soc", "lambda_task", "lambda_kpi")},
                        "mean_delay_min": float(group.mean_delay_min.mean()), "worst_scenario_delay_min": float(group.mean_delay_min.max()),
                        "mean_urgent_on_time_percent": float(group.urgent_on_time_percent.mean()), "worst_urgent_on_time_percent": float(group.urgent_on_time_percent.min()),
                        "mean_completion_rate_percent": float(group.completion_rate_percent.mean()), "worst_fleet_min_soc": float(group.fleet_min_soc.min()),
                        "mean_solver_time_s": float(group.mean_solver_time_s.mean()), "total_solver_calls": int(group.total_solver_calls.sum()),
                        "hard_reject": bool((group.solver_infeasible_calls > 0).any() or (group.low_soc_stops > 0).any() or (group.simulation_failures > 0).any())})
    return pd.DataFrame(records)


def _pareto(summary: pd.DataFrame) -> pd.DataFrame:
    valid = summary[~summary.hard_reject].copy()
    # minimize delay and solve time; maximize urgent/completion/minimum SOC.
    columns = ["mean_delay_min", "worst_scenario_delay_min", "mean_urgent_on_time_percent", "mean_completion_rate_percent", "worst_fleet_min_soc", "mean_solver_time_s"]
    values = valid[columns].to_numpy(float)
    keep = []
    for i, c in enumerate(values):
        no_worse = ((values[:, 0] <= c[0]) & (values[:, 1] <= c[1]) & (values[:, 2] >= c[2]) & (values[:, 3] >= c[3]) & (values[:, 4] >= c[4]) & (values[:, 5] <= c[5]))
        strict = ((values[:, 0] < c[0]) | (values[:, 1] < c[1]) | (values[:, 2] > c[2]) | (values[:, 3] > c[3]) | (values[:, 4] > c[4]) | (values[:, 5] < c[5]))
        keep.append(not bool((no_worse & strict).any()))
    return valid.loc[keep].sort_values(["worst_scenario_delay_min", "mean_delay_min", "mean_urgent_on_time_percent", "mean_solver_time_s"], ascending=[True, True, False, True])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    data = load_experiment_config(); seeds = tuning_seeds(data); names = list(data["tuning_scenarios"]); candidates = oat_candidates(data)
    expected_runs = len(candidates) * len(names) * len(seeds)
    pilot_calls = 5015  # measured with old scales for one seed across all five scenarios in the approved pre-final audit
    plan = {"method": "OAT around old scales; not full 27-grid", "candidates": candidates, "scenario_count": len(names), "seed_count": len(seeds),
            "expected_simulations": expected_runs, "pilot_solver_calls_per_5scenario_seed": pilot_calls,
            "expected_solver_calls_from_pilot": pilot_calls * len(candidates) * len(seeds), "final_seed_range_used": None}
    (OUT / "c5_revalidation_plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    print("C5_PLAN", json.dumps(plan, sort_keys=True), flush=True)
    jobs = [(scenario, scales, seed) for scales in candidates for scenario in names for seed in seeds]
    rows: list[dict[str, object]] = []
    with ProcessPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(_run_one, scenario, scales, seed) for scenario, scales, seed in jobs]
        for complete, future in enumerate(as_completed(futures), 1):
            rows.append(future.result())
            if complete % 100 == 0 or complete == len(futures): print(f"C5_REVALIDATION {complete}/{len(futures)}", flush=True)
    rows.sort(key=lambda r: (str(r["scale_id"]), str(r["scenario"]), int(r["replication"])))
    _write(OUT / "c5_revalidation_raw.csv", rows)
    frame = pd.DataFrame(rows)
    summary = _summary(frame); summary.to_csv(OUT / "c5_revalidation_summary.csv", index=False)
    candidates_summary = _candidate_summary(summary); candidates_summary.to_csv(OUT / "c5_refinement_candidates.csv", index=False)
    pareto = _pareto(candidates_summary); pareto.to_csv(OUT / "c5_pareto_candidates.csv", index=False)
    chosen = pareto.iloc[0]
    frozen = {name: float(chosen[name]) for name in ("lambda_soc", "lambda_task", "lambda_kpi")}
    (OUT / "frozen_c5_parameters.json").write_text(json.dumps({"parameters_frozen_for_unseen_final_evaluation": True, "scales": frozen,
        "structure": "15-min rolling-horizon MILP; 60-s slots; first-slot receding-horizon implementation", "terminology": "rolling-horizon MILP reference / optimization-based reference",
        "tuning_seeds": list(seeds), "selection": "hard safety/solver rejection then Pareto robustness across rho regions"}, indent=2), encoding="utf-8")
    report = ["# C5 Robust Revalidation and OAT Refinement", "", "## Scope", "- C5 structure was unchanged: 15-minute rolling horizon, 60-s slots, MILP constraints, and first-slot receding-horizon execution.", "- Only lambda_soc, lambda_task, and lambda_kpi objective scales were revalidated.", "- C5 is a **rolling-horizon MILP reference** / **optimization-based reference**, not a clairvoyant global optimum.", "", "## Compute plan", "```json", json.dumps(plan, indent=2), "```", "", "## Scenario summaries", summary.to_markdown(index=False, floatfmt=".4f"), "", "## Cross-region candidates", candidates_summary.to_markdown(index=False, floatfmt=".4f"), "", "## Pareto candidates", pareto.to_markdown(index=False, floatfmt=".4f"), "", "## Frozen scales", "```json", json.dumps(frozen, indent=2), "```"]
    (OUT / "C5_REVALIDATION_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("FROZEN_C5", json.dumps(frozen, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
