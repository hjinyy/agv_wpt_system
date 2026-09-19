from __future__ import annotations
import csv, json, shutil, subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from math import sqrt
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
import v2_runner, v3_runner
from rho_pipeline import FEATURES, FourFeatureC4Sim, configuration_for, load_experiment_config, scenario_catalog_rows, scenarios
from simulation.final_wpt import physical_efficiency_values
from v2_runner import generate_common
from v3_runner import V3Sim
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'results'/'final_unseen'; RAW=OUT/'raw'; SUM=OUT/'summary'; STATS=OUT/'statistics'
SEEDS=tuple(range(6007,6057)); STRATEGIES=('C1','C2','C3','C4','C5'); FROZEN='63bf5d486e061894a29d136272debe738cdb4871'
def cb(): v2_runner.eta_values=physical_efficiency_values; v3_runner.eta_values=physical_efficiency_values
def run_one(name,seed):
 cb(); data=load_experiment_config(); sc=scenarios(data)[name]; c4=json.load(open(ROOT/'results/tuning/frozen_c4_parameters.json'))['weights']; c5=json.load(open(ROOT/'results/pre_final/frozen_c5_parameters.json'))['scales']; cfg=configuration_for(sc,c4); cfg.update({'c5_lambda_soc':c5['lambda_soc'],'c5_lambda_task':c5['lambda_task'],'c5_lambda_kpi':c5['lambda_kpi']}); tasks,initial=generate_common(cfg,seed,distances=sc.distances,urgent_ratio=sc.urgent_ratio); lookup={x.task_id:i for i,x in enumerate(tasks)}; rows=[]; solver=[]
 for st in STRATEGIES:
  sim=(FourFeatureC4Sim(cfg,st,seed,tasks,initial,name,variable_eta=True,task_index_lookup=lookup,predicted_eta_mode='variable',realized_eta_mode='variable',current_distances=sc.distances_m) if st=='C4' else V3Sim(cfg,st,seed,tasks,initial,name,variable_eta=True,task_index_lookup=lookup,predicted_eta_mode='variable',realized_eta_mode='variable'))
  m=sim.run(); m['critical_soc_event_count']=sum(int(s<=cfg['critical_soc'] and p>cfg['critical_soc']) for a in sim.agvs for p,s in zip((1.0,*(v for _,v in a.trace[:-1])),(v for _,v in a.trace))); m['simulation_failure_count']=0; m['infeasible_count']=int(m.get('solver_infeasible_calls',0)); rows.append(m); solver.extend(sim.solver_rows)
 return rows,solver
def write(path,rows):
 path.parent.mkdir(parents=True,exist_ok=True); f=list(dict.fromkeys(k for r in rows for k in r));
 with path.open('w',newline='',encoding='utf8') as h: w=csv.DictWriter(h,fieldnames=f);w.writeheader();w.writerows(rows)
def paired(df,left,right,metric,scenario):
 a=df[(df.scenario==scenario)&(df.strategy==left)].set_index('replication')[metric];b=df[(df.scenario==scenario)&(df.strategy==right)].set_index('replication')[metric]; d=(a-b).to_numpy(float); se=d.std(ddof=1)/sqrt(len(d)); margin=stats.t.ppf(.975,len(d)-1)*se; p=float(stats.ttest_1samp(d,0).pvalue); better=(d<0).mean()*100 if metric=='mean_delay' else (d>0).mean()*100
 return {'scenario':scenario,'comparison':f'{left}_minus_{right}','metric':metric,'mean_difference':d.mean(),'median_difference':np.median(d),'standard_error':se,'ci95_low':d.mean()-margin,'ci95_high':d.mean()+margin,'left_better_fraction_percent':better,'p_value':p,'paired_replications':len(d)}
def main():
 if OUT.exists(): raise RuntimeError('final_unseen already exists: one-time final execution is blocked')
 data=load_experiment_config(); t=set(range(5007,5057)); assert not(t&set(SEEDS)); assert json.load(open(ROOT/'results/pre_final/frozen_experiment_manifest.json'))['frozen_experiment_sha']==FROZEN
 catalog=pd.DataFrame(scenario_catalog_rows(data)); assert (catalog.logistics_utilization<1).all(); assert set(catalog[catalog.scenario.isin(data['tuning_scenarios'])].rho_region)=={'non_binding','near_transition','transition','moderately_constrained','strongly_constrained'}
 jobs=[(n,s) for n in ['base','stress_non_binding','stress_near_transition','stress_transition','primary','stress_strongly_constrained'] for s in SEEDS]; rows=[];solver=[]
 with ProcessPoolExecutor(max_workers=4) as ex:
  fs=[ex.submit(run_one,*j) for j in jobs]
  for i,f in enumerate(as_completed(fs),1): r,x=f.result();rows+=r;solver+=x;print(f'FINAL {i}/{len(fs)}',flush=True)
 write(RAW/'replication_metrics.csv',sorted(rows,key=lambda x:(x['scenario'],x['strategy'],x['replication'])));write(RAW/'c5_solver_calls.csv',solver)
 df=pd.DataFrame(rows); metrics=['mean_delay','urgent_on_time_rate','completion_rate','battery_delivered_energy','wpt_loss','fleet_min_soc','critical_soc_event_count','low_soc_stops','charging_wait','priority_decisions','total_priority_computation_time_s','mean_decision_latency_ms','p95_decision_latency_ms','max_decision_latency_ms','solver_calls_per_replication','solver_total_time_per_replication_s','solver_mean_time_per_call_ms','solver_p95_time_per_call_ms','solver_max_time_per_call_ms']
 summary=df.groupby(['scenario','strategy'])[metrics].agg(['mean','std']).reset_index();summary.columns=['_'.join(x).strip('_') for x in summary.columns];summary.to_csv(SUM/'strategy_summary.csv',index=False)
 ps=[]
 for r in ['C1','C2','C3','C5']:
  for m in ['mean_delay','urgent_on_time_rate']: ps.append(paired(df,'C4',r,m,'primary'))
 for n in ['stress_non_binding','stress_near_transition','stress_transition','primary','stress_strongly_constrained']:
  for m in ['mean_delay','urgent_on_time_rate']:ps.append(paired(df,'C4','C3',m,n))
 p=pd.DataFrame(ps); order=p.p_value.sort_values().index; q=np.empty(len(p)); prev=1.
 for rank,idx in reversed(list(enumerate(order,1))): prev=min(prev,float(p.loc[idx,'p_value'])*len(p)/rank);q[idx]=prev
 p['bh_adjusted_p_value']=q;p.to_csv(STATS/'paired_statistics.csv',index=False);catalog.to_csv(SUM/'rho_catalog.csv',index=False)
 manifest={'frozen_experiment_sha':FROZEN,'final_results_commit_sha':None,'final_seeds':list(SEEDS),'C4_weights':json.load(open(ROOT/'results/tuning/frozen_c4_parameters.json'))['weights'],'C5_scales':json.load(open(ROOT/'results/pre_final/frozen_c5_parameters.json'))['scales'],'scenario_parameters':data['scenarios'],'rho_taxonomy':'<0.7 non-binding; [0.7,0.9) near-transition; [0.9,1.0) transition; [1.0,1.3) moderately constrained; >=1.3 strongly constrained','software':{'python':subprocess.check_output(['.venv/bin/python','--version'],text=True).strip()},'one_time_execution':True};(OUT/'final_result_manifest.json').write_text(json.dumps(manifest,indent=2))
 (OUT/'FINAL_EVALUATION_REPORT.md').write_text('# Unseen Final Evaluation\n\nFinal seeds 6007–6056 were used once with CRN across strategies. See CSV summaries/statistics; interpretation is based on paired CIs without universal-winner claims.\n')
if __name__=='__main__':main()
