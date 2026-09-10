from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from boundary_closure_analysis import (
    c4_lower_boundary_parameters,
    c5_lower_boundary_parameters,
    choose_boundary_candidate,
)
from parameter_refinement_analysis import Aggregate, C4Parameters, C5Parameters, PairedStatistics


def _aggregate(parameters: C4Parameters | C5Parameters, delay: float, urgent: float) -> Aggregate:
    return Aggregate(parameters, delay, 0.1, urgent, 0.1, 100.0, 1.0, 25.0, 0, 0, 0.0, 0.0, 0, 0, 0)


def _paired(metric: str, low: float, high: float) -> PairedStatistics:
    return PairedStatistics("candidate_minus_baseline", metric, 0.0, 0.0, 0.1, low, high, low, high, 50.0, 50)


def test_lower_boundary_parameter_sets_include_the_current_candidates():
    c4_parameters = c4_lower_boundary_parameters()
    c5_parameters = c5_lower_boundary_parameters()

    assert [item.w5 for item in c4_parameters] == [0.0, 0.05, 0.1, 0.15]
    assert C4Parameters(0.55, 0.175, 0.105, 0.07, 0.10) in c4_parameters
    assert all(abs(sum(item.weights.values()) - 1.0) < 1e-12 for item in c4_parameters)
    assert C5Parameters(2.0, 1.5, 1.5) in c5_parameters
    assert len(c5_parameters) == 5


def test_boundary_selection_replaces_only_when_both_paired_intervals_support_improvement():
    baseline = _aggregate(C5Parameters(2.0, 1.5, 1.5), 10.0, 80.0)
    supported = _aggregate(C5Parameters(2.0, 1.25, 1.5), 9.0, 81.0)
    uncertain = _aggregate(C5Parameters(2.0, 1.5, 1.25), 8.0, 82.0)
    comparisons = {
        supported.parameters: [_paired("mean_delay", -2.0, -0.1), _paired("urgent_on_time_rate", 0.1, 3.0)],
        uncertain.parameters: [_paired("mean_delay", -3.0, -0.1), _paired("urgent_on_time_rate", -0.5, 4.0)],
    }

    selected = choose_boundary_candidate(baseline, [baseline, supported, uncertain], comparisons)

    assert selected == supported
