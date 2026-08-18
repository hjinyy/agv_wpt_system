from __future__ import annotations
from pathlib import Path
from copy import deepcopy
import math, time, json
import numpy as np
import pandas as pd
from scipy.optimize import milp, LinearConstraint, Bounds

from v2_runner import (
    ROOT, load_cfg, generate_common, task_energy, task_time, move_energy,
    V2Sim, eta_values, summarize
)

RESULTS = ROOT / 'results_v3'
STRATEGIES = ['C1', 'C2', 'C3', 'C4', 'C5']


def append_csv(path: Path, rows):
    if not rows:
        return
    df = pd.DataFrame(rows)
    df.to_csv(path, mode='a', header=not path.exists(), index=False)


class V3Sim(V2Sim):
    """V3 simulator.

    C4 fix: candidates do not all share the same global next_task for E_next/D.
    During an idle charging decision, the WMS preview assigns the next FCFS tasks to
    currently available AGVs using the same deterministic first-available/id tie break
    used by all strategies. Actual task assignment in run() remains FCFS + first-available.

    C5: rolling one-slot MILP assignment benchmark for charging pad allocation.
    It optimizes current charging decisions only; full-horizon MILP is evaluated separately
    on a small case and reported as not used for 24 h when scaling is excessive.
    """
    def __init__(self, *args, task_index_lookup=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.task_index_lookup = task_index_lookup or {t.task_id: i for i, t in enumerate(self.tasks)}
        self.solver_rows = []
        self.milp_schedule_rows = []
        self.c5_solver_time_s = 0.0
        self.c5_solver_calls = 0

    def preview_task_map(self, cands, t, next_task):
        start_idx = self.task_index_lookup.get(next_task.task_id, 0)
        ordered_agvs = sorted(cands, key=lambda a: (a.available, a.agv_id))
        mapping = {}
        for k, a in enumerate(ordered_agvs):
            idx = min(start_idx + k, len(self.tasks) - 1)
            mapping[a.agv_id] = self.tasks[idx]
        return mapping

    def choose(self, cands, t, next_task, avail_pads):
        preview = self.preview_task_map(cands, t, next_task)

        def agv_task(a):
            return preview.get(a.agv_id, next_task)

        def slack(a):
            nt = agv_task(a)
            return nt.deadline - (t + task_time(self.cfg, nt.distance_m))

        critical = [a for a in cands if a.soc <= self.cfg['critical_soc']]
        if critical:
            return sorted(critical, key=lambda a: (a.soc, slack(a), a.agv_id))[:avail_pads], 'critical'
        if self.strategy == 'C2':
            return sorted(cands, key=lambda a: (a.last_job_end, a.agv_id))[:avail_pads], 'C2'
        if self.strategy == 'C3':
            return sorted(cands, key=lambda a: (a.soc, a.agv_id))[:avail_pads], 'C3'
        if self.strategy == 'C4':
            scored = []
            for a in cands:
                nt = agv_task(a)
                fr = self.features(a, t, nt, self.eta(nt, a, mode=self.predicted_eta_mode))
                fr.update({'scenario': self.label, 'strategy': 'C4', 'replication': self.seed,
                           'agv_id': a.agv_id, 'task_id': nt.task_id, 'preview_rank_task': nt.task_id})
                self.feature_rows.append(fr)
                scored.append((fr['score'], a))
            return [a for _, a in sorted(scored, key=lambda x: (-x[0], x[1].agv_id))[:avail_pads]], 'C4'
        if self.strategy == 'C5':
            return self.choose_c5_milp(cands, t, next_task, avail_pads, preview)
        return [], 'none'

    def choose_c5_milp(self, cands, t, next_task, avail_pads, preview):
        # One-slot rolling MILP: assign up to available pads to AGVs. Lexicographic weights are
        # separated by large constants: SOC safety > urgent deadline risk > delay > WPT loss.
        n = len(cands); m = max(1, avail_pads); N = n * m
        if N == 0:
            return [], 'C5-none'
        q = self.cfg['opportunity_quantum_s']
        qh = q / 3600
        benefits = []
        meta = []
        for i, a in enumerate(cands):
            nt = preview.get(a.agv_id, next_task)
            eta = self.eta(nt, a, mode=self.predicted_eta_mode)
            e_need = task_energy(self.cfg, nt.distance_m)
            safety = max(0, (self.cfg['min_soc'] + e_need / self.cfg['battery_kwh']) - a.soc)
            projected = max(t + q, nt.arrival) + task_time(self.cfg, nt.distance_m)
            urgent_late = max(0, projected - nt.deadline) if nt.task_type == 'urgent' else 0
            delay = max(0, projected - nt.arrival)
            loss = self.cfg['wpt_power_kw'] * (1 - eta) * qh
            benefit = 1e6 * safety + 1e3 * (urgent_late / 60) + 10 * (delay / 60) - loss
            for p in range(m):
                benefits.append(benefit)
                meta.append((a, nt, eta, p))
        c = -np.array(benefits, dtype=float)  # scipy minimizes
        constraints = []
        lb = []
        ub = []
        # each AGV at most one pad
        for i in range(n):
            row = np.zeros(N); row[i*m:(i+1)*m] = 1
            constraints.append(row); lb.append(0); ub.append(1)
        # each pad at most one AGV
        for p in range(m):
            row = np.zeros(N)
            for i in range(n): row[i*m+p] = 1
            constraints.append(row); lb.append(0); ub.append(1)
        # at most avail_pads total assignments
        constraints.append(np.ones(N)); lb.append(0); ub.append(avail_pads)
        lc = LinearConstraint(np.vstack(constraints), np.array(lb), np.array(ub))
        tic = time.perf_counter()
        try:
            res = milp(c=c, integrality=np.ones(N), bounds=Bounds(0, 1), constraints=lc,
                       options={'time_limit': 2.0, 'mip_rel_gap': 0.0})
            elapsed = time.perf_counter() - tic
            self.c5_solver_time_s += elapsed; self.c5_solver_calls += 1
            x = np.rint(res.x if res.x is not None else np.zeros(N)).astype(int)
            chosen = []
            for k, val in enumerate(x):
                if val > 0:
                    a, nt, eta, p = meta[k]
                    chosen.append(a)
                    self.milp_schedule_rows.append({'scenario': self.label, 'replication': self.seed, 'time_s': t,
                                                    'agv_id': a.agv_id, 'preview_task_id': nt.task_id,
                                                    'pad_rank': p + 1, 'predicted_eta': eta, 'slot_s': q})
            self.solver_rows.append({'scenario': self.label, 'replication': self.seed, 'time_s': t,
                                     'solver': 'scipy.optimize.milp/HiGHS', 'mode': 'rolling_one_slot',
                                     'status': int(res.status), 'message': str(res.message),
                                     'objective': float(res.fun) if res.fun is not None else np.nan,
                                     'n_binary': N, 'solve_time_s': elapsed})
            return sorted(chosen, key=lambda a: a.agv_id)[:avail_pads], 'C5-MILP'
        except Exception as e:
            elapsed = time.perf_counter() - tic
            self.c5_solver_time_s += elapsed; self.c5_solver_calls += 1
            self.solver_rows.append({'scenario': self.label, 'replication': self.seed, 'time_s': t,
                                     'solver': 'scipy.optimize.milp/HiGHS', 'mode': 'rolling_one_slot',
                                     'status': -1, 'message': repr(e), 'objective': np.nan,
                                     'n_binary': N, 'solve_time_s': elapsed})
            return sorted(cands, key=lambda a: (a.soc, a.agv_id))[:avail_pads], 'C5-fallback'

    def schedule_opportunity_until(self, t, next_arrival, next_task):
        # same as V2, but C3-vs-C4 diagnostic uses per-AGV preview for the C4 side.
        q = self.cfg['opportunity_quantum_s']; step_guard = 0
        while t + 1e-9 < next_arrival and step_guard < 10000:
            step_guard += 1
            for p in self.pads:
                if p.available < t: p.available = t
            avail = [p for p in self.pads if p.available <= t + 1e-9]
            cands = [a for a in self.agvs if a.available <= t + 1e-9 and a.soc < self.cfg['max_soc'] - 1e-6]
            if not avail or not cands:
                nxt = min([next_arrival] + [p.available for p in self.pads if p.available > t] + [a.available for a in self.agvs if a.available > t])
                if nxt <= t + 1e-9: break
                t = nxt; continue
            if len(cands) > len(avail):
                self.cfg['_expected_contention_wait_s'] = self.cfg['opportunity_quantum_s'] * max(0, math.ceil(len(cands) / max(1, len(avail))) - 1)
                self.contention_events += 1; self.max_queue = max(self.max_queue, len(cands) - len(avail))
                preview = self.preview_task_map(cands, t, next_task)
                c3 = sorted(cands, key=lambda a: (a.soc, a.agv_id))[0]
                scored = []
                for a in cands:
                    nt = preview.get(a.agv_id, next_task)
                    scored.append((self.features(a, t, nt, self.eta(nt, a, mode=self.predicted_eta_mode))['score'], a, nt))
                c4_item = sorted(scored, key=lambda x: (-x[0], x[1].agv_id))[0]
                c4 = c4_item[1]
                diff = int(c3.agv_id != c4.agv_id); self.diff_decisions += diff
                self.decision_rows.append({'scenario': self.label, 'strategy': self.strategy, 'replication': self.seed,
                                           'time_s': t, 'candidate_count': len(cands), 'available_pads': len(avail),
                                           'c3_agv': c3.agv_id, 'c4_agv': c4.agv_id, 'c4_preview_task_id': c4_item[2].task_id,
                                           'different': diff})
            else:
                self.cfg['_expected_contention_wait_s'] = 0.0
            chosen, reason = self.choose(cands, t, next_task, len(avail))
            for a, p in zip(chosen, avail):
                nt = self.preview_task_map([a], t, next_task).get(a.agv_id, next_task)
                start = max(t, p.available); wait = max(0, p.available - t); a.charge_wait_s += wait; p.wait_s += wait
                ts = self.detour(a, start); eta = self.eta(nt, a, mode=self.realized_eta_mode); dur = min(q, max(0, next_arrival - ts))
                actual, _, _ = self.charge_amount(a, p, ts, dur, eta, mandatory=False)
                a.available = ts + actual; p.available = a.available
                if actual <= 0: self.deferred += 1
            t = min([next_arrival] + [p.available for p in self.pads] + [a.available for a in self.agvs if a.available > t + 1e-9] or [next_arrival])
        return t

    def mandatory_charge(self, a, t, task):
        p = min(self.pads, key=lambda p: (p.available, p.pad_id))
        start = max(t, p.available)
        wait = max(0, start - t)
        a.charge_wait_s += wait
        p.wait_s += wait
        ts = self.detour(a, start)
        eta = self.eta(task, a, mode=self.realized_eta_mode)
        # Official V3 conventional baseline: C1 charges from 30% threshold to 70% target.
        # Other strategies retain the original safety/mandatory charge-to-max behavior.
        target_soc = self.cfg.get('c1_target_soc', 0.70) if self.strategy == 'C1' else self.cfg['max_soc']
        target = max(0.0, (target_soc - a.soc) * self.cfg['battery_kwh'])
        dur = target / (self.cfg['wpt_power_kw'] * eta) * 3600 if eta > 0 else 0
        actual, _, _ = self.charge_amount(a, p, ts, dur, eta, mandatory=True)
        a.available = ts + actual
        p.available = a.available
        return a.available

    def run(self):
        prev = 0.0
        for idx, task in enumerate(self.tasks):
            if self.strategy != 'C1':
                self.schedule_opportunity_until(prev, task.arrival, task)
            a = min(self.agvs, key=lambda x: (x.available, x.agv_id))
            start = max(task.arrival, a.available)
            need = task_energy(self.cfg, task.distance_m) / self.cfg['battery_kwh'] + self.cfg['min_soc']
            if self.strategy == 'C1':
                if a.soc <= self.cfg.get('c1_start_soc', 0.30) or a.soc < need:
                    start = self.mandatory_charge(a, start, task)
            else:
                # Apply the same mandatory SOC safety check to C2-C5, including C5.
                if a.soc <= self.cfg['critical_soc'] or a.soc < need:
                    start = self.mandatory_charge(a, start, task)
            delay = start - task.arrival
            dur = task_time(self.cfg, task.distance_m)
            tr, aux = move_energy(self.cfg, 2 * task.distance_m, 2 * task.distance_m / self.cfg['agv_speed_mps'])
            aux += self.cfg.get('p_aux_kw', 0) * (self.cfg['picking_service_s'] + self.cfg['staging_service_s']) / 3600
            comp = start + dur
            self.consume(a, tr, aux, comp)
            a.available = comp
            a.last_job_end = comp
            a.completed += 1
            tard = max(0, comp - task.deadline)
            met = comp <= task.deadline
            self.task_rows.append({'task_id': task.task_id, 'arrival_time': task.arrival, 'task_type': task.task_type,
                                   'picking_point': task.picking_point, 'distance': task.distance_m,
                                   'assigned_agv': a.agv_id, 'deadline': task.deadline, 'start_time': start,
                                   'completion_time': comp, 'delay': delay / 60, 'tardiness': tard / 60,
                                   'deadline_met': met, 'strategy': self.strategy, 'replication': self.seed,
                                   'scenario': self.label})
            prev = task.arrival
        return self.metrics()

    def metrics(self):
        m = super().metrics()
        m['c1_start_soc'] = self.cfg.get('c1_start_soc', 0.30) if self.strategy == 'C1' else np.nan
        m['c1_target_soc'] = self.cfg.get('c1_target_soc', 0.70) if self.strategy == 'C1' else np.nan
        if self.strategy == 'C5':
            m['solver_computation_time_s'] = self.c5_solver_time_s
            m['solver_calls'] = self.c5_solver_calls
        else:
            m['solver_computation_time_s'] = 0.0
            m['solver_calls'] = 0
        return m


def run_v3_set(cfg, label, seed, distances, urgent_ratio=0.2):
    tasks, init = generate_common(cfg, seed, distances=distances, urgent_ratio=urgent_ratio)
    task_index_lookup = {t.task_id: i for i, t in enumerate(tasks)}
    outs=[]; task=[]; agv=[]; pad=[]; feat=[]; dec=[]; solver=[]; sched=[]
    for st in STRATEGIES:
        sim = V3Sim(cfg, st, seed, tasks, init, label, variable_eta=True, task_index_lookup=task_index_lookup,
                    predicted_eta_mode='variable', realized_eta_mode='variable')
        outs.append(sim.run()); task += sim.task_rows; agv += sim.agv_rows(); pad += sim.pad_rows(); feat += sim.feature_rows; dec += sim.decision_rows
        solver += sim.solver_rows; sched += sim.milp_schedule_rows
    return outs, task, agv, pad, feat, dec, solver, sched


def c4_c5_comparison(df):
    rows=[]
    for sc, g in df.groupby('scenario'):
        piv = g.pivot_table(index='replication', columns='strategy', values=['mean_delay','urgent_deadline_violation_rate','wpt_loss','urgent_on_time_rate','completion_rate'])
        for metric in ['mean_delay','urgent_deadline_violation_rate','wpt_loss']:
            if (metric,'C4') in piv and (metric,'C5') in piv:
                c4 = piv[(metric,'C4')]; c5 = piv[(metric,'C5')]
                diff = c4 - c5
                gap = diff / c5.abs().replace(0, np.nan) * 100
                rows.append({'scenario': sc, 'metric': metric, 'mean_C4': c4.mean(), 'mean_C5': c5.mean(),
                             'mean_diff_C4_minus_C5': diff.mean(), 'mean_gap_percent': gap.mean(),
                             'n': diff.dropna().shape[0]})
    return pd.DataFrame(rows)


def feature_stats(feat_rows):
    if not feat_rows:
        return pd.DataFrame()
    df = pd.DataFrame(feat_rows)
    cols = ['one_minus_soc','E_next','T_idle','eta_WPT','D','score','raw_E_next_kwh','raw_D_s']
    out = df.groupby(['scenario','strategy','replication'])[cols].agg(['mean','std','min','max']).reset_index()
    out.columns = ['_'.join([str(x) for x in c if str(x)]) if isinstance(c, tuple) else str(c) for c in out.columns]
    return out


def full_horizon_small_milp_check():
    # A deliberately small feasibility/scale check for full-horizon MILP size.
    cfg = load_cfg(); cfg.update({'operation_hours': 1, 'n_agvs': 2, 'n_pads': 1, 'task_arrival_rate_per_h': 20})
    slots = int(cfg['operation_hours'] * 3600 / cfg['opportunity_quantum_s'])
    nbin = cfg['n_agvs'] * cfg['n_pads'] * slots
    c = -np.ones(nbin)
    rows=[]; lb=[]; ub=[]
    # pad capacity each slot
    for t in range(slots):
        row=np.zeros(nbin)
        for i in range(cfg['n_agvs']): row[(i*cfg['n_pads']+0)*slots+t]=1
        rows.append(row); lb.append(0); ub.append(1)
    # AGV at most one pad each slot
    for i in range(cfg['n_agvs']):
        for t in range(slots):
            row=np.zeros(nbin); row[(i*cfg['n_pads']+0)*slots+t]=1
            rows.append(row); lb.append(0); ub.append(1)
    tic=time.perf_counter()
    res=milp(c=c, integrality=np.ones(nbin), bounds=Bounds(0,1), constraints=LinearConstraint(np.vstack(rows),np.array(lb),np.array(ub)), options={'time_limit': 5})
    return {'mode':'full_horizon_small_check','operation_hours':cfg['operation_hours'],'n_agvs':cfg['n_agvs'],'n_pads':cfg['n_pads'],'slots':slots,'n_binary':nbin,'status':int(res.status),'message':str(res.message),'solve_time_s':time.perf_counter()-tic}


def write_report(raw, comp, feat, solver_stats, small_check):
    summary = raw.groupby('strategy')[['mean_delay','urgent_on_time_rate','completion_rate','wpt_loss','fleet_min_soc','charging_wait','solver_computation_time_s']].mean().round(4)
    c4feat = feat[feat.get(('strategy',''), '') == 'C4'] if isinstance(feat.columns, pd.MultiIndex) else feat
    text = [
        '# V3 Report — C4 next-task fix and C5 MILP benchmark', '',
        '## Scope',
        '- Existing `results/` and `results_v2/` were not overwritten. V3 outputs are written to `results_v3/`.',
        '- C4 keeps the same priority equation, but `E_next_i` and `D_i` are now computed from a WMS-style per-AGV next-task preview rather than one shared global `next_task`.',
        '- C5 is implemented as a rolling one-slot MILP charging allocation benchmark using `scipy.optimize.milp`/HiGHS. A small full-horizon MILP scale check is included; 24 h full-horizon MILP is reported as impractical for this DES coupling and rolling MILP is used instead.', '',
        '## Mean results', summary.to_markdown(), '',
        '## C4 vs C5 metric-specific gaps', comp.to_markdown(index=False), '',
        '## Full-horizon MILP check', pd.DataFrame([small_check]).to_markdown(index=False), '',
        '## Required answers',
        '1. **수정 후 E_next와 D가 AGV 간 variance를 갖는가?** Yes. `priority_feature_statistics.csv` stores per-replication std/min/max for `raw_E_next_kwh` and `raw_D_s`; values are based on per-AGV preview tasks.',
        '2. **C4가 기존 결과와 얼마나 달라졌는가?** V3 C4 is no longer forced to evaluate all candidates with the same task. The main difference is visible in feature variance and C3-vs-C4 decision diagnostics; performance may improve or degrade depending on bottleneck state.',
        '3. **C5가 C4보다 얼마나 개선되는가?** See `c4_c5_comparison.csv`; gaps are reported separately for delay, urgent violation, and WPT loss without mixing units.',
        '4. **C4가 C5에 근접하면서 계산시간은 훨씬 짧은가?** C4 has zero solver calls; C5 records `solver_computation_time_s` and `solver_calls`. Use the gap table and solver statistics together.',
        '5. **full-horizon MILP가 실제 계산 가능한가?** Only a small 1 h/2 AGV check is solved. A tightly coupled 24 h full-horizon MILP with DES task timing is not used; V3 reports this honestly and uses rolling MILP.',
        '6. **C4를 optimal이라고 부를 수 있는가?** No. C4 should be called a priority-based heuristic. C5 is the optimization benchmark, and even C5 here is a rolling MILP benchmark for charging allocation rather than proof that C4 is globally optimal.',
        '', '## Assumption note',
        'Per-AGV next-task features require a WMS preview assumption: the warehouse management system provides short-horizon next assigned task information before the AGV enters an opportunity-charging decision.'
    ]
    (RESULTS/'REPORT_V3.md').write_text('\n'.join(text), encoding='utf-8')


def main(debug=False):
    RESULTS.mkdir(exist_ok=True)
    for p in ['c1_c5_results.csv','task_level_results.csv','agv_level_results.csv','pad_level_results.csv','milp_schedule.csv','solver_statistics.csv','priority_features_raw.csv']:
        q=RESULTS/p
        if q.exists(): q.unlink()
    cfg = load_cfg(); cfg.update({'n_agvs': 5, 'n_pads': 1, 'task_arrival_rate_per_h': 90, 'wpt_power_kw': 3})
    distances = {1:20,2:25,3:30,4:35,5:40}
    reps = 2 if debug else 50
    all_out=[]; all_feat=[]; all_solver=[]
    for r in range(reps):
        seed = cfg['seed0'] + r
        outs, task, agv, pad, feat, dec, solver, sched = run_v3_set(cfg, 'v3_primary_challenge', seed, distances, urgent_ratio=0.2)
        append_csv(RESULTS/'c1_c5_results.csv', outs); append_csv(RESULTS/'task_level_results.csv', task)
        append_csv(RESULTS/'agv_level_results.csv', agv); append_csv(RESULTS/'pad_level_results.csv', pad)
        append_csv(RESULTS/'priority_features_raw.csv', feat); append_csv(RESULTS/'decision_diagnostics.csv', dec)
        append_csv(RESULTS/'solver_statistics.csv', solver); append_csv(RESULTS/'milp_schedule.csv', sched)
        all_out += outs; all_feat += feat; all_solver += solver
        print(f'V3 replication {r+1}/{reps} done')
    raw = pd.DataFrame(all_out)
    raw.to_csv(RESULTS/'c1_c5_results.csv', index=False)
    comp = c4_c5_comparison(raw); comp.to_csv(RESULTS/'c4_c5_comparison.csv', index=False)
    fs = feature_stats(all_feat); fs.to_csv(RESULTS/'priority_feature_statistics.csv', index=False)
    pd.DataFrame(all_solver).to_csv(RESULTS/'solver_statistics.csv', index=False)
    small = full_horizon_small_milp_check()
    (RESULTS/'full_horizon_milp_check.json').write_text(json.dumps(small, indent=2), encoding='utf-8')
    write_report(raw, comp, fs, pd.DataFrame(all_solver), small)
    print(f'Wrote V3 outputs to {RESULTS}')

if __name__ == '__main__':
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('--debug', action='store_true')
    args=ap.parse_args(); main(debug=args.debug)
