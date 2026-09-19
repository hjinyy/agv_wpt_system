import v2_runner, v3_runner
from rho_pipeline import FourFeatureC4Sim, configuration_for, scenarios
from simulation.final_wpt import physical_efficiency_values
from v2_runner import generate_common

def test_c4_timing_hook_preserves_deterministic_schedule_metrics(monkeypatch):
    monkeypatch.setattr(v2_runner, 'eta_values', physical_efficiency_values)
    monkeypatch.setattr(v3_runner, 'eta_values', physical_efficiency_values)
    sc=scenarios()['primary']; w={'soc':.75,'next_task_energy':0.,'idle':0.,'deadline':.25}; cfg=configuration_for(sc,w); tasks,initial=generate_common(cfg,5007,distances=sc.distances,urgent_ratio=sc.urgent_ratio); lookup={t.task_id:i for i,t in enumerate(tasks)}
    def run():
        sim=FourFeatureC4Sim(cfg,'C4',5007,tasks,initial,'timing',variable_eta=True,task_index_lookup=lookup,predicted_eta_mode='variable',realized_eta_mode='variable',current_distances=sc.distances_m); return sim.run()
    a,b=run(),run()
    for key in ('mean_delay','urgent_on_time_rate','completion_rate','low_soc_stops','fleet_min_soc'): assert a[key]==b[key]
    assert a['priority_decisions']>0 and a['total_priority_computation_time_s']>=0
