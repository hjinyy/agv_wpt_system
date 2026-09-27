from __future__ import annotations
import pandas as pd
from pathlib import Path
from rho_pipeline import load_experiment_config,scenario_catalog_rows,scenarios,tuning_seeds,configuration_for,FEATURES
from simulation.literature_wpt import condition_at_index
from v2_runner import generate_common
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results'/'pre_final_literature_wpt'
def main():
 data=load_experiment_config();base={r['scenario']:r for r in scenario_catalog_rows(data)};rows=[]
 for name,sc in scenarios(data).items():
  cfg=configuration_for(sc,{f:1/len(FEATURES) for f in FEATURES},data);powers=[]
  for seed in tuning_seeds(data):
   tasks,_=generate_common(cfg,seed,distances=sc.distances,urgent_ratio=sc.urgent_ratio)
   powers += [condition_at_index(t.realized_eta_state).charge_power_kw for t in tasks]
  mean=sum(powers)/len(powers);row=dict(base[name]);row['condition_draw_count']=len(powers);row['mean_available_charge_power_kw_simulation']=mean;row['rho_simulation_based']=row['analytical_demand_kw']/(row['n_pads']*mean);row['rho_region_simulation_based']=row['rho_region'] if row['rho_region']==('non_binding' if row['rho_simulation_based']<.7 else 'near_transition' if row['rho_simulation_based']<.9 else 'transition' if row['rho_simulation_based']<1 else 'moderately_constrained' if row['rho_simulation_based']<1.3 else 'strongly_constrained') else 'TAXONOMY_MISMATCH';rows.append(row)
 pd.DataFrame(rows).to_csv(OUT/'frozen_rho_catalog.csv',index=False);assert all(r['rho_region_simulation_based']!='TAXONOMY_MISMATCH' for r in rows);print('RHO_SIMULATION_AUDIT_OK',len(rows))
if __name__=='__main__':main()
