from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from rho_pipeline import configuration_for, load_experiment_config, scenario_catalog_rows, scenarios, FEATURES
from simulation.literature_wpt import distribution_moments, measurement_table
from v2_runner import task_time
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'results'/'pre_tuning_literature_wpt'
def main():
 OUT.mkdir(parents=True,exist_ok=True); data=load_experiment_config(); table=measurement_table(); table.to_csv(OUT/'literature_wpt_lookup_derived.csv',index=False)
 catalog=pd.DataFrame(scenario_catalog_rows(data));catalog.to_csv(OUT/'rho_alignment_scenario_catalog.csv',index=False)
 rows=[]
 for scenario in scenarios(data).values():
  cfg=configuration_for(scenario,{f:1/len(FEATURES) for f in FEATURES},data)
  for distance in scenario.distances_m:
   min_service=task_time(cfg,distance); rows.append({'scenario':scenario.name,'distance_m':distance,'minimum_service_s':min_service,'legacy_urgent_deadline_s':240.,'legacy_urgent_structurally_infeasible':min_service>240.,'provisional_urgent_deadline_s':min_service+cfg['deadline_model']['urgent_slack_s'],'provisional_normal_deadline_s':min_service+cfg['deadline_model']['normal_slack_s']})
 deadline=pd.DataFrame(rows);deadline.to_csv(OUT/'deadline_feasibility_audit.csv',index=False)
 condition={name:distribution_moments(raw['probabilities']) for name,raw in data['alignment_conditions'].items()};(OUT/'alignment_condition_moments.json').write_text(json.dumps(condition,indent=2)+'\n')
 lines=['# [3]-based WPT pre-tuning audit','', 'No tuning or unseen-final simulation was executed.','', '## Deadline finding', f"- Legacy urgent deadline is structurally infeasible for {int(deadline.legacy_urgent_structurally_infeasible.sum())}/{len(deadline)} scenario-distance rows because its fixed 240 s budget is shorter than irreducible service time.", '- Provisional rule: `deadline = arrival + minimum_service_time(distance) + urgency_slack`; urgent/normal slacks are 240/480 s and require parameter-freeze approval.','', '## rho definition','- `rho = lambda * E_task_avg / (N_pad * E[P_charge(delta)])`; eta is not multiplied again because `P_charge` is battery-side delivered power.','', '## Alignment scenarios','- Good/moderate/severe are controlled sensitivity conditions, not empirical AGV docking distributions. Extreme 250–350 mm is failure sensitivity only.','', '## Catalog','',catalog.to_markdown(index=False,floatfmt='.4f'),'','## Expected C4 tuning count','- Coarse 5-feature simplex, step 0.25: 70 candidates × 5 scenarios × 50 seeds = 17,500 C4 simulations.','- C1/C2/C3 reference: 3 × 5 × 50 = 750 simulations.','- Local 0.05 one-transfer neighborhood: at most 21 candidates × 5 × 50 = 5,250 C4 simulations.','- Maximum C4-plus-reference total before C5 revalidation: 23,500 simulations.']
 (OUT/'PRE_TUNING_AUDIT.md').write_text('\n'.join(lines)+'\n')
 print('PRE_TUNING_AUDIT_OK',len(catalog),len(deadline))
if __name__=='__main__':main()
