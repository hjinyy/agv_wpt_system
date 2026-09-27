from run_c5_revalidation import oat_candidates
from rho_pipeline import load_experiment_config

def test_c5_oat_refinement_has_reference_plus_six_local_candidates():
 data=load_experiment_config();candidates=oat_candidates(data);assert len(candidates)==7

def test_final_seed_block_is_disjoint_from_tuning_block():
 data=load_experiment_config();tuning=set(range(data['seeds']['tuning_start'],data['seeds']['tuning_end']+1));final=set(range(data['seeds']['reserved_final_start'],data['seeds']['reserved_final_end']+1));assert tuning.isdisjoint(final) and tuning==set(range(7107,7157)) and final==set(range(8007,8057))
