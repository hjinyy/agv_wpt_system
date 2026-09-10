from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from parameter_refinement_analysis import (
    C4Parameters,
    C5Parameters,
    Aggregate,
    c4_local_parameters,
    c5_oat_parameters,
    is_joint_kpi_leader,
)


def aggregate(parameters: C4Parameters | C5Parameters, delay: float, urgent: float) -> Aggregate:
    return Aggregate(parameters, delay, 0.1, urgent, 0.1, 100.0, 1.0, 25.0, 0, 0, 0.0, 0.0, 0, 0, 0)


def test_c4_local_grid_preserves_residual_ratio_and_includes_old_candidate():
    parameters = c4_local_parameters()

    assert len(parameters) == 22
    assert C4Parameters(0.60, 0.10, 0.06, 0.04, 0.20) in parameters
    assert all(abs(sum(item.weights.values()) - 1.0) < 1e-12 for item in parameters)
    assert all(item.w1 + item.w5 <= 0.90 + 1e-12 for item in parameters)


def test_c5_oat_grid_has_one_baseline_and_single_factor_offsets():
    parameters = c5_oat_parameters(2.0)

    assert len(parameters) == 7
    assert C5Parameters(2.0, 2.0, 2.0) in parameters
    assert C5Parameters(1.5, 2.0, 2.0) in parameters
    assert C5Parameters(2.0, 2.5, 2.0) in parameters
    assert C5Parameters(2.0, 2.0, 2.5) in parameters


def test_boundary_leader_requires_best_delay_and_best_urgent_rate():
    leader = aggregate(C5Parameters(4.0, 4.0, 4.0), 4.0, 92.0)
    other = aggregate(C5Parameters(3.0, 3.0, 3.0), 5.0, 91.0)
    tradeoff = aggregate(C5Parameters(2.0, 2.0, 2.0), 3.0, 90.0)

    assert is_joint_kpi_leader(leader, [leader, other])
    assert not is_joint_kpi_leader(leader, [leader, tradeoff])
