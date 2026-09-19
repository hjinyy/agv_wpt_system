import json,subprocess
from pathlib import Path
import numpy as np,pandas as pd
from run_unseen_final import OUT,RAW,SUM,STATS,SEEDS,FROZEN,paired,load_experiment_config

def main():
 SUM.mkdir(parents=True,exist_ok=True);STATS.mkdir(parents=True,exist_ok=True);df=pd.read_csv(RAW/'replication_metrics.csv');sol=pd.read_csv(RAW/'c5_solver_calls.csv'); metrics=['mean_delay','urgent_on_time_rate','completion_rate','battery_delivered_energy','wpt_loss','fleet_min_soc','critical_soc_event_count','low_soc_stops','charging_wait','priority_decisions','total_priority_computation_time_s','mean_decision_latency_ms','p95_decision_latency_ms','max_decision_latency_ms','solver_calls_per_replication','solver_total_time_per_replication_s','solver_mean_time_per_call_ms','solver_p95_time_per_call_ms','solver_max_time_per_call_ms'];summary=df.groupby(['scenario','strategy'])[metrics].agg(['mean','std']).reset_index();summary.columns=['_'.join(x).strip('_') for x in summary.columns];summary.to_csv(SUM/'strategy_summary.csv',index=False); data=load_experiment_config(); from rho_pipeline import scenario_catalog_rows; pd.DataFrame(scenario_catalog_rows(data)).to_csv(SUM/'rho_catalog.csv',index=False)
 ps=[]
 for r in ['C1','C2','C3','C5']:
  for m in ['mean_delay','urgent_on_time_rate']:ps.append(paired(df,'C4',r,m,'primary'))
 for n in ['stress_non_binding','stress_near_transition','stress_transition','primary','stress_strongly_constrained']:
  for m in ['mean_delay','urgent_on_time_rate']:ps.append(paired(df,'C4','C3',m,n))
 p=pd.DataFrame(ps);order=p.p_value.sort_values().index;q=np.empty(len(p));prev=1.
 for rank,idx in reversed(list(enumerate(order,1))):prev=min(prev,float(p.loc[idx,'p_value'])*len(p)/rank);q[idx]=prev
 p['bh_adjusted_p_value']=q;p.to_csv(STATS/'paired_statistics.csv',index=False)
 man={'frozen_experiment_sha':FROZEN,'final_results_commit_sha':None,'final_seeds':list(SEEDS),'C4_weights':json.load(open('results/tuning/frozen_c4_parameters.json'))['weights'],'C5_scales':json.load(open('results/pre_final/frozen_c5_parameters.json'))['scales'],'scenario_parameters':data['scenarios'],'rho_taxonomy':'<0.7 non-binding; [0.7,0.9) near-transition; [0.9,1.0) transition; [1.0,1.3) moderately constrained; >=1.3 strongly constrained','software':{'python':subprocess.check_output(['.venv/bin/python','--version'],text=True).strip()},'one_time_execution':True,'raw_execution_complete_before_finalization_fix':True};(OUT/'final_result_manifest.json').write_text(json.dumps(man,indent=2));(OUT/'FINAL_EVALUATION_REPORT.md').write_text('# Unseen Final Evaluation\n\nSeeds 6007–6056 were executed once. Raw outputs were complete before a directory-finalization failure; summaries here were regenerated exclusively from those raw CSVs, with no rerun.\n')
 print('FINALIZE_OK',len(df),len(sol),len(p))
if __name__=='__main__':main()
