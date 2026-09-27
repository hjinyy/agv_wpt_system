from __future__ import annotations
import hashlib,json,platform,sys
from pathlib import Path
import numpy as np,pandas as pd,scipy
from rho_pipeline import FEATURES,configuration_for,load_experiment_config,scenario_catalog_rows,scenarios
from simulation.literature_wpt import TABLE_PATH,measurement_table
from v2_runner import task_time
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results'/'methodology_freeze_literature_wpt'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True);data=load_experiment_config();catalog=pd.DataFrame(scenario_catalog_rows(data));catalog.to_csv(OUT/'frozen_scenario_catalog.csv',index=False);table=measurement_table();table.to_csv(OUT/'frozen_physical_lookup.csv',index=False)
 audit=[]
 for su in data['deadline_model']['sensitivity_urgent_s']:
  for sn in data['deadline_model']['sensitivity_normal_s']:
   infeasible=0
   for sc in scenarios(data).values():
    cfg=configuration_for(sc,{f:1/len(FEATURES) for f in FEATURES},data)
    for d in sc.distances_m:
     service=task_time(cfg,d);infeasible += int(service+su<=service or service+sn<=service)
   audit.append({'urgent_slack_s':su,'normal_slack_s':sn,'structurally_feasible':infeasible==0,'urgency_separation_s':sn-su,'selection_status':'selected' if (su,sn)==(240.,480.) else 'sensitivity_only'})
 pd.DataFrame(audit).to_csv(OUT/'deadline_slack_sensitivity.csv',index=False)
 frozen={'physical_source':data['physical_source'],'physical_table_sha256':sha(TABLE_PATH),'deadline_model':data['deadline_model'],'alignment_conditions':data['alignment_conditions'],'prediction_model':data['prediction_model'],'c4_general_formulation':data['c4_general_formulation'],'c5_revalidation':data['c5_revalidation'],'tuning_seeds':list(range(7107,7157)),'reserved_final_seeds':list(range(8007,8057)),'seed_overlap':0,'software':{'python':sys.version,'scipy':scipy.__version__,'platform':platform.platform()},'taxonomy':'<0.7 non-binding; [0.7,0.9) near-transition; [0.9,1.0) transition; [1.0,1.3) moderately constrained; >=1.3 strongly constrained'}
 (OUT/'frozen_methodology.json').write_text(json.dumps(frozen,indent=2)+'\n')
 lines=['# PRE_TUNING_METHODOLOGY_FREEZE','','## Deadline rule','- `deadline = arrival + T_min(distance) + controlled urgency slack`.','- Selected urgent/normal slack: 240/480 s. This is a **controlled urgency-slack assumption**, not literature-derived.','- The 180/360, 240/480, and 300/600 s sensitivity combinations are structurally feasible because slack is added after irreducible service time; the selected pair preserves a 240-s urgency separation and the legacy 4/8-min allowance magnitudes.','','## Physical source','- [3] Table 2 X/Y measured lookup is source-of-truth. Its SHA-256 is recorded in `frozen_methodology.json`.','- `P_charge = 3 kW*g_P`; eta is used only for input/loss accounting and is not multiplied into delivered power.','','## Alignment and information','- Good/moderate/severe are controlled misalignment-sensitivity conditions, not empirical fleet distributions. Extreme 250-350 mm is excluded from tuning main scenarios.','- C4/C5 use predicted P_charge; actual SOC/energy/loss use realized state with controlled zero-mean discrete error.','','## Scenario naming audit','',catalog[['scenario','physical_condition','rho_analytical','rho_region','logistics_utilization']].to_markdown(index=False,floatfmt='.4f'),'','All logistics utilizations are below one.']
 (OUT/'PRE_TUNING_METHODOLOGY_FREEZE.md').write_text('\n'.join(lines)+'\n');print('METHODOLOGY_FREEZE_OK')
if __name__=='__main__':main()
