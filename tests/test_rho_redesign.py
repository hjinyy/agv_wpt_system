import math
from simulation.literature_wpt import condition_at_delta, distribution_moments, measurement_table
from rho_pipeline import FEATURES, FourFeatureC4Sim, configuration_for, load_experiment_config, scenario_catalog_rows, scenarios, tuning_seeds
from run_rho_tuning import simplex_grid
from v2_runner import generate_common, task_time

def weights(): return {"soc": .75, "next_task_energy": 0., "idle": 0., "charging_power_quality": 0., "deadline": .25}

def test_literature_table_xy_averages_and_normalized_power():
    table=measurement_table()
    row=table[table.delta_mm==100].iloc[0]
    assert math.isclose(row.eta_mean_percent,(72.53+74.92)/2,rel_tol=0,abs_tol=1e-12)
    assert math.isclose(row.g_power,1.205/2.495,rel_tol=0,abs_tol=1e-12)
    assert math.isclose(row.p_charge_kw,3*(1.205/2.495),rel_tol=0,abs_tol=1e-12)
    assert math.isclose(condition_at_delta(0).charge_power_kw,3.0,rel_tol=0,abs_tol=1e-12)

def test_c4_power_feature_uses_predicted_not_realized_condition():
    scenario=scenarios()["near_boundary_moderate"]; cfg=configuration_for(scenario,weights())
    tasks,initial=generate_common(cfg,7067,distances=scenario.distances,urgent_ratio=scenario.urgent_ratio)
    lookup={task.task_id:index for index,task in enumerate(tasks)}
    sim=FourFeatureC4Sim(cfg,"C4",7067,tasks,initial,"unit",variable_eta=True,task_index_lookup=lookup,current_distances=scenario.distances_m)
    task=tasks[0]; task.realized_eta_state=7
    feature=sim.four_features(sim.agvs[0],0.,task,pad_id=1)
    assert feature['predicted_charge_power_kw']==condition_at_delta([0,50,100,150,200,250,300,350][task.eta_state]).charge_power_kw
    assert 'f_P' in feature and 0<=feature['f_P']<=1

def test_catalog_is_controlled_alignment_grid_and_logistically_feasible():
    data=load_experiment_config(); rows={row['scenario']:row for row in scenario_catalog_rows(data)}
    assert set(data['tuning_scenarios'])==set(rows)
    assert all(float(row['logistics_utilization'])<1 for row in rows.values())
    assert rows['near_boundary_good']['physical_condition']=='good'
    assert rows['near_boundary_severe']['physical_condition']=='severe'
    assert rows['near_boundary_severe']['rho_analytical']>rows['near_boundary_good']['rho_analytical']

def test_deadline_rule_exceeds_minimum_service_time():
    scenario=scenarios()['near_boundary_good']; cfg=configuration_for(scenario,weights())
    for distance in scenario.distances_m:
        service=task_time(cfg,distance)
        assert service+cfg['deadline_model']['urgent_slack_s']>service

def test_new_tuning_and_unseen_seed_blocks_are_disjoint_and_unused_by_catalog():
    seeds=tuning_seeds(); assert seeds==tuple(range(7007,7057)); assert len(seeds)==50
    assert not set(seeds)&set(range(5007,5057)); assert not set(seeds)&set(range(6007,6057)); assert not set(seeds)&set(range(8007,8057))

def test_coarse_five_feature_simplex_has_70_candidates():
    candidates=simplex_grid(.25); assert len(candidates)==70
    assert all(set(c)==set(FEATURES) and abs(sum(c.values())-1)<1e-12 and all(v>=0 for v in c.values()) for c in candidates)
