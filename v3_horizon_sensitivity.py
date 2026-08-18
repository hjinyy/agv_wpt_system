from __future__ import annotations
from pathlib import Path
import pandas as pd

from v2_runner import load_cfg, generate_common
from v3_runner import RESULTS, V3Sim


def run_horizon_sensitivity(debug: bool = False):
    RESULTS.mkdir(exist_ok=True)
    cfg = load_cfg()
    cfg.update({'n_agvs': 5, 'n_pads': 1, 'task_arrival_rate_per_h': 90, 'wpt_power_kw': 3})
    distances = {1: 20, 2: 25, 3: 30, 4: 35, 5: 40}
    horizons = [300, 900, 1800]
    reps = 1 if debug else 5
    rows = []
    for h in horizons:
        cfg_h = dict(cfg)
        cfg_h['c5_horizon_s'] = h
        cfg_h['c5_slot_s'] = 60
        cfg_h['c5_time_limit_s'] = 5.0
        for r in range(reps):
            seed = cfg['seed0'] + r
            tasks, init = generate_common(cfg_h, seed, distances=distances, urgent_ratio=0.2)
            lookup = {t.task_id: i for i, t in enumerate(tasks)}
            sim = V3Sim(cfg_h, 'C5', seed, tasks, init, f'horizon_{h}s', variable_eta=True,
                        task_index_lookup=lookup, predicted_eta_mode='variable', realized_eta_mode='variable')
            out = sim.run()
            out.update({'horizon_s': h, 'horizon_min': h / 60, 'slot_s': 60})
            rows.append(out)
            print(f'horizon {h}s rep {r+1}/{reps} done')
    df = pd.DataFrame(rows)
    df.to_csv(RESULTS / 'horizon_sensitivity.csv', index=False)
    return df


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--debug', action='store_true')
    args = ap.parse_args()
    run_horizon_sensitivity(debug=args.debug)
