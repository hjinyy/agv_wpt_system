from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from v2_runner import load_cfg, generate_common
from v3_runner import V3Sim, run_v3_set


def test_v3_c4_preview_features_have_task_variance():
    cfg = load_cfg()
    cfg.update({'n_agvs': 5, 'n_pads': 1, 'task_arrival_rate_per_h': 90, 'wpt_power_kw': 3})
    distances = {1: 20, 2: 25, 3: 30, 4: 35, 5: 40}
    tasks, init = generate_common(cfg, cfg['seed0'], distances=distances, urgent_ratio=0.2)
    lookup = {t.task_id: i for i, t in enumerate(tasks)}
    sim = V3Sim(cfg, 'C4', cfg['seed0'], tasks, init, 'unit', variable_eta=True, task_index_lookup=lookup)
    cands = sim.agvs[:4]
    mapping = sim.preview_task_map(cands, 0.0, tasks[0])
    raw_e = [sim.features(a, 0.0, mapping[a.agv_id], sim.eta(mapping[a.agv_id], a))['raw_E_next_kwh'] for a in cands]
    assert len(set(round(x, 8) for x in raw_e)) > 1


def test_v3_c5_debug_runs_and_records_solver_stats():
    cfg = load_cfg()
    cfg.update({'operation_hours': 0.25, 'n_agvs': 2, 'n_pads': 1, 'task_arrival_rate_per_h': 20})
    distances = {i: cfg['picking_staging_distance_m'] for i in range(1, cfg['n_picking_points'] + 1)}
    outs, *_rest, solver, sched = run_v3_set(cfg, 'unit_short', cfg['seed0'], distances, urgent_ratio=0.1)
    c5 = [o for o in outs if o['strategy'] == 'C5'][0]
    assert c5['solver_calls'] >= 0
    assert c5['solver_computation_time_s'] >= 0
    assert isinstance(solver, list)
    assert isinstance(sched, list)
