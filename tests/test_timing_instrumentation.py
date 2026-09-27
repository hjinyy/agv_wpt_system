from rho_pipeline import FourFeatureC4Sim, configuration_for, scenarios
from v2_runner import generate_common

def test_c4_timing_hook_preserves_deterministic_schedule_metrics():
    sc=scenarios()['near_boundary_moderate']; w={'soc':.75,'next_task_energy':0.,'idle':0.,'charging_power_quality':0.,'deadline':.25}; cfg=configuration_for(sc,w); tasks,initial=generate_common(cfg,7067,distances=sc.distances,urgent_ratio=sc.urgent_ratio); lookup={t.task_id:i for i,t in enumerate(tasks)}
    def run():
        sim=FourFeatureC4Sim(cfg,'C4',7067,tasks,initial,'timing',variable_eta=True,task_index_lookup=lookup,predicted_eta_mode='predicted',realized_eta_mode='realized',current_distances=sc.distances_m); return sim.run()
    a,b=run(),run()
    for key in ('mean_delay','urgent_on_time_rate','completion_rate','low_soc_stops','fleet_min_soc'): assert a[key]==b[key]
    assert a['priority_decisions']>0 and a['total_priority_computation_time_s']>=0
