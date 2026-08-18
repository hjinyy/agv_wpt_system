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


def test_v3_c1_revised_baseline_metadata_is_recorded():
    cfg = load_cfg()
    cfg.update({'operation_hours': 0.25, 'n_agvs': 2, 'n_pads': 1, 'task_arrival_rate_per_h': 20})
    distances = {i: cfg['picking_staging_distance_m'] for i in range(1, cfg['n_picking_points'] + 1)}
    tasks, init = generate_common(cfg, cfg['seed0'], distances=distances, urgent_ratio=0.0)
    lookup = {t.task_id: i for i, t in enumerate(tasks)}
    sim = V3Sim(cfg, 'C1', cfg['seed0'], tasks, init, 'unit_c1', variable_eta=True, task_index_lookup=lookup)
    out = sim.run()
    assert out['c1_start_soc'] == 0.30
    assert out['c1_target_soc'] == 0.70


def test_v3_c5_uses_15_min_rolling_horizon_and_records_solver_stats():
    cfg = load_cfg()
    cfg.update({'operation_hours': 0.25, 'n_agvs': 2, 'n_pads': 1, 'task_arrival_rate_per_h': 20})
    distances = {i: cfg['picking_staging_distance_m'] for i in range(1, cfg['n_picking_points'] + 1)}
    outs, *_rest, solver, sched = run_v3_set(cfg, 'unit_short', cfg['seed0'], distances, urgent_ratio=0.1)
    c5 = [o for o in outs if o['strategy'] == 'C5'][0]
    assert c5['solver_calls'] >= 0
    assert c5['solver_computation_time_s'] >= 0
    assert isinstance(solver, list)
    assert isinstance(sched, list)
    assert solver
    first = solver[0]
    assert first['horizon_s'] == 900.0
    assert first['slot_s'] == 60.0
    assert first['n_slots'] == 15
    assert first['mode'] == '15min_rolling_horizon_milp'
    assert first['n_binary'] == first['candidate_agvs'] * first['available_pads'] * 15
    assert 'n_constraints' in first
    assert 'safety_slack_total' in first


def test_v3_c5_pad_capacity_and_first_slot_execution_metadata():
    cfg = load_cfg()
    cfg.update({'operation_hours': 0.25, 'n_agvs': 2, 'n_pads': 1, 'task_arrival_rate_per_h': 20})
    distances = {i: cfg['picking_staging_distance_m'] for i in range(1, cfg['n_picking_points'] + 1)}
    tasks, init = generate_common(cfg, cfg['seed0'], distances=distances, urgent_ratio=0.1)
    lookup = {t.task_id: i for i, t in enumerate(tasks)}
    sim = V3Sim(cfg, 'C5', cfg['seed0'], tasks, init, 'unit_c5', variable_eta=True, task_index_lookup=lookup,
                predicted_eta_mode='variable', realized_eta_mode='variable')
    for a in sim.agvs:
        a.soc = 0.10
    cands = sim.agvs[:2]
    preview = sim.preview_task_map(cands, 0.0, tasks[0])
    chosen, reason = sim.choose_c5_milp(cands, 0.0, tasks[0], 1, preview)
    assert reason == 'C5-15min-RH-MILP'
    assert len(chosen) <= 1
    assert sim.solver_rows[-1]['n_slots'] == 15
    first_slot_rows = [r for r in sim.milp_schedule_rows if r['slot_index'] == 1]
    assert len(first_slot_rows) <= 1
    assert all(r['execute_first_slot'] == 1 for r in first_slot_rows)
    for r in sim.milp_schedule_rows:
        assert 1 <= r['slot_index'] <= 15


def test_v3_c1_to_c4_short_regression_unchanged_by_c5_code():
    cfg = load_cfg()
    cfg.update({'operation_hours': 0.25, 'n_agvs': 2, 'n_pads': 1, 'task_arrival_rate_per_h': 20})
    distances = {i: cfg['picking_staging_distance_m'] for i in range(1, cfg['n_picking_points'] + 1)}
    outs, *_ = run_v3_set(cfg, 'unit_short_regression', cfg['seed0'], distances, urgent_ratio=0.1)
    expected = {
        'C1': (0.0, 100.0, 0.0),
        'C2': (0.0, 100.0, 0.059540),
        'C3': (0.0, 100.0, 0.059726),
        'C4': (0.0, 100.0, 0.059726),
    }
    for out in outs:
        if out['strategy'] in expected:
            delay, completion, loss = expected[out['strategy']]
            assert abs(out['mean_delay'] - delay) < 1e-6
            assert abs(out['completion_rate'] - completion) < 1e-6
            assert abs(out['wpt_loss'] - loss) < 1e-6
