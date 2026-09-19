from __future__ import annotations

"""Deterministic integrity gate for the frozen 6-AGV pre-final package."""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent


def main() -> None:
    tuning = ROOT / "results" / "tuning"
    pre = ROOT / "results" / "pre_final"
    catalog = pd.read_csv(tuning / "rho_scenario_catalog.csv")
    c4 = json.loads((tuning / "frozen_c4_parameters.json").read_text(encoding="utf-8"))
    c5 = json.loads((pre / "frozen_c5_parameters.json").read_text(encoding="utf-8"))
    manifest = json.loads((pre / "frozen_experiment_manifest.json").read_text(encoding="utf-8"))
    c4_rows = pd.read_csv(tuning / "c4_local_refinement.csv")
    c5_rows = pd.read_csv(pre / "c5_revalidation_raw.csv")

    assert len(catalog) == 6
    assert (catalog["logistics_utilization"] < 1.0).all()
    expected_regions = {"non_binding", "near_transition", "transition", "moderately_constrained", "strongly_constrained"}
    actual = set(catalog[catalog.scenario.isin(["stress_non_binding", "stress_near_transition", "stress_transition", "primary", "stress_strongly_constrained"])].rho_region)
    assert actual == expected_regions
    primary = catalog[catalog.scenario == "primary"].iloc[0]
    assert int(primary.n_agvs) == 6 and abs(primary.rho_analytical - 1.009449) < 0.01 and abs(primary.logistics_utilization - 0.875) < 0.01
    assert c4["weights"] == {"soc": 0.75, "next_task_energy": 0.0, "idle": 0.0, "deadline": 0.25}
    assert set(c4_rows.groupby(["weight_id", "scenario"]).size()) == {50}
    assert len(c5_rows) == 1750 and set(c5_rows.groupby(["scale_id", "scenario"]).size()) == {50}
    assert c5_rows.simulation_failure.sum() == 0 and c5_rows.low_soc_stops.sum() == 0 and c5_rows.solver_infeasible_calls.sum() == 0
    assert c5["scales"] == {"lambda_soc": 2.0, "lambda_task": 1.5, "lambda_kpi": 2.0}
    assert manifest["seed_overlap"] == 0 and manifest["planned_final_seeds"] == list(range(6007, 6057))
    assert not manifest["final_evaluation_executed"] and not manifest["final_figures_generated"]
    print("PRE_FINAL_INTEGRITY_OK")


if __name__ == "__main__":
    main()
