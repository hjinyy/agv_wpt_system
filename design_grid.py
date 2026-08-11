from pathlib import Path
from copy import deepcopy
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from main import load_config, run_one
from simulation.environment import common_random_inputs
ROOT=Path(__file__).resolve().parent; RESULTS=ROOT/'results'

def main():
    cfg=load_config(); reps=int(cfg['replications'])
    agvs=cfg['_raw']['scenarios']['A_agv']; workloads=cfg['_raw']['scenarios']['C_workload']; pads=cfg['_raw']['scenarios']['B_pad']; powers=cfg['_raw']['scenarios']['D_power']
    rows=[]
    for n in agvs:
        for wl in workloads:
            for mode, vals in [('pad',pads),('power',powers)]:
                for v in vals:
                    c=deepcopy(cfg); c['n_agvs']=int(n); c['task_arrival_rate_per_h']=float(wl)
                    if mode=='pad': c['n_pads']=int(v); c['wpt_power_kw']=3.0
                    else: c['n_pads']=2; c['wpt_power_kw']=float(v)
                    for r in range(reps):
                        seed=cfg['seed0']+r; tasks,init,etas=common_random_inputs(c,seed)
                        m,_,_,_,_=run_one(c,'C4',seed,f'design_{mode}:{v}',tasks,init,etas)
                        rows.append({**m,'replication':r,'agv_number':n,'workload':wl,'design_mode':mode,'candidate_value':v})
    df=pd.DataFrame(rows); df.to_csv(RESULTS/'design_grid_raw.csv',index=False)
    crits=[]
    for mode,gmode in df.groupby('design_mode'):
        for (n,wl,val),g in gmode.groupby(['agv_number','workload','candidate_value']):
            crits.append({'design_mode':mode,'agv_number':n,'workload':wl,'candidate_value':val,
                          'mean_completion_rate':g.completion_rate.mean(),'stop_free_fraction':(g.low_soc_stops==0).mean(),'mean_delay':g.mean_delay.mean(),
                          'feasible_99':(g.completion_rate.mean()>=99 and (g.low_soc_stops==0).mean()>=0.95),
                          'feasible_97':(g.completion_rate.mean()>=97 and (g.low_soc_stops==0).mean()>=0.95),
                          'feasible_95':(g.completion_rate.mean()>=95 and (g.low_soc_stops==0).mean()>=0.95)})
    cr=pd.DataFrame(crits).sort_values(['design_mode','agv_number','workload','candidate_value']); cr.to_csv(RESULTS/'design_grid_summary.csv',index=False)
    final=[]
    for n in agvs:
        for wl in workloads:
            gp=cr[(cr.design_mode=='pad')&(cr.agv_number==n)&(cr.workload==wl)&(cr.feasible_99)]
            gw=cr[(cr.design_mode=='power')&(cr.agv_number==n)&(cr.workload==wl)&(cr.feasible_99)]
            minpad=gp.candidate_value.min() if len(gp) else np.nan
            minpwr=gw.candidate_value.min() if len(gw) else np.nan
            # metrics at chosen paired criteria when available
            src=gp[gp.candidate_value==minpad].head(1) if len(gp) else cr[(cr.design_mode=='pad')&(cr.agv_number==n)&(cr.workload==wl)].sort_values('mean_completion_rate',ascending=False).head(1)
            final.append({'AGV number':n,'Workload':wl,'Minimum WPT pads':minpad,'Minimum WPT power':minpwr,
                          'Completion rate':float(src.mean_completion_rate.iloc[0]) if len(src) else np.nan,
                          'Mean delay':float(src.mean_delay.iloc[0]) if len(src) else np.nan})
    ft=pd.DataFrame(final); ft.to_csv(RESULTS/'final_design_table.csv',index=False)
    # heatmaps
    figdir=RESULTS/'figures'; figdir.mkdir(exist_ok=True)
    for col,title,fname in [('Minimum WPT pads','Minimum WPT pad requirement map','fig13_min_pad_requirement_map'),('Minimum WPT power','Minimum charging power design map','fig14_min_power_design_map')]:
        mat=ft.pivot(index='AGV number',columns='Workload',values=col)
        fig,ax=plt.subplots(figsize=(5,4)); im=ax.imshow(mat.values, cmap='viridis')
        ax.set_xticks(range(len(mat.columns)),mat.columns); ax.set_yticks(range(len(mat.index)),mat.index)
        ax.set_xlabel('Workload [tasks/h]'); ax.set_ylabel('AGV number'); ax.set_title(title)
        for i in range(mat.shape[0]):
            for j in range(mat.shape[1]): ax.text(j,i,'NA' if pd.isna(mat.iloc[i,j]) else f'{mat.iloc[i,j]:.0f}',ha='center',va='center',color='white')
        fig.colorbar(im,ax=ax); fig.tight_layout(); fig.savefig(figdir/f'{fname}.png',dpi=300); fig.savefig(figdir/f'{fname}.pdf'); plt.close(fig)
    with open(RESULTS/'REPORT.md','a',encoding='utf-8') as f:
        f.write('\n\n## Final design criteria table (C4, 99% criterion)\n\n')
        f.write(ft.to_markdown(index=False))
        f.write('\n')
    print(f'wrote design grid {len(df)} runs')
if __name__=='__main__': main()
