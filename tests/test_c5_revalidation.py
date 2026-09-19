from run_c5_revalidation import oat_candidates
from rho_pipeline import load_experiment_config


def test_c5_oat_refinement_has_reference_plus_six_local_candidates():
    data = load_experiment_config()
    candidates = oat_candidates(data)
    assert len(candidates) == 7
    assert {tuple(candidate.values()) for candidate in candidates} == {
        (2.0, 1.5, 1.5), (1.5, 1.5, 1.5), (2.5, 1.5, 1.5),
        (2.0, 1.0, 1.5), (2.0, 2.0, 1.5), (2.0, 1.5, 1.0), (2.0, 1.5, 2.0),
    }


def test_final_seed_block_is_disjoint_from_tuning_block():
    data = load_experiment_config()
    tuning = set(range(data['seeds']['tuning_start'], data['seeds']['tuning_end'] + 1))
    final = set(range(data['seeds']['planned_final_start'], data['seeds']['planned_final_end'] + 1))
    assert tuning.isdisjoint(final)
