import sys
sys.path.insert(0, '/home/hy/wpt_agv_opportunity_charging')
from pathlib import Path
import pandas as pd
from v2_runner import load_cfg, generate_common
from v3_runner import V3Sim

root=Path('/home/hy/wpt_agv_opportunity_charging')
outdir=root/'results_v3_ablation_no_prior'
outdir.mkdir(exist_ok=True)
cfg0=load_cfg()
cfg0.update({'n_agvs':5,'n_pads':1,'task_arrival_rate_per_h':90,'wpt_power_kw':3})
dist={1:20,2:25,3:30,4:35,5:40}
rows=[]; solver=[]; sched=[]
for r in range(20):
    cfg=dict(cfg0)
    cfg['c5_priority_weight']=0.0
    cfg['c5_conflict_weight']=6.0
    cfg['c5_reserve_slack_weight']=6.0
    cfg['c5_early_charge_weight']=0.8
    tasks, init = generate_common(cfg, cfg['seed0']+r, distances=dist, urgent_ratio=0.2)
    lookup={t.task_id:i for i,t in enumerate(tasks)}
    sim=V3Sim(cfg,'C5',cfg['seed0']+r,tasks,init,'C5_no_prior_20rep',variable_eta=True,task_index_lookup=lookup,predicted_eta_mode='variable',realized_eta_mode='variable')
    row=sim.run(); rows.append(row); solver.extend(sim.solver_rows); sched.extend(sim.milp_schedule_rows)
    print(f'C5-no-prior {r+1}/20 done', flush=True)
pd.DataFrame(rows).to_csv(outdir/'c5_no_prior_20rep_results.csv', index=False)
pd.DataFrame(solver).to_csv(outdir/'c5_no_prior_solver_statistics.csv', index=False)
pd.DataFrame(sched).to_csv(outdir/'c5_no_prior_milp_schedule.csv', index=False)
summary=pd.DataFrame(rows).mean(numeric_only=True).to_frame('C5_no_prior_20rep_mean')
summary.to_csv(outdir/'c5_no_prior_20rep_summary.csv')
print('\nSUMMARY')
print(pd.DataFrame(rows)[['mean_delay','urgent_on_time_rate','completion_rate','wpt_loss','fleet_min_soc','charging_wait','solver_calls','solver_computation_time_s','solver_reserve_slack_total','solver_task_slack_total']].mean().round(4).to_string())
print('\nSOLVER')
df=pd.DataFrame(solver)
print(df[['solve_time_s','fallback_used','infeasible','time_limit_hit','safety_slack_total','reserve_slack_total','task_slack_sum','available_agv_slot_pairs','forecast_busy_agv_slot_pairs']].agg(['mean','sum','max']).round(6).to_string())
print('schedule_rows', len(sched), 'first_slot_rows', sum(1 for x in sched if x.get('execute_first_slot')))
