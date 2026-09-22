import pandas as pd,numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from simulation.final_wpt import physical_efficiency_values,load_final_wpt_configuration
O=Path('results/final_unseen');F=O/'figures';F.mkdir(exist_ok=True);raw=pd.read_csv(O/'raw/replication_metrics.csv');summ=pd.read_csv(O/'summary/strategy_summary.csv');pair=pd.read_csv(O/'statistics/paired_statistics.csv');cat=pd.read_csv(O/'summary/rho_catalog.csv')
def save(fig,n):fig.savefig(F/(n+'.png'),dpi=180,bbox_inches='tight');fig.savefig(F/(n+'.pdf'),bbox_inches='tight');plt.close(fig)
fig,ax=plt.subplots();ax.scatter(cat.rho_analytical,cat.logistics_utilization);[ax.annotate(r.scenario,(r.rho_analytical,r.logistics_utilization)) for _,r in cat.iterrows()];ax.axvline(1,color='k',ls='--');ax.set(xlabel='Charging adequacy rho',ylabel='Logistics utilization');save(fig,'Figure1_rho_map')
p=raw[raw.scenario=='primary'].groupby('strategy')[['mean_delay','urgent_on_time_rate']].mean();fig,ax=plt.subplots();ax.scatter(p.mean_delay,p.urgent_on_time_rate);[ax.annotate(i,(r.mean_delay,r.urgent_on_time_rate)) for i,r in p.iterrows()];ax.set(xlabel='Mean task delay [min]',ylabel='Urgent on-time [%]');save(fig,'Figure2_primary_tradeoff')
d=pair[(pair.comparison=='C4_minus_C3')&(pair.metric=='mean_delay')];fig,ax=plt.subplots();y=np.arange(len(d));ax.errorbar(d.mean_difference,y,xerr=[d.mean_difference-d.ci95_low,d.ci95_high-d.mean_difference],fmt='o');ax.axvline(0,color='k');ax.set(yticks=y,yticklabels=d.scenario,xlabel='C4-C3 delay difference [min]');save(fig,'Figure3_c4_c3_rho')
d=pair[(pair.scenario=='primary')&(pair.metric=='mean_delay')];fig,ax=plt.subplots();y=np.arange(len(d));ax.errorbar(d.mean_difference,y,xerr=[d.mean_difference-d.ci95_low,d.ci95_high-d.mean_difference],fmt='o');ax.axvline(0,color='k');ax.set(yticks=y,yticklabels=d.comparison,xlabel='C4-other delay difference [min]');save(fig,'Figure4_primary_forest')
from generate_wpt_nominal_validation import generate_figure
# Figure 5 is the nominal-3-kW analytical model plus qualitative 50-W prototype panel.
generate_figure()
c4=raw[(raw.scenario=='primary')&(raw.strategy=='C4')].mean(numeric_only=True);c5=raw[(raw.scenario=='primary')&(raw.strategy=='C5')].mean(numeric_only=True);fig,ax=plt.subplots();ax.bar(['C4 priority decision','C5 MILP solve'],[c4.mean_decision_latency_ms,c5.solver_mean_time_per_call_ms]);ax.set_ylabel('Latency [ms/event]');save(fig,'Figure6_computational_cost')
