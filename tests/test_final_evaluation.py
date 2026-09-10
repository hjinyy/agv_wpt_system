from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import csv

from final_evaluation import (
    C4_FINAL_WEIGHTS,
    C5_FINAL_SCALES,
    FINAL_EVALUATION_SEEDS,
    TUNING_SEEDS,
    final_configuration,
    _write_csv,
)


def test_final_configuration_freezes_parameters_and_uses_independent_seeds():
    configuration = final_configuration()

    assert configuration["weights"] == C4_FINAL_WEIGHTS
    assert tuple(configuration[key] for key in ("c5_lambda_soc", "c5_lambda_task", "c5_lambda_kpi")) == C5_FINAL_SCALES
    assert len(FINAL_EVALUATION_SEEDS) == 50
    assert not set(FINAL_EVALUATION_SEEDS).intersection(TUNING_SEEDS)


def test_csv_writer_preserves_c5_only_solver_columns_when_c1_row_is_first(tmp_path):
    path = tmp_path / "metrics.csv"

    _write_csv(path, [{"strategy": "C1", "mean_delay": 1.0}, {"strategy": "C5", "mean_delay": 1.0, "solver_calls": 3}])

    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[1]["solver_calls"] == "3"
