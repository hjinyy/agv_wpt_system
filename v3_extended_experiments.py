from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np

from v2_runner import load_cfg, generate_common
from v3_runner import V3Sim, append_csv

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'results_v3'

BASE_STRATEGIES = ['C1', 'C2', 'C3', 'C4', 'C5']
STRESS_STRATEGIES = ['C1', 'C2', 'C3', 'C4']  # C5 kept to primary/base only to avoid 24h MILP grid explosion.


def run_strategies(cfg, label, seed, distances, urgent_ratio, strategies):
    tasks, init = generate_common(cfg, seed, distances=distances, urgent_ratio=urgent_ratio)
    lookup = {t.task_id: i for i, t in enumerate(tasks)}
    outs=[]; feat=[]; dec=[]; solver=[]; sched=[]
    for st in strategies:
        sim = V3Sim(cfg, st, seed, tasks, init, label, variable_eta=True,
                    task_index_lookup=lookup, predicted_eta_mode='variable', realized_eta_mode='variable')
        outs.append(sim.run())
        feat += sim.feature_rows
        dec += sim.decision_rows
        solver += sim.solver_rows
        sched += sim.milp_schedule_rows
    return outs, feat, dec, solver, sched


def main(debug=False):
    OUT.mkdir(exist_ok=True)
    for name in ['base_case_runs.csv', 'stress_grid.csv', 'base_solver_statistics.csv',
                 'base_milp_schedule.csv', 'stress_decision_diagnostics.csv',
                 'stress_priority_features_raw.csv']:
        p = OUT / name
        if p.exists():
            p.unlink()
    reps = 2 if debug else 50
    seed0 = load_cfg()['seed0']

    # V3 Base Case: original homogeneous base, C1-C5.
    base_cfg = load_cfg()
    base_dist = {i: base_cfg['picking_staging_distance_m'] for i in range(1, base_cfg['n_picking_points'] + 1)}
    base_rows=[]; base_solver=[]; base_sched=[]
    for r in range(reps):
        outs, feat, dec, solver, sched = run_strategies(base_cfg, 'v3_base', seed0 + r, base_dist, urgent_ratio=0.0, strategies=BASE_STRATEGIES)
        append_csv(OUT / 'base_case_runs.csv', outs)
        append_csv(OUT / 'base_solver_statistics.csv', solver)
        append_csv(OUT / 'base_milp_schedule.csv', sched)
        base_rows += outs; base_solver += solver; base_sched += sched
        print(f'V3 base {r+1}/{reps} done')
    pd.DataFrame(base_rows).to_csv(OUT / 'base_case_runs.csv', index=False)
    pd.DataFrame(base_solver).to_csv(OUT / 'base_solver_statistics.csv', index=False)
    pd.DataFrame(base_sched).to_csv(OUT / 'base_milp_schedule.csv', index=False)

    # V3 stress grid for C4-vs-C3 region: corrected C4 only, C1-C4, all 50 CRN reps.
    workloads = [75, 90, 105]
    pads = [1, 2]
    powers = [1, 3, 5]
    dist = {1:20, 2:25, 3:30, 4:35, 5:40}
    stress_rows=[]; stress_feat=[]; stress_dec=[]
    total = len(workloads) * len(pads) * len(powers) * reps
    k = 0
    for wl in workloads:
        for npad in pads:
            for pw in powers:
                cfg = load_cfg()
                cfg.update({'n_agvs': 5, 'n_pads': npad, 'task_arrival_rate_per_h': wl, 'wpt_power_kw': pw})
                label = f'v3_stress_w{wl}_p{npad}_kw{pw}'
                for r in range(reps):
                    k += 1
                    outs, feat, dec, solver, sched = run_strategies(cfg, label, seed0 + r, dist, urgent_ratio=0.2, strategies=STRESS_STRATEGIES)
                    for o in outs:
                        o.update({'workload': wl, 'n_pads': npad, 'wpt_power_kw': pw})
                    append_csv(OUT / 'stress_grid.csv', outs)
                    append_csv(OUT / 'stress_priority_features_raw.csv', feat)
                    append_csv(OUT / 'stress_decision_diagnostics.csv', dec)
                    stress_rows += outs; stress_feat += feat; stress_dec += dec
                    if k % 25 == 0:
                        print(f'V3 stress {k}/{total} rep-scenarios done')
    pd.DataFrame(stress_rows).to_csv(OUT / 'stress_grid.csv', index=False)
    pd.DataFrame(stress_feat).to_csv(OUT / 'stress_priority_features_raw.csv', index=False)
    pd.DataFrame(stress_dec).to_csv(OUT / 'stress_decision_diagnostics.csv', index=False)
    print(f'Wrote V3 extended experiments to {OUT}')

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--debug', action='store_true')
    args = ap.parse_args()
    main(debug=args.debug)
