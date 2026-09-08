from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from run_c5_penalty_sensitivity import (
    C5PenaltyResult,
    effective_coefficients,
    generate_parameter_combinations,
    select_stage2_candidates,
)


def make_result(lambda_soc: float, lambda_task: float, lambda_kpi: float, delay: float, urgent_rate: float, critical_events: int = 0) -> C5PenaltyResult:
    coefficients = effective_coefficients(lambda_soc, lambda_task, lambda_kpi)
    return C5PenaltyResult(
        lambda_soc=lambda_soc,
        lambda_task=lambda_task,
        lambda_kpi=lambda_kpi,
        **coefficients,
        mean_delay=delay,
        mean_delay_std=0.1,
        urgent_on_time_rate=urgent_rate,
        urgent_on_time_std=0.1,
        completion_rate=100.0,
        wpt_loss_kwh=1.0,
        fleet_min_soc=30.0,
        critical_soc_event_count=critical_events,
        safety_violation_count=0,
        mean_solver_time=0.01,
        max_solver_time=0.02,
        solver_calls=10,
        infeasible_count=0,
        simulation_failure_count=0,
    )


def test_parameter_grid_has_all_27_combinations_and_expected_coefficients():
    combinations = generate_parameter_combinations()

    assert len(combinations) == 27
    assert (combinations[0].lambda_soc, combinations[0].lambda_task, combinations[0].lambda_kpi) == (0.5, 0.5, 0.5)
    assert effective_coefficients(2.0, 0.5, 0.5) == {
        'effective_soc_shortage_coefficient': 400.0,
        'effective_soc_risk_coefficient': 12.0,
        'effective_task_scale': 0.5,
        'effective_kpi_risk_coefficient': 15.0,
    }


def test_stage2_selection_excludes_unsafe_results_and_keeps_baseline():
    baseline = make_result(1.0, 1.0, 1.0, delay=5.0, urgent_rate=90.0)
    dominant = make_result(0.5, 1.0, 2.0, delay=4.0, urgent_rate=91.0)
    unsafe = make_result(2.0, 2.0, 2.0, delay=1.0, urgent_rate=99.0, critical_events=1)

    selected = select_stage2_candidates([baseline, dominant, unsafe])

    selected_triples = {(item.lambda_soc, item.lambda_task, item.lambda_kpi) for item in selected}
    assert (0.5, 1.0, 2.0) in selected_triples
    assert (1.0, 1.0, 1.0) in selected_triples
    assert (2.0, 2.0, 2.0) not in selected_triples
    assert len(selected) <= 5
    assert all(np.isclose(item.effective_soc_shortage_coefficient, item.lambda_soc * 200.0) for item in selected)
