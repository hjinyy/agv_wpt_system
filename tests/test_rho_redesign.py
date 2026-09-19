from rho_pipeline import FEATURES, FourFeatureC4Sim, configuration_for, load_experiment_config, scenario_catalog_rows, scenarios, tuning_seeds
from run_rho_tuning import simplex_grid
from v2_runner import generate_common


def test_four_feature_c4_score_is_eta_independent():
    scenario = scenarios()["primary"]
    configuration = configuration_for(scenario, {"soc": 0.75, "next_task_energy": 0.0, "idle": 0.0, "deadline": 0.25})
    tasks, initial_soc = generate_common(configuration, 5007, distances=scenario.distances, urgent_ratio=scenario.urgent_ratio)
    lookup = {task.task_id: index for index, task in enumerate(tasks)}
    simulation = FourFeatureC4Sim(configuration, "C4", 5007, tasks, initial_soc, "unit", variable_eta=True, task_index_lookup=lookup, current_distances=scenario.distances_m)

    low_eta = simulation.features(simulation.agvs[0], 0.0, tasks[0], eta=0.1)
    high_eta = simulation.features(simulation.agvs[0], 0.0, tasks[0], eta=0.99)

    assert low_eta["score"] == high_eta["score"]
    assert "eta_WPT" not in low_eta


def test_rho_catalog_covers_each_requested_operating_region():
    data = load_experiment_config()
    rows = {row["scenario"]: row for row in scenario_catalog_rows(data)}
    regions = {rows[name]["rho_region"] for name in data["tuning_scenarios"]}

    assert {"non_binding", "near_transition", "transition", "moderately_constrained", "strongly_constrained"}.issubset(regions)
    assert 1.0 <= float(rows["primary"]["rho_analytical"]) <= 1.2
    assert rows["primary"]["rho_region"] == "moderately_constrained"
    assert all(float(row["logistics_utilization"]) < 1.0 for row in rows.values())


def test_tuning_seed_block_is_new_and_has_50_replications():
    seeds = tuning_seeds()

    assert seeds == tuple(range(5007, 5057))
    assert len(seeds) == 50
    assert not set(seeds).intersection(range(4007, 4057))


def test_coarse_c4_four_feature_simplex_has_35_valid_candidates():
    candidates = simplex_grid(0.25)

    assert len(candidates) == 35
    assert all(set(candidate) == set(FEATURES) for candidate in candidates)
    assert all(abs(sum(candidate.values()) - 1.0) < 1e-12 for candidate in candidates)
    assert all(all(weight >= 0.0 for weight in candidate.values()) for candidate in candidates)
