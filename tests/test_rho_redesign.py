import math
from simulation.literature_wpt import condition_at_delta, measurement_table
from rho_pipeline import FEATURES, FourFeatureC4Sim, configuration_for, load_experiment_config, scenario_catalog_rows, scenarios, tuning_seeds
from run_rho_tuning import simplex_grid
from v2_runner import generate_common, task_time

def weights(): return {'soc':.75,'next_task_energy':0.,'idle':0.,'charging_power_quality':0.,'deadline':.25}
def test_literature_table_xy_averages_and_normalized_power():
 table=measurement_table();row=table[table.delta_mm==100].iloc[0]
 assert math.isclose(row.eta_mean_percent,(72.53+74.92)/2,abs_tol=1e-12)
 assert math.isclose(row.g_power,1.205/2.495,abs_tol=1e-12)
 assert math.isclose(row.p_charge_kw,3*(1.205/2.495),abs_tol=1e-12)
 assert math.isclose(condition_at_delta(0).charge_power_kw,3.0,abs_tol=1e-12)
def test_c4_power_feature_uses_predicted_not_realized_condition():
 sc=scenarios()['moderately_constrained_moderate'];cfg=configuration_for(sc,weights());tasks,initial=generate_common(cfg,7067,distances=sc.distances,urgent_ratio=sc.urgent_ratio);lookup={t.task_id:i for i,t in enumerate(tasks)};sim=FourFeatureC4Sim(cfg,'C4',7067,tasks,initial,'unit',variable_eta=True,task_index_lookup=lookup,current_distances=sc.distances_m);task=tasks[0];task.realized_eta_state=7;f=sim.four_features(sim.agvs[0],0.,task,pad_id=1)
 assert f['predicted_charge_power_kw']==condition_at_delta([0,50,100,150,200,250,300,350][task.eta_state]).charge_power_kw and 0<=f['f_P']<=1
def test_c4_feature_signs_and_weight_constraints():
 sc=scenarios()['moderately_constrained_moderate'];cfg=configuration_for(sc,weights());tasks,initial=generate_common(cfg,7067,distances=sc.distances,urgent_ratio=sc.urgent_ratio);sim=FourFeatureC4Sim(cfg,'C4',7067,tasks,initial,'unit',variable_eta=True,task_index_lookup={t.task_id:i for i,t in enumerate(tasks)},current_distances=sc.distances_m);f=sim.four_features(sim.agvs[0],0,tasks[0]);assert cfg['c4_five_feature_weights']['deadline']>=0 and abs(sum(cfg['c4_five_feature_weights'].values())-1)<1e-12 and f['score']==weights()['soc']*f['f_SOC']+weights()['next_task_energy']*f['f_E']+weights()['idle']*f['f_idle']+weights()['charging_power_quality']*f['f_P']-weights()['deadline']*f['f_D']
def test_catalog_taxonomy_names_and_logistics_feasibility():
 rows={r['scenario']:r for r in scenario_catalog_rows()};assert all(float(r['logistics_utilization'])<1 for r in rows.values());assert rows['non_binding_good']['rho_region']=='non_binding';assert rows['near_transition_good']['rho_region']=='near_transition';assert rows['moderately_constrained_moderate']['rho_region']=='moderately_constrained';assert rows['strongly_constrained_severe']['rho_region']=='strongly_constrained'
def test_deadline_rule_exceeds_minimum_service_time():
 sc=scenarios()['near_transition_good'];cfg=configuration_for(sc,weights());assert all(task_time(cfg,d)+cfg['deadline_model']['urgent_slack_s']>task_time(cfg,d) for d in sc.distances_m)
def test_seed_blocks_are_disjoint():
 data=load_experiment_config();seeds=tuning_seeds();final=range(data['seeds']['reserved_final_start'],data['seeds']['reserved_final_end']+1);assert seeds==tuple(range(7107,7157)) and len(seeds)==50 and not set(seeds)&set(final) and not set(seeds)&set(range(5007,5057)) and not set(seeds)&set(range(6007,6057))
def test_coarse_five_feature_simplex_has_70_candidates():
 c=simplex_grid(.25);assert len(c)==70 and all(set(x)==set(FEATURES) and abs(sum(x.values())-1)<1e-12 and all(v>=0 for v in x.values()) for x in c)
