from __future__ import annotations
import json, platform, sys, shutil
from pathlib import Path
from copy import deepcopy
import yaml
import numpy as np
import pandas as pd
from scipy import stats
from simulation.environment import WPTAGVSimulation, common_random_inputs, STRATEGIES

ROOT=Path(__file__).resolve().parent
RESULTS=ROOT/'results'

def load_config():
    with open(ROOT/'config.yaml','r',encoding='utf-8') as f: raw=yaml.safe_load(f)
    cfg=dict(raw['base']); cfg['weights']=raw['weights']; cfg['efficiency_states']=raw['efficiency_states']; cfg['_raw']=raw
    return cfg

def run_one(cfg, strategy, seed, label='base:base', tasks=None, init_socs=None, eta_states=None):
    sim=WPTAGVSimulation(cfg,strategy,seed,tasks=tasks,init_socs=init_socs,eta_states=eta_states,label=label)
    m=sim.run(); return m, sim.agv_results(), sim.pad_results(), sim.soc_trace_frame(), sim.scheduler.feature_records

def run_strategy_set(cfg, seed, label):
    tasks, init_socs, eta_states = common_random_inputs(cfg, seed)
    rows=[]; agv=[]; pad=[]; traces=[]; feats=[]
    for st in STRATEGIES:
        m,a,p,tr,f = run_one(deepcopy(cfg), st, seed, label, tasks, init_socs, eta_states)
        rows.append(m); agv += [{**r,'replication':seed} for r in a]; pad += [{**r,'replication':seed} for r in p]
        if seed == cfg.get('_trace_seed', cfg['seed0']): traces.append(tr.assign(replication=seed, scenario=label))
        for rec in f: feats.append({**rec,'strategy':st,'scenario':label.split(':')[0],'scenario_value':label.split(':')[-1],'replication':seed})
    return rows, agv, pad, traces, feats

def calibration(cfg):
    rows=[]; raw=cfg['_raw']['calibration']
    base=deepcopy(cfg); reps=int(raw['reps'])
    for e in raw['e_dist_values']:
        for paux in raw['p_aux_values']:
            tmp=[]
            for r in range(reps):
                c=deepcopy(base); c['e_dist_kwh_per_km']=float(e); c['p_aux_kw']=float(paux); c['n_pads']=0
                # no-WPT sanity by making C1 but no pads impossible; instead disable mandatory by giving pads? use C2 no charge via zero power
                c['n_pads']=2; c['wpt_power_kw']=0.001; c['critical_soc']=-1.0; c['min_soc']=-1.0
                m,_,_,_,_=run_one(c,'C2',c['seed0']+r,'calibration:no_wpt')
                tmp.append(m)
            rows.append({'e_dist_kwh_per_km':e,'p_aux_kw':paux,'mean_fleet_min_soc':np.mean([x['fleet_min_soc'] for x in tmp]),
                         'mean_stops':np.mean([x['low_soc_stops'] for x in tmp]),'mean_completion_rate':np.mean([x['completion_rate'] for x in tmp])})
    return pd.DataFrame(rows)

def aggregate(raw):
    metrics=['requested_tasks','completed_tasks','throughput','completion_rate','mean_delay','max_delay','idle_ratio','charging_wait','low_soc_stops','traction_energy','aux_energy','wpt_input_energy','battery_delivered_energy','wpt_loss','mean_efficiency','fleet_min_soc','pad_utilization','mean_queue','max_queue','detour_distance_m']
    summ=raw.groupby(['scenario','scenario_value','strategy'])[metrics].agg(['mean','std','median',lambda x: np.percentile(x,5),lambda x: np.percentile(x,95)])
    summ.columns=['_'.join([a,b if isinstance(b,str) else 'p']).replace('<lambda_0>','p5').replace('<lambda_1>','p95') for a,b in summ.columns]
    return summ.reset_index()

def paired(raw):
    rows=[]
    for (sc,val),g in raw.groupby(['scenario','scenario_value']):
        piv=g.pivot_table(index='replication',columns='strategy',values=['throughput','mean_delay','completion_rate','low_soc_stops'])
        for metric in ['throughput','mean_delay','completion_rate','low_soc_stops']:
            for base in ['C1','C2','C3']:
                if (metric,'C4') in piv and (metric,base) in piv:
                    d=(piv[(metric,'C4')]-piv[(metric,base)]).dropna();
                    if len(d)>1:
                        ci=stats.t.interval(0.95,len(d)-1,loc=d.mean(),scale=stats.sem(d)) if d.std()>0 else (d.mean(),d.mean())
                        rows.append({'scenario':sc,'scenario_value':val,'metric':metric,'comparison':f'C4-{base}','mean_diff':d.mean(),'ci95_low':ci[0],'ci95_high':ci[1],'n':len(d)})
    return pd.DataFrame(rows)

def design_guideline(raw,cfg):
    rows=[]; thresholds=cfg['_raw']['design']['completion_thresholds']; stopfrac=cfg['_raw']['design']['stop_free_rep_fraction']
    for th in thresholds:
        for (sc,val,st),g in raw.groupby(['scenario','scenario_value','strategy']):
            feasible=(g['completion_rate'].mean()/100>=th) and ((g['low_soc_stops']==0).mean()>=stopfrac)
            rows.append({'criterion_completion':th,'scenario':sc,'scenario_value':val,'strategy':st,'feasible':feasible,'mean_completion_rate':g['completion_rate'].mean(),'stop_free_fraction':(g['low_soc_stops']==0).mean(),'mean_delay':g['mean_delay'].mean()})
    # scenario B min pads and D min power for C4 under base criterion
    return pd.DataFrame(rows)

def run_all(fast=False):
    RESULTS.mkdir(exist_ok=True)
    cfg=load_config(); reps=10 if fast else int(cfg['replications'])
    rows=[]; agv=[]; pad=[]; traces=[]; feats=[]
    cal=calibration(cfg); cal.to_csv(RESULTS/'energy_calibration.csv',index=False)
    scenarios=[('base','base',{})]
    for v in cfg['_raw']['scenarios']['A_agv']: scenarios.append(('A_agv',str(v),{'n_agvs':int(v)}))
    for v in cfg['_raw']['scenarios']['B_pad']: scenarios.append(('B_pad',str(v),{'n_pads':int(v)}))
    for v in cfg['_raw']['scenarios']['C_workload']: scenarios.append(('C_workload',str(v),{'task_arrival_rate_per_h':float(v)}))
    for v in cfg['_raw']['scenarios']['D_power']: scenarios.append(('D_power',str(v),{'wpt_power_kw':float(v)}))
    seen=set()
    for sc,val,over in scenarios:
        key=(sc,val)
        # keep duplicated base rows only once for base + individual scenarios? run all because labels differ
        c=deepcopy(cfg); c.update(over); c['_trace_seed']=cfg['seed0']
        for r in range(reps):
            seed=cfg['seed0']+r
            rr,aa,pp,tt,ff=run_strategy_set(c,seed,f'{sc}:{val}')
            for x in rr: x['replication']=r
            rows += rr; agv += aa; pad += pp; traces += tt; feats += ff
    # ablation C4 fixed vs variable
    abl=[]
    for mode,var in [('C4-Fixed',False),('C4-Variable',True)]:
        c=deepcopy(cfg); c['variable_efficiency']=var
        for r in range(reps):
            seed=cfg['seed0']+r; tasks,init,etas=common_random_inputs(c,seed)
            m,_,_,_,_=run_one(c,'C4',seed,f'ablation_efficiency:{mode}',tasks,init,etas)
            m['replication']=r; m['strategy']=mode; abl.append(m); rows.append(m)
    raw=pd.DataFrame(rows); raw.to_csv(RESULTS/'raw_runs.csv',index=False)
    pd.DataFrame(agv).to_csv(RESULTS/'agv_level_results.csv',index=False)
    pd.DataFrame(pad).to_csv(RESULTS/'pad_level_results.csv',index=False)
    pd.concat(traces,ignore_index=True).to_csv(RESULTS/'soc_trace_representative.csv',index=False)
    feat=pd.DataFrame(feats)
    if not feat.empty:
        feat_stats=feat.groupby(['scenario','scenario_value','strategy'])[['one_minus_soc','E_next','T_idle','eta_WPT','D','score']].agg(['mean','std','median','min','max']).reset_index()
        feat_stats.columns=['_'.join([str(x) for x in c if str(x)]) for c in feat_stats.columns]
        feat_stats.to_csv(RESULTS/'priority_feature_statistics.csv',index=False)
        feat.sample(min(len(feat),5000), random_state=1).to_csv(RESULTS/'priority_feature_sample.csv',index=False)
    else:
        feat.to_csv(RESULTS/'priority_feature_statistics.csv',index=False)
    pd.DataFrame(abl).to_csv(RESULTS/'ablation_efficiency.csv',index=False)
    summ=aggregate(raw); summ.to_csv(RESULTS/'summary_by_scenario.csv',index=False)
    raw.groupby('strategy')[['throughput','completion_rate','mean_delay','low_soc_stops','pad_utilization']].agg(['mean','std']).to_csv(RESULTS/'summary_by_strategy.csv')
    paired(raw).to_csv(RESULTS/'paired_comparisons.csv',index=False)
    design_guideline(raw,cfg).to_csv(RESULTS/'design_guideline.csv',index=False)
    with open(RESULTS/'run_metadata.json','w',encoding='utf-8') as f: json.dump({'python':sys.version,'platform':platform.platform(),'reps':reps,'config':cfg['_raw']},f,indent=2,ensure_ascii=False)
    from analysis.plots import make_plots
    make_plots(RESULTS)
    from analysis.aggregate import write_report
    write_report(RESULTS)
    return raw

if __name__ == '__main__':
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('--fast',action='store_true')
    args=ap.parse_args(); df=run_all(args.fast); print(f'completed {len(df)} runs; results in {RESULTS}')
