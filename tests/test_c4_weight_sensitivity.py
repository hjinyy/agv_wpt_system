from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from run_c4_weight_sensitivity import SensitivityResult, generate_weight_combinations, pareto_results


def test_weight_grid_contains_only_valid_normalized_combinations():
    combinations = generate_weight_combinations()

    assert len(combinations) == 26
    assert [(item.w1, item.w5) for item in combinations[:5]] == [
        (0.1, 0.1),
        (0.1, 0.2),
        (0.1, 0.3),
        (0.1, 0.4),
        (0.1, 0.5),
    ]
    assert all(item.w1 + item.w5 <= 0.8 + 1e-12 for item in combinations)
    assert all(np.isclose(sum(item.weights.values()), 1.0) for item in combinations)


def test_pareto_results_excludes_combinations_dominated_on_both_metrics():
    results = [
        SensitivityResult(0.1, 0.4, 0.24, 0.16, 0.1, 4.0, 90.0, 0.2, 1.0),
        SensitivityResult(0.2, 0.35, 0.21, 0.14, 0.1, 5.0, 88.0, 0.3, 1.1),
        SensitivityResult(0.3, 0.3, 0.18, 0.12, 0.1, 3.0, 85.0, 0.4, 1.2),
    ]

    pareto = pareto_results(results)

    assert [(item.w1, item.w5) for item in pareto] == [(0.1, 0.1), (0.3, 0.1)]
