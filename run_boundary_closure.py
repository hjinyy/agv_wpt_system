from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import assert_never

from boundary_closure_analysis import (
    c4_lower_boundary_parameters,
    c5_lower_boundary_parameters,
    choose_boundary_candidate,
)
from parameter_refinement_analysis import (
    Aggregate,
    C4Parameters,
    C5Parameters,
    PairedStatistics,
    ReplicaMetrics,
    aggregate,
    paired_statistics,
)
from run_parameter_refinement import (
    REFINEMENT_SEEDS,
    _run_c4_parallel,
    _run_c5_parallel,
    effective_c5_coefficients,
)


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results_boundary_closure"
C4_BASELINE = C4Parameters(0.55, 0.175, 0.105, 0.070, 0.10)
C5_BASELINE = C5Parameters(2.0, 1.5, 1.5)


class BoundaryWeightError(Exception):
    pass


def _aggregate_map(results: dict[C4Parameters | C5Parameters, list[ReplicaMetrics]]) -> dict[C4Parameters | C5Parameters, Aggregate]:
    return {parameters: aggregate(parameters, rows) for parameters, rows in results.items()}


def _metric_rows(results: dict[C4Parameters | C5Parameters, list[ReplicaMetrics]]) -> list[dict[str, float | int]]:
    rows: list[dict[str, float | int]] = []
    for parameters, result in sorted(_aggregate_map(results).items(), key=lambda item: str(item[0])):
        data = asdict(result)
        data.pop("parameters")
        row = {**asdict(parameters), **data}
        match parameters:
            case C5Parameters():
                row.update(effective_c5_coefficients(parameters))
            case C4Parameters():
                pass
            case unreachable:
                assert_never(unreachable)
        rows.append(row)
    return rows


def _paired_rows(
    prefix: str,
    baseline: C4Parameters | C5Parameters,
    results: dict[C4Parameters | C5Parameters, list[ReplicaMetrics]],
) -> tuple[list[dict[str, float | int | str]], dict[C4Parameters | C5Parameters, list[PairedStatistics]]]:
    baseline_rows = results[baseline]
    rows: list[dict[str, float | int | str]] = []
    comparisons: dict[C4Parameters | C5Parameters, list[PairedStatistics]] = {}
    for parameters, candidate_rows in results.items():
        label = f"{prefix}_{parameters}_minus_baseline"
        paired = [paired_statistics(label, metric, candidate_rows, baseline_rows) for metric in ("mean_delay", "urgent_on_time_rate")]
        comparisons[parameters] = paired
        rows.extend(asdict(item) for item in paired)
    return rows, comparisons


def _write_csv(path: Path, rows: list[dict[str, float | int | str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _table(rows: list[dict[str, float | int | str]], columns: tuple[str, ...]) -> list[str]:
    return [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
        *("| " + " | ".join(str(row[column]) for column in columns) + " |" for row in rows),
    ]


def _write_report(
    c4_results: dict[C4Parameters | C5Parameters, Aggregate],
    c5_results: dict[C4Parameters | C5Parameters, Aggregate],
    c4_pairs: list[dict[str, float | int | str]],
    c5_pairs: list[dict[str, float | int | str]],
    c4_final: Aggregate,
    c5_final: Aggregate,
) -> None:
    c4_closed = c4_final.parameters == C4_BASELINE
    c5_closed = c5_final.parameters == C5_BASELINE
    lines = [
        "# C4/C5 Lower-Boundary Closure Report",
        "",
        "## Scope",
        "Only the specified C4 and C5 lower-boundary parameter sets were evaluated. DES architecture, strategy logic, WPT model, task generation, safety rules, scenario, and metrics were unchanged.",
        "",
        "## CRN protocol",
        f"All candidates used the same 50 seeds: {REFINEMENT_SEEDS[0]}-{REFINEMENT_SEEDS[-1]}. Paired differences are candidate minus baseline; negative delay and positive urgent on-time favor the candidate.",
        "",
        "## C4 lower-boundary result",
        f"C4 lower boundary is {'closed' if c4_closed else 'not closed'}. Frozen C4: `{asdict(c4_final.parameters)}`.",
        *_table(_metric_rows_from_aggregates(c4_results), ("w1", "w2", "w3", "w4", "w5", "mean_delay", "urgent_on_time_rate", "safety_violation_count")),
        "",
        "## C5 lower-boundary result",
        f"C5 lower boundary is {'closed' if c5_closed else 'not closed'}. Frozen C5: `{asdict(c5_final.parameters)}`.",
        *_table(_metric_rows_from_aggregates(c5_results), ("lambda_soc", "lambda_task", "lambda_kpi", "mean_delay", "urgent_on_time_rate", "infeasible_count", "simulation_failure_count")),
        "",
        "## Paired 95% confidence intervals",
        *_table(c4_pairs + c5_pairs, ("comparison", "metric", "mean_difference", "ci95_low", "ci95_high", "improved_replication_rate", "paired_replications")),
        "",
        "## Decision rule",
        "A lower candidate could replace the current candidate only when it had zero actual low-SOC stops, zero infeasibility, zero simulation failures, better mean delay and urgent on-time rate, and both paired 95% intervals supported improvement. Otherwise, the current candidate was retained.",
        "",
        "## Freeze scope",
        "Only C4/C5 parameter closure was performed. No final C1-C5 comparison, Base Case, Stress Grid, or figure regeneration was run.",
    ]
    (OUT / "BOUNDARY_CLOSURE_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def _metric_rows_from_aggregates(results: dict[C4Parameters | C5Parameters, Aggregate]) -> list[dict[str, float | int]]:
    rows: list[dict[str, float | int]] = []
    for parameters, result in sorted(results.items(), key=lambda item: str(item[0])):
        data = asdict(result)
        data.pop("parameters")
        rows.append({**asdict(parameters), **data})
    return rows


def _validate_c4_weights(parameters: list[C4Parameters]) -> None:
    for parameter in parameters:
        if abs(sum(parameter.weights.values()) - 1.0) > 1e-12:
            raise BoundaryWeightError(f"C4 weights must sum to one: {parameter}")


def main() -> None:
    c4_parameters = c4_lower_boundary_parameters()
    c5_parameters = c5_lower_boundary_parameters()
    _validate_c4_weights(c4_parameters)
    print("C4 combinations:", [asdict(parameters) for parameters in c4_parameters])
    print("C5 combinations:", [asdict(parameters) for parameters in c5_parameters])
    print("Seeds:", list(REFINEMENT_SEEDS))
    print("C4 baseline:", asdict(C4_BASELINE))
    print("C5 baseline:", asdict(C5_BASELINE))
    print("Expected total runs:", (len(c4_parameters) + len(c5_parameters)) * len(REFINEMENT_SEEDS))

    OUT.mkdir(exist_ok=True)
    c4_runs = _run_c4_parallel(c4_parameters)
    c5_runs = _run_c5_parallel(c5_parameters)
    c4_aggregates = _aggregate_map(c4_runs)
    c5_aggregates = _aggregate_map(c5_runs)
    c4_pair_rows, c4_comparisons = _paired_rows("C4", C4_BASELINE, c4_runs)
    c5_pair_rows, c5_comparisons = _paired_rows("C5", C5_BASELINE, c5_runs)
    c4_final = choose_boundary_candidate(c4_aggregates[C4_BASELINE], list(c4_aggregates.values()), c4_comparisons)
    c5_final = choose_boundary_candidate(c5_aggregates[C5_BASELINE], list(c5_aggregates.values()), c5_comparisons)
    _write_csv(OUT / "c4_lower_boundary_check.csv", _metric_rows(c4_runs))
    _write_csv(OUT / "c5_lower_boundary_check.csv", _metric_rows(c5_runs))
    _write_csv(OUT / "c4_paired_statistics.csv", c4_pair_rows)
    _write_csv(OUT / "c5_paired_statistics.csv", c5_pair_rows)
    frozen = {
        "parameters_frozen": True,
        "refinement_seeds": list(REFINEMENT_SEEDS),
        "C4": asdict(c4_final.parameters),
        "C5": {**asdict(c5_final.parameters), **effective_c5_coefficients(c5_final.parameters)},
        "c4_lower_boundary_closed": c4_final.parameters == C4_BASELINE,
        "c5_lower_boundary_closed": c5_final.parameters == C5_BASELINE,
    }
    (OUT / "final_frozen_parameters.json").write_text(json.dumps(frozen, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_report(c4_aggregates, c5_aggregates, c4_pair_rows, c5_pair_rows, c4_final, c5_final)
    print("Final frozen C4:", asdict(c4_final.parameters))
    print("Final frozen C5:", asdict(c5_final.parameters))


if __name__ == "__main__":
    main()
