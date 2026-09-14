from __future__ import annotations

import csv
import json
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import deepcopy
from pathlib import Path

import pandas as pd

import v2_runner
import v3_runner
from final_evaluation import FINAL_EVALUATION_SEEDS, PRIMARY_DISTANCES, final_configuration
from simulation.final_wpt import physical_efficiency_values
from v2_runner import generate_common
from v3_runner import V3Sim, feature_stats


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results_final"
C5_ABLATIONS = {
    "Full objective": (2.0, 1.5, 1.5),
    "No SOC term": (0.0, 1.5, 1.5),
    "No task term": (2.0, 0.0, 1.5),
    "No KPI-risk term": (2.0, 1.5, 0.0),
}


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _primary_configuration() -> dict:
    configuration = final_configuration()
    configuration.update({"n_agvs": 5, "n_pads": 1, "task_arrival_rate_per_h": 90, "wpt_power_kw": 3})
    return configuration


def _run_c4_diagnostic(seed: int) -> dict[str, object]:
    v2_runner.eta_values = physical_efficiency_values
    v3_runner.eta_values = physical_efficiency_values
    configuration = _primary_configuration()
    tasks, initial_soc = generate_common(configuration, seed, distances=PRIMARY_DISTANCES, urgent_ratio=0.2)
    lookup = {task.task_id: index for index, task in enumerate(tasks)}
    simulation = V3Sim(configuration, "C4", seed, tasks, initial_soc, "final_c4_diagnostics", variable_eta=True, task_index_lookup=lookup, predicted_eta_mode="variable", realized_eta_mode="variable")
    metrics = simulation.run()
    stats = feature_stats(simulation.feature_rows)
    row: dict[str, object] = {
        "replication": seed,
        "charging_contention_events": metrics["charging_contention_events"],
        "different_decision_rate_C4_vs_C3": metrics["different_decision_rate_C4_vs_C3"],
    }
    if not stats.empty:
        feature_row = stats.iloc[0]
        for feature in ("one_minus_soc", "E_next", "T_idle", "eta_WPT", "D"):
            row[f"{feature}_std"] = float(feature_row[f"{feature}_std"])
    return row


def _run_c5_ablation(seed: int) -> list[dict[str, object]]:
    v2_runner.eta_values = physical_efficiency_values
    v3_runner.eta_values = physical_efficiency_values
    base = _primary_configuration()
    tasks, initial_soc = generate_common(base, seed, distances=PRIMARY_DISTANCES, urgent_ratio=0.2)
    lookup = {task.task_id: index for index, task in enumerate(tasks)}
    rows: list[dict[str, object]] = []
    for variant, (lambda_soc, lambda_task, lambda_kpi) in C5_ABLATIONS.items():
        configuration = deepcopy(base)
        configuration["c5_lambda_soc"] = lambda_soc
        configuration["c5_lambda_task"] = lambda_task
        configuration["c5_lambda_kpi"] = lambda_kpi
        simulation = V3Sim(configuration, "C5", seed, deepcopy(tasks), list(initial_soc), "final_c5_objective_ablation", variable_eta=True, task_index_lookup=lookup, predicted_eta_mode="variable", realized_eta_mode="variable")
        metrics = simulation.run()
        metrics.update({
            "variant": variant,
            "replication": seed,
            "lambda_soc": lambda_soc,
            "lambda_task": lambda_task,
            "lambda_kpi": lambda_kpi,
            "infeasible_count": int(metrics.get("solver_infeasible_calls", 0)),
            "simulation_failure_count": 0,
        })
        rows.append(metrics)
    return rows


def _write_c5_ablation(seeds: tuple[int, ...], partial: bool) -> None:
    c5_rows: list[dict[str, object]] = []
    with ProcessPoolExecutor(max_workers=min(4, len(seeds))) as executor:
        futures = [executor.submit(_run_c5_ablation, seed) for seed in seeds]
        for index, future in enumerate(as_completed(futures), start=1):
            c5_rows.extend(future.result())
            print(f"C5 objective ablation: {index}/{len(seeds)}", flush=True)
    filename = f"c5_objective_ablation_part_{seeds[0]}_{seeds[-1]}.csv" if partial else "c5_objective_ablation.csv"
    _write_csv(OUT / filename, sorted(c5_rows, key=lambda row: (str(row["variant"]), int(row["replication"]))))


def _merge_c5_ablation() -> None:
    files = sorted(OUT.glob("c5_objective_ablation_part_*.csv"))
    rows = [pd.read_csv(path) for path in files]
    merged = pd.concat(rows, ignore_index=True)
    merged = merged.drop_duplicates(subset=["variant", "replication"], keep="first")
    expected = len(FINAL_EVALUATION_SEEDS) * len(C5_ABLATIONS)
    if len(merged) != expected or merged["replication"].nunique() != len(FINAL_EVALUATION_SEEDS):
        raise RuntimeError(f"Expected {expected} ablation rows across 50 seeds; found {len(merged)}.")
    merged.sort_values(["variant", "replication"]).to_csv(OUT / "c5_objective_ablation.csv", index=False)
    (OUT / "c5_objective_ablation_metadata.json").write_text(json.dumps({"replications": 50, "seeds": list(FINAL_EVALUATION_SEEDS), "common_random_numbers": True, "baseline": "Full objective", "ablations": C5_ABLATIONS}, indent=2), encoding="utf-8")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    if "--merge-c5" in sys.argv:
        _merge_c5_ablation()
        return
    if "--c5-only" not in sys.argv:
        c4_rows: list[dict[str, object]] = []
        with ProcessPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(_run_c4_diagnostic, seed) for seed in FINAL_EVALUATION_SEEDS]
            for index, future in enumerate(as_completed(futures), start=1):
                c4_rows.append(future.result())
                if index % 5 == 0 or index == len(FINAL_EVALUATION_SEEDS):
                    print(f"C4 diagnostics: {index}/50", flush=True)
        _write_csv(OUT / "c4_priority_diagnostics.csv", sorted(c4_rows, key=lambda row: int(row["replication"])))
    if "--seed-start" in sys.argv:
        start_index = sys.argv.index("--seed-start") + 1
        count_index = sys.argv.index("--seed-count") + 1
        start = int(sys.argv[start_index])
        count = int(sys.argv[count_index])
        seeds = tuple(range(start, start + count))
        _write_c5_ablation(seeds, partial=True)
    else:
        _write_c5_ablation(FINAL_EVALUATION_SEEDS, partial=False)


if __name__ == "__main__":
    main()
