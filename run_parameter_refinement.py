from __future__ import annotations

import csv
import json
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path
from typing import TypeVar

from tqdm import tqdm

from parameter_refinement_analysis import (
    Aggregate,
    C4Parameters,
    C5Parameters,
    PairedStatistics,
    ReplicaMetrics,
    aggregate,
    c4_adaptive_parameters,
    c4_local_parameters,
    c5_common_parameters,
    c5_oat_parameters,
    choose_refined,
    is_joint_kpi_leader,
    paired_statistics,
    pareto,
)
from parameter_refinement_simulation import C4_OLD, run_c4_replications, run_c5_replications


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results_parameter_refinement"
REFINEMENT_SEEDS = tuple(range(3007, 3057))
C5_COMMON_ALPHAS = (1.0, 1.5, 2.0, 2.5, 3.0, 4.0)
C5_OLD = C5Parameters(2.0, 2.0, 2.0)
C5_ORIGINAL = C5Parameters(1.0, 1.0, 1.0)
P = TypeVar("P", C4Parameters, C5Parameters)


def effective_c5_coefficients(parameters: C5Parameters) -> dict[str, float]:
    return {
        "effective_soc_shortage_coefficient": 200.0 * parameters.lambda_soc,
        "effective_soc_risk_coefficient": 6.0 * parameters.lambda_soc,
        "effective_task_scale": parameters.lambda_task,
        "effective_kpi_risk_coefficient": 30.0 * parameters.lambda_kpi,
    }


def _c4_worker(parameters: C4Parameters, seeds: tuple[int, ...]) -> tuple[C4Parameters, list[ReplicaMetrics]]:
    return parameters, run_c4_replications(parameters, seeds)


def _c5_worker(parameters: C5Parameters, seeds: tuple[int, ...]) -> tuple[C5Parameters, list[ReplicaMetrics]]:
    return parameters, run_c5_replications(parameters, seeds)


def _run_c4_parallel(parameters: list[C4Parameters]) -> dict[C4Parameters, list[ReplicaMetrics]]:
    return _run_parallel(parameters, _c4_worker)


def _run_c5_parallel(parameters: list[C5Parameters]) -> dict[C5Parameters, list[ReplicaMetrics]]:
    return _run_parallel(parameters, _c5_worker)


def _run_parallel(parameters: list[P], worker) -> dict[P, list[ReplicaMetrics]]:
    if not parameters:
        return {}
    workers = min(int(os.environ.get("PARAM_REFINEMENT_WORKERS", "4")), len(parameters))
    results: dict[P, list[ReplicaMetrics]] = {}
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(worker, parameter, REFINEMENT_SEEDS) for parameter in parameters]
        for future in tqdm(as_completed(futures), total=len(futures), desc="weight combinations"):
            parameter, rows = future.result()
            results[parameter] = rows
    return results


def _aggregate(results: dict[P, list[ReplicaMetrics]]) -> list[Aggregate]:
    return [aggregate(parameters, rows) for parameters, rows in sorted(results.items(), key=lambda item: str(item[0]))]


def _rows_with_phase(results: dict[P, list[ReplicaMetrics]], phase_by_parameter: dict[P, str]) -> list[dict[str, float | int | str]]:
    rows: list[dict[str, float | int | str]] = []
    for result in _aggregate(results):
        data = asdict(result)
        parameters = data.pop("parameters")
        row = {"phase": phase_by_parameter[result.parameters], **parameters, **data}
        if isinstance(result.parameters, C5Parameters):
            row.update(effective_c5_coefficients(result.parameters))
        rows.append(row)
    return rows


def _write_csv(filename: str, rows: list[dict[str, float | int | str]]) -> None:
    path = OUT / filename
    if not rows:
        return
    fieldnames = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _paired_rows(comparison: str, new: list[ReplicaMetrics], old: list[ReplicaMetrics]) -> list[dict[str, float | int | str]]:
    return [asdict(paired_statistics(comparison, metric, new, old)) for metric in ("mean_delay", "urgent_on_time_rate")]


def _format_parameters(parameters: C4Parameters | C5Parameters) -> str:
    values = asdict(parameters)
    return ", ".join(f"{name}={value:.2f}" for name, value in values.items())


def _table(rows: list[dict[str, float | int | str]], fields: tuple[str, ...]) -> list[str]:
    header = "| " + " | ".join(fields) + " |"
    separator = "| " + " | ".join("---" for _ in fields) + " |"
    rendered = [header, separator]
    for row in rows:
        rendered.append("| " + " | ".join(str(row[field]) for field in fields) + " |")
    return rendered


def _write_report(
    c5_common: list[Aggregate],
    c5_oat: list[Aggregate],
    c4_results: list[Aggregate],
    c5_final: Aggregate,
    c4_final: Aggregate,
    c5_pairs: list[dict[str, float | int | str]],
    c4_pairs: list[dict[str, float | int | str]],
    c5_boundary_expanded: bool,
    c4_boundary_expanded: bool,
) -> None:
    c5_pareto = pareto([item for item in [*c5_common, *c5_oat] if item.infeasible_count == 0 and item.safety_violation_count == 0 and item.simulation_failure_count == 0])
    c4_pareto = pareto([item for item in c4_results if item.infeasible_count == 0 and item.safety_violation_count == 0 and item.simulation_failure_count == 0])
    lines = [
        "# C4/C5 Parameter Refinement Report",
        "",
        "## 1. Scope and fixed components",
        "Only the C4 priority weights and C5 objective coefficients were changed. The DES, C1-C5 strategy structures, WPT state model, 15-minute rolling horizon, 60-second slot, first-slot execution, MILP constraints, scenario, task generation, and KPI definitions were retained.",
        "",
        "## 2. C5 common-scale scan and boundary check",
        f"The common scale scan evaluated alpha in {list(C5_COMMON_ALPHAS)} with 50 replications each. Boundary extension to alpha=5 and 6 was {'run' if c5_boundary_expanded else 'not triggered'}, because alpha=4 {'was' if c5_boundary_expanded else 'was not'} the joint mean-delay/urgent-on-time leader in the initially tested range.",
        *_table([{"parameters": _format_parameters(item.parameters), "mean_delay": round(item.mean_delay, 4), "urgent_on_time_rate": round(item.urgent_on_time_rate, 4)} for item in c5_common], ("parameters", "mean_delay", "urgent_on_time_rate")),
        "",
        "## 3. C5 one-at-a-time refinement",
        f"OAT points changed one C5 scale at a time around the selected common-scale alpha. The locally refined C5 candidate is `{_format_parameters(c5_final.parameters)}`.",
        "",
        "## 4. C4 local refinement",
        f"The local C4 grid was evaluated with 50 CRN-matched replications. Extension to w1=0.75/0.80 was {'run' if c4_boundary_expanded else 'not triggered'}. The locally refined C4 candidate is `{_format_parameters(c4_final.parameters)}`.",
        "",
        "## 5. Safety interpretation",
        "Hard rejection required zero MILP infeasibility, zero simulation failures, and zero actual low-SOC stops. Critical-SOC crossings are reported as preventive-rule activations and were not used as automatic disqualification.",
        "",
        "## 6. Pareto interpretation",
        f"Safe C5 Pareto candidates: {', '.join(_format_parameters(item.parameters) for item in c5_pareto)}.",
        f"Safe C4 Pareto candidates: {', '.join(_format_parameters(item.parameters) for item in c4_pareto)}.",
        "",
        "## 7. Replication-wise paired uncertainty",
        "Paired differences are new minus old, using the same seed for each member of a pair. Negative delay differences and positive urgent-on-time differences favor the refined candidate.",
        *_table(c5_pairs + c4_pairs, ("comparison", "metric", "mean_difference", "ci95_low", "ci95_high", "improved_replication_rate", "paired_replications")),
        "",
        "## 8. Selection rationale",
        "Selection was restricted to safe solutions and Pareto comparisons. Where effects were practically close, proximity to the previous parameterization was preferred; no arbitrary composite score was used.",
        "",
        "## 9. Frozen parameters",
        "Only the selected C4 and C5 parameter values are frozen in `final_frozen_parameters.json`. A final independent-seed C1-C5 evaluation was not run in this refinement experiment.",
        "",
        "## 10. Limitation",
        "These conclusions apply to the tested/refined parameter range and this fixed DES scenario. They are not a claim of a global optimum.",
    ]
    (OUT / "PARAMETER_REFINEMENT_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def _print_preflight(c5_common: list[C5Parameters], c4_local: list[C4Parameters]) -> None:
    print("C5 common-scale combinations:", [asdict(parameters) for parameters in c5_common])
    print("C5 common-scale expected simulation runs:", len(c5_common) * len(REFINEMENT_SEEDS))
    print("C5 OAT maximum additional runs (central point reused):", 6 * len(REFINEMENT_SEEDS))
    print("C4 valid local combination count:", len(c4_local))
    print("C4 first five combinations:", [asdict(parameters) for parameters in c4_local[:5]])
    print("Refinement CRN seeds:", f"{REFINEMENT_SEEDS[0]}-{REFINEMENT_SEEDS[-1]}")
    print("Old C4 candidate:", asdict(C4_OLD))
    print("Old C5 candidate:", asdict(C5_OLD))
    print("Original C5 baseline:", asdict(C5_ORIGINAL))


def main() -> None:
    OUT.mkdir(exist_ok=True)
    c5_common_parameters_list = c5_common_parameters(C5_COMMON_ALPHAS)
    c4_local_parameters_list = c4_local_parameters()
    _print_preflight(c5_common_parameters_list, c4_local_parameters_list)

    c5_runs = _run_c5_parallel(c5_common_parameters_list)
    c5_common_results = _aggregate(c5_runs)
    alpha_four = next(item for item in c5_common_results if item.parameters == C5Parameters(4.0, 4.0, 4.0))
    c5_boundary_expanded = is_joint_kpi_leader(alpha_four, c5_common_results)
    if c5_boundary_expanded:
        c5_runs.update(_run_c5_parallel(c5_common_parameters((5.0, 6.0))))
        c5_common_results = _aggregate(c5_runs)
    c5_common_phase = {parameters: "common_scale" for parameters in c5_runs}
    _write_csv("c5_common_scale_boundary.csv", _rows_with_phase(c5_runs, c5_common_phase))

    c5_common_choice = choose_refined(c5_common_results, C5_OLD)
    alpha_best = c5_common_choice.parameters.lambda_soc
    c5_oat_parameters_list = c5_oat_parameters(alpha_best)
    c5_oat_new = [parameters for parameters in c5_oat_parameters_list if parameters not in c5_runs]
    c5_runs.update(_run_c5_parallel(c5_oat_new))
    c5_oat_runs = {parameters: c5_runs[parameters] for parameters in c5_oat_parameters_list}
    c5_oat_phase = {parameters: "oat" for parameters in c5_oat_runs}
    _write_csv("c5_oat_refinement.csv", _rows_with_phase(c5_oat_runs, c5_oat_phase))
    c5_final = choose_refined(_aggregate(c5_runs), C5_OLD)

    c4_runs = _run_c4_parallel(c4_local_parameters_list)
    c4_initial_results = _aggregate(c4_runs)
    c4_w1_upper = [item for item in c4_initial_results if item.parameters.w1 == 0.70]
    c4_boundary_expanded = any(is_joint_kpi_leader(item, c4_initial_results) for item in c4_w1_upper)
    if c4_boundary_expanded:
        c4_runs.update(_run_c4_parallel(c4_adaptive_parameters()))
    c4_phase = {parameters: "local" if parameters in c4_local_parameters_list else "adaptive_boundary" for parameters in c4_runs}
    _write_csv("c4_local_refinement.csv", _rows_with_phase(c4_runs, c4_phase))
    c4_final = choose_refined(_aggregate(c4_runs), C4_OLD)

    c5_pairs = _paired_rows("refined_C5_minus_old_C5_2_2_2", c5_runs[c5_final.parameters], c5_runs[C5_OLD])
    c5_pairs += _paired_rows("refined_C5_minus_original_C5_1_1_1", c5_runs[c5_final.parameters], c5_runs[C5_ORIGINAL])
    c4_pairs = _paired_rows("refined_C4_minus_old_C4", c4_runs[c4_final.parameters], c4_runs[C4_OLD])
    _write_csv("c5_paired_statistics.csv", c5_pairs)
    _write_csv("c4_paired_statistics.csv", c4_pairs)

    frozen = {
        "parameters_frozen": True,
        "refinement_seeds": list(REFINEMENT_SEEDS),
        "C4": asdict(c4_final.parameters),
        "C5": {**asdict(c5_final.parameters), **effective_c5_coefficients(c5_final.parameters)},
        "selection_scope": "tested/refined parameter range under the fixed primary scenario",
        "final_independent_c1_c5_evaluation_run": False,
    }
    (OUT / "final_frozen_parameters.json").write_text(json.dumps(frozen, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_report(c5_common_results, _aggregate(c5_oat_runs), _aggregate(c4_runs), c5_final, c4_final, c5_pairs, c4_pairs, c5_boundary_expanded, c4_boundary_expanded)
    print("Frozen C4:", asdict(c4_final.parameters))
    print("Frozen C5:", asdict(c5_final.parameters))


if __name__ == "__main__":
    main()
