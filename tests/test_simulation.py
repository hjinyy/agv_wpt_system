import yaml
from simulation.environment import WPTAGVSimulation, common_random_inputs

def cfg():
    raw=yaml.safe_load(open('config.yaml'))
    c=raw['base']; c['weights']=raw['weights']; c['efficiency_states']=raw['efficiency_states']; c['_raw']=raw
    c['operation_hours']=1; c['task_arrival_rate_per_h']=20; c['replications']=2
    return c

def test_common_random_numbers_and_run():
    c=cfg(); tasks,init,etas=common_random_inputs(c,1007)
    assert len(tasks)>0 and len(init)==c['n_agvs'] and len(etas)==len(tasks)
    m=[]
    for st in ['C1','C2','C3','C4']:
        sim=WPTAGVSimulation(c,st,1007,tasks=tasks,init_socs=init,eta_states=etas,label='test:x')
        out=sim.run(); m.append(out)
        assert out['requested_tasks']==len(tasks)
        assert 0 <= out['completed_tasks'] <= len(tasks)
        assert out['fleet_min_soc'] <= 90
    assert len({x['requested_tasks'] for x in m})==1

def test_pad_capacity_metrics():
    c=cfg(); c['n_pads']=1; c['wpt_power_kw']=1
    sim=WPTAGVSimulation(c,'C2',42,label='test:pad')
    out=sim.run()
    assert out['pad_utilization'] >= 0
    assert out['detour_distance_m'] >= 0
