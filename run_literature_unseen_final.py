from __future__ import annotations
import csv, json, subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from math import sqrt
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
from rho_pipeline import FEATURES, FourFeatureC4Sim, configuration_for, load_experiment_config, scenario_catalog_rows, scenarios
from v2_runner import generate_common
from v3_runner import V3Sim
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'results'/'final_literature_wpt'; RAW=OUT/'raw'; SUM=OUT/'summary'; STATS=OUT/'statistics'; SEEDS=tuple(range(8007,8057)); STRATEGIES=('C1','C2','C3','C4','C5')
def write(path,rows):
 path.parent.mkdir(parents=True,exist_ok=True); fields=list(dict.fromkeys(k for r in rows for k in r))
 with path.open('w',newline='',encoding='utf8') as h:w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows(rows)
def run_one(name,seed):
 data=load_experiment_config();sc=scenarios(data)[name];c4=json.loads((ROOT/'results/pre_final_literature_wpt/frozen_c4_parameters.json').read_text())['weights'];c5=json.loads((ROOT/'results/pre_final_literature_wpt/frozen_c5_parameters.json').read_text())['scales'];cfg=configuration_for(sc,c4,data);cfg.update({'c5_lambda_soc':c5['lambda_soc'],'c5_lambda_task':c5['lambda_task'],'c5_lambda_kpi':c5['lambda_kpi']});tasks,initial=generate_common(cfg,seed,distances=sc.distances,urgent_ratio=sc.urgent_ratio);lookup={x.task_id:i for i,x in enumerate(tasks)};rows=[];solver=[]
 for st in STRATEGIES:
  sim=FourFeatureC4Sim(cfg,'C4',seed,tasks,initial,name,variable_eta=True,task_index_lookup=lookup,predicted_eta_mode='predicted',realized_eta_mode='realized',current_distances=sc.distances_m) if st=='C4' else V3Sim(cfg,st,seed,tasks,initial,name,variable_eta=True,task_index_lookup=lookup,predicted_eta_mode='predicted',realized_eta_mode='realized')
  m=sim.run();m.update({'simulation_failure':0,'infeasible_count':int(m.get('solver_infeasible_calls',0))});rows.append(m);solver+=sim.solver_rows
 return rows,solver
def paired(df,left,right,metric,scenario):
 a=df[(df.scenario==scenario)&(df.strategy==left)].set_index('replication')[metric];b=df[(df.scenario==scenario)&(df.strategy==right)].set_index('replication')[metric];d=(a-b).to_numpy(float);se=d.std(ddof=1)/sqrt(len(d));margin=stats.t.ppf(.975,len(d)-1)*se;p=float(stats.ttest_1samp(d,0).pvalue);better=(d<0).mean()*100 if metric=='mean_delay' else (d>0).mean()*100
 return {'scenario':scenario,'comparison':f'{left}_minus_{right}','metric':metric,'mean_difference':d.mean(),'ci95_low':d.mean()-margin,'ci95_high':d.mean()+margin,'left_better_fraction_percent':better,'p_value':p,'paired_replications':len(d)}
def main():
 data=load_experiment_config();names=list(data['tuning_scenarios']);assert SEEDS==tuple(range(data['seeds']['reserved_final_start'],data['seeds']['reserved_final_end']+1));assert not set(SEEDS)&set(range(data['seeds']['tuning_start'],data['seeds']['tuning_end']+1));assert (ROOT/'results/pre_final_literature_wpt/frozen_methodology.json').exists();catalog=pd.DataFrame(scenario_catalog_rows(data));assert (catalog.logistics_utilization<1).all();RAW.mkdir(parents=True,exist_ok=True);raw_path=RAW/'replication_metrics.csv';solver_path=RAW/'c5_solver_calls.csv';rows=pd.read_csv(raw_path).to_dict('records') if raw_path.exists() else [];solver=pd.read_csv(solver_path).to_dict('records') if solver_path.exists() else [];done={(str(r['scenario']),int(r['replication'])) for r in rows if sum(1 for x in rows if str(x['scenario'])==str(r['scenario']) and int(x['replication'])==int(r['replication']))==len(STRATEGIES)};jobs=[(n,s) for n in names for s in SEEDS if (n,s) not in done]
 for start in range(0,len(jobs),20):
  batch=jobs[start:start+20]
  with ProcessPoolExecutor(max_workers=4) as ex:
   fs=[ex.submit(run_one,*j) for j in batch]
   for f in as_completed(fs):r,x=f.result();rows+=r;solver+=x
  rows.sort(key=lambda x:(str(x['scenario']),str(x['strategy']),int(x['replication'])));solver.sort(key=lambda x:(str(x['scenario']),int(x['replication']),float(x['time_s'])));write(raw_path,rows);write(solver_path,solver);print(f'FINAL {min(start+len(batch),len(jobs))}/{len(jobs)} new blocks; rows={len(rows)}',flush=True)
 expected=len(names)*len(SEEDS)*len(STRATEGIES);assert len(rows)==expected,(len(rows),expected)
 df=pd.DataFrame(rows);metrics=['mean_delay','urgent_on_time_rate','completion_rate','battery_delivered_energy','wpt_loss','fleet_min_soc','low_soc_stops','charging_wait','priority_decisions','total_priority_computation_time_s','mean_decision_latency_ms','p95_decision_latency_ms','max_decision_latency_ms','solver_calls_per_replication','solver_total_time_per_replication_s','solver_mean_time_per_call_ms','solver_p95_time_per_call_ms','solver_max_time_per_call_ms'];summary=df.groupby(['scenario','strategy'])[metrics].agg(['mean','std']).reset_index();summary.columns=['_'.join(c).strip('_') for c in summary.columns];SUM.mkdir(parents=True,exist_ok=True);summary.to_csv(SUM/'strategy_summary.csv',index=False);catalog.to_csv(SUM/'rho_catalog.csv',index=False);pairs=[paired(df,'C4','C3',metric,n) for n in names for metric in ('mean_delay','urgent_on_time_rate')];p=pd.DataFrame(pairs);order=p.p_value.sort_values().index;q=np.empty(len(p));prev=1.0
 for rank,idx in reversed(list(enumerate(order,1))):prev=min(prev,float(p.loc[idx,'p_value'])*len(p)/rank);q[idx]=prev
 p['bh_adjusted_p_value']=q;STATS.mkdir(parents=True,exist_ok=True);p.to_csv(STATS/'paired_statistics.csv',index=False);manifest={'frozen_pre_final_sha':subprocess.check_output(['git','rev-parse','archive/pre-literature-wpt-final-20260929'],cwd=ROOT,text=True).strip(),'final_seeds':list(SEEDS),'final_seed_authorized_by_user':True,'final_execution_count':1,'c4_weights':json.loads((ROOT/'results/pre_final_literature_wpt/frozen_c4_parameters.json').read_text())['weights'],'c5_scales':json.loads((ROOT/'results/pre_final_literature_wpt/frozen_c5_parameters.json').read_text())['scales'],'physical_model':'experimentally measured reference WPT condition model; delivered power and eta separated','final_results_commit_sha':None};(OUT/'final_result_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(OUT/'FINAL_EVALUATION_REPORT.md').write_text('# [3]-Based WPT Unseen Final Evaluation\n\nFinal seeds 8007–8056 were executed once with CRN across strategies. Interpretation must use the paired statistics and summary artifacts. C5 is a rolling-horizon MILP reference, not a global optimum.\n');print('FINAL_COMPLETE',len(rows),flush=True)
if __name__=='__main__':main()
