from __future__ import annotations
import csv, json
from concurrent.futures import ProcessPoolExecutor, as_completed
from math import sqrt
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
from rho_pipeline import FEATURES, FourFeatureC4Sim, configuration_for, load_experiment_config, scenario_catalog_rows, scenarios, tuning_seeds
from run_rho_tuning import simplex_grid, _local_neighbors
from v2_runner import generate_common
from v3_runner import V3Sim
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'results'/'pre_final_literature_wpt'
def write(name,rows):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True); cols=list(dict.fromkeys(k for r in rows for k in r));
 with p.open('w',newline='',encoding='utf8') as f:w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)
def wid(w):return '_'.join(f'{k}{w[k]:.2f}' for k in FEATURES)
def run_one(scenario_name,seed,strategy,weights=None,capture=False):
 data=load_experiment_config();sc=scenarios(data)[scenario_name];w=weights or {k:1/len(FEATURES) for k in FEATURES};cfg=configuration_for(sc,w,data);tasks,init=generate_common(cfg,seed,distances=sc.distances,urgent_ratio=sc.urgent_ratio);lookup={t.task_id:i for i,t in enumerate(tasks)}
 if strategy=='C4': sim=FourFeatureC4Sim(cfg,'C4',seed,tasks,init,scenario_name,variable_eta=True,task_index_lookup=lookup,predicted_eta_mode='predicted',realized_eta_mode='realized',current_distances=sc.distances_m)
 else: sim=V3Sim(cfg,strategy,seed,tasks,init,scenario_name,variable_eta=True,task_index_lookup=lookup,predicted_eta_mode='predicted',realized_eta_mode='realized')
 m=sim.run();m.update({'weight_id':wid(w) if strategy=='C4' else 'reference',**(w if strategy=='C4' else {}),'simulation_failure':0})
 return m,(sim.feature_rows if capture else []),(sim.physical_feature_diagnostic_rows if capture and strategy=='C4' else []),(sim.wpt_condition_rows if capture else []),sim.decision_rows if capture else []
def paired(c4,c3):
 ref={(r['scenario'],r['replication']):r for r in c3};rows=[]
 for r in c4:
  b=ref[(r['scenario'],r['replication'])];rows.append({**{k:r[k] for k in FEATURES},'weight_id':r['weight_id'],'scenario':r['scenario'],'replication':r['replication'],'delay_diff':r['mean_delay']-b['mean_delay'],'urgent_diff':r['urgent_on_time_rate']-b['urgent_on_time_rate'],'completion_diff':r['completion_rate']-b['completion_rate'],'min_soc_diff':r['fleet_min_soc']-b['fleet_min_soc'],'hard_reject':int(r['low_soc_stops']>0 or r['simulation_failure']>0)})
 return rows
def summary(pairs):
 df=pd.DataFrame(pairs);out=[]
 for wid_,g in df.groupby('weight_id'):
  out.append({'weight_id':wid_,**{k:float(g[k].iloc[0]) for k in FEATURES},'mean_delay_diff':g.delay_diff.mean(),'worst_delay_degradation':g.groupby('scenario').delay_diff.mean().max(),'mean_urgent_diff':g.urgent_diff.mean(),'worst_urgent_degradation':g.groupby('scenario').urgent_diff.mean().min(),'mean_completion_diff':g.completion_diff.mean(),'worst_min_soc_diff':g.groupby('scenario').min_soc_diff.mean().min(),'hard_reject':bool(g.hard_reject.any())})
 return pd.DataFrame(out)
def pareto(s):
 valid=s[~s.hard_reject].copy();v=valid[['mean_delay_diff','worst_delay_degradation','mean_urgent_diff','worst_urgent_degradation','mean_completion_diff','worst_min_soc_diff']].to_numpy(float);keep=[]
 for i,x in enumerate(v):
  nw=(v[:,0]<=x[0])&(v[:,1]<=x[1])&(v[:,2]>=x[2])&(v[:,3]>=x[3])&(v[:,4]>=x[4])&(v[:,5]>=x[5]);st=(v[:,0]<x[0])|(v[:,1]<x[1])|(v[:,2]>x[2])|(v[:,3]>x[3])|(v[:,4]>x[4])|(v[:,5]>x[5]);keep.append(not bool((nw&st).any()))
 return valid.loc[keep].sort_values(['worst_delay_degradation','mean_delay_diff','worst_urgent_degradation','mean_urgent_diff'],ascending=[True,True,False,False])
def parallel_runs(jobs, capture=False):
 rows=[]
 with ProcessPoolExecutor(max_workers=16) as ex:
  fs=[ex.submit(run_one,*j,capture) for j in jobs]
  for i,f in enumerate(as_completed(fs),1):
   rows.append(f.result())
   if i%100==0 or i==len(fs):print(f'RUN {i}/{len(fs)}',flush=True)
 return rows

def run_grid(candidates,phase,names,seeds):
 jobs=[(n,s,'C4',w) for w in candidates for n in names for s in seeds];rows=[]
 for m,_,_,_,_ in parallel_runs(jobs): rows.append(m)
 for r in rows:r['phase']=phase
 return rows
def renormalize_without(w,key):
 z={k:(0.0 if k==key else float(v)) for k,v in w.items()};total=sum(z.values());return {k:v/total for k,v in z.items()} if total else z
def main():
 if OUT.exists() and any(OUT.iterdir()): raise RuntimeError('pre_final_literature_wpt exists; refusing overwrite')
 OUT.mkdir(parents=True);data=load_experiment_config();seeds=tuning_seeds(data);names=list(data['tuning_scenarios']);assert seeds==tuple(range(7107,7157));assert not set(seeds)&set(range(8007,8057))
 pd.DataFrame(scenario_catalog_rows(data)).to_csv(OUT/'frozen_rho_catalog.csv',index=False)
 refs=[]
 for m,_,_,_,_ in parallel_runs([(n,s,st,None) for st in ('C1','C2','C3') for n in names for s in seeds]): refs.append(m)
 write('reference_strategies.csv',refs);c3=[r for r in refs if r['strategy']=='C3']
 coarse=simplex_grid(.25);coarse_rows=run_grid(coarse,'coarse',names,seeds);write('c4_coarse_search.csv',coarse_rows);cp=paired(coarse_rows,c3);write('c4_coarse_paired.csv',cp);cs=summary(cp);cs.to_csv(OUT/'c4_coarse_candidates.csv',index=False);anchor=pareto(cs).iloc[0];local=_local_neighbors({k:float(anchor[k]) for k in FEATURES},.05);local_rows=run_grid(local,'local',names,seeds);write('c4_local_refinement.csv',local_rows);lp=paired(local_rows,c3);allp=cp+lp;write('c4_paired_statistics_raw.csv',allp);summ=summary(allp);summ.to_csv(OUT/'c4_candidates.csv',index=False);front=pareto(summ);front.to_csv(OUT/'c4_pareto_candidates.csv',index=False);chosen=front.iloc[0];w={k:float(chosen[k]) for k in FEATURES};(OUT/'frozen_c4_parameters.json').write_text(json.dumps({'weights':w,'score':data['c4_general_formulation']['score'],'tuning_seeds':list(seeds),'selection':'hard safety rejection then six-KPI Pareto robustness'},indent=2))
 # diagnostic/ablation reruns on tuning block only
 ablations={'full':w,'no_P':renormalize_without(w,'charging_power_quality'),'no_deadline':renormalize_without(w,'deadline')};diag=[];features=[];phys=[];conds=[];decs=[]
 for label,aw in ablations.items():
  for n in names:
   for s in seeds:
    m,f,p,c,d=run_one(n,s,'C4',aw,True);m['ablation']=label;diag.append(m);features += [{**x,'ablation':label} for x in f];phys += [{**x,'ablation':label} for x in p];conds += [{**x,'ablation':label} for x in c];decs += [{**x,'ablation':label} for x in d]
 for r in c3:r2=dict(r);r2['ablation']='soc_only';diag.append(r2)
 write('c4_ablation_results.csv',diag);write('c4_feature_rows.csv',features);write('physical_feature_diagnostics.csv',phys);write('wpt_condition_realizations.csv',conds);write('c4_decision_diagnostics.csv',decs)
 d=pd.DataFrame(phys);q=pd.DataFrame(conds);fd=[]
 for (ab,sc),g in d.groupby(['ablation','scenario']):fd.append({'ablation':ab,'scenario':sc,'decisions':len(g),'f_P_std_mean':g.f_P_std.mean(),'f_P_std_contention_mean':g[g.contention_event==1].f_P_std.mean(),'selection_changed_fraction':g.p_term_changed_selection.mean(),'selection_changed_fraction_contention':g[g.contention_event==1].p_term_changed_selection.mean()})
 pd.DataFrame(fd).to_csv(OUT/'physical_feature_summary.csv',index=False);q.groupby(['ablation','scenario']).apply(lambda g: pd.Series({'prediction_power_mae_kw':(g.predicted_charge_power_kw-g.realized_charge_power_kw).abs().mean(),'prediction_power_rmse_kw':np.sqrt(((g.predicted_charge_power_kw-g.realized_charge_power_kw)**2).mean()),'prediction_power_bias_kw':(g.predicted_charge_power_kw-g.realized_charge_power_kw).mean()})).reset_index().to_csv(OUT/'prediction_error_summary.csv',index=False)
 report=['# C4 Five-Feature Robust Tuning','',f'- Coarse candidates: {len(coarse)}; local candidates: {len(local)}.','- Selected by hard safety rejection then multi-scenario Pareto robustness; no w_P positivity constraint.','', '## Frozen weights','```json',json.dumps(w,indent=2),'```','', '## Pareto candidates',front.to_markdown(index=False,floatfmt='.4f')];(OUT/'C4_TUNING_REPORT.md').write_text('\n'.join(report)+'\n')
 print('FROZEN_C4',json.dumps(w,sort_keys=True),flush=True)
if __name__=='__main__':main()
