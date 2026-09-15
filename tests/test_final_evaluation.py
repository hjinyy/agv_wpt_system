from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import csv

import pandas as pd

from final_evaluation import (
    C4_FINAL_WEIGHTS,
    C5_FINAL_SCALES,
    FINAL_EVALUATION_SEEDS,
    TUNING_SEEDS,
    final_configuration,
    _write_csv,
)
import generate_final_figures as figures


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


def test_urgent_on_time_is_not_applicable_to_base_case_without_urgent_tasks():
    assert not figures._is_urgent_on_time_applicable("Base Case")
    assert figures._is_urgent_on_time_applicable("Primary Challenge")


def test_base_primary_figure_renders_without_an_urgent_base_case_metric(tmp_path, monkeypatch):
    base = pd.DataFrame({"strategy": ["C1", "C2", "C3", "C4", "C5"], "mean_delay": [1, 2, 3, 4, 5], "completion_rate": [99, 99, 99, 99, 99]})
    primary = pd.DataFrame({"strategy": ["C1", "C2", "C3", "C4", "C5"], "mean_delay": [1, 2, 3, 4, 5], "urgent_on_time_rate": [50, 60, 70, 80, 90]})
    monkeypatch.setattr(figures, "FIGURES", tmp_path)

    figures._base_primary_figure(base, primary)

    assert (tmp_path / "Figure1_Final_Base_Primary.png").is_file()


def test_figure6_boxplot_writes_exact_50_replication_plot_data(tmp_path, monkeypatch):
    primary = pd.DataFrame(
        {
            "strategy": [strategy for strategy in ("C1", "C2", "C3", "C4", "C5") for _ in range(50)],
            "replication": [replication for _ in ("C1", "C2", "C3", "C4", "C5") for replication in range(4007, 4057)],
            "mean_delay": [float(replication % 11) for _ in ("C1", "C2", "C3", "C4", "C5") for replication in range(4007, 4057)],
        }
    )
    monkeypatch.setattr(figures, "FIGURES", tmp_path)

    figures._uncertainty_figure(primary)

    plot_data = pd.read_csv(tmp_path / "Figure6_Final_Replication_Uncertainty_data.csv")
    pd.testing.assert_frame_equal(plot_data, primary)
    assert (tmp_path / "Figure6_Final_Replication_Uncertainty.png").is_file()
    assert (tmp_path / "Figure6_Final_Replication_Uncertainty.pdf").is_file()
