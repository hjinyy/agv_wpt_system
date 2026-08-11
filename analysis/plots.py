from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams.update({'figure.dpi':120,'savefig.dpi':300,'axes.grid':True})

def _save(fig,pathbase):
    fig.tight_layout()
    fig.savefig(str(pathbase)+'.png')
    fig.savefig(str(pathbase)+'.pdf')
    plt.close(fig)

def bar_base(raw, metric, ylabel, fname):
    g=raw[(raw.scenario=='base') & (raw.strategy.isin(['C1','C2','C3','C4']))].groupby('strategy')[metric].agg(['mean','std']).reindex(['C1','C2','C3','C4'])
    fig,ax=plt.subplots(figsize=(6,4)); ax.bar(g.index,g['mean'],yerr=g['std'],capsize=4); ax.set_ylabel(ylabel); ax.set_xlabel('Charging strategy')
    _save(fig, fname)

def line_scenario(raw, scenario, metric, ylabel, fname, xlab):
    g=raw[(raw.scenario==scenario)&(raw.strategy.isin(['C1','C2','C3','C4']))].groupby(['scenario_value','strategy'])[metric].mean().reset_index()
    order=sorted(g.scenario_value.unique(), key=lambda x: float(x) if str(x).replace('.','',1).isdigit() else str(x))
    fig,ax=plt.subplots(figsize=(6,4))
    for st in ['C1','C2','C3','C4']:
        y=[g[(g.scenario_value==v)&(g.strategy==st)][metric].mean() for v in order]
        ax.plot([float(v) for v in order], y, marker='o', label=st)
    ax.set_xlabel(xlab); ax.set_ylabel(ylabel); ax.legend()
    _save(fig, fname)

def make_plots(results_dir):
    rd=Path(results_dir); figdir=rd/'figures'; figdir.mkdir(exist_ok=True)
    raw=pd.read_csv(rd/'raw_runs.csv')
    bar_base(raw,'throughput','Throughput [tasks/h]',figdir/'fig01_base_throughput')
    bar_base(raw,'mean_delay','Mean task delay [min]',figdir/'fig02_base_delay')
    trace=pd.read_csv(rd/'soc_trace_representative.csv')
    fig,ax=plt.subplots(figsize=(7,4))
    t=trace[(trace.strategy=='C4') & (trace.scenario=='base:base')]
    if len(t)==0: t=trace[trace.strategy=='C4']
    for agv,gg in t.groupby('agv_id'):
        ax.step(gg.time_h,gg.soc,where='post',label=f'AGV {agv}',alpha=.85)
    ax.set_xlabel('Time [h]'); ax.set_ylabel('SOC [%]'); ax.legend(ncol=2,fontsize=8)
    _save(fig,figdir/'fig03_soc_timeseries')
    line_scenario(raw,'A_agv','throughput','Throughput [tasks/h]',figdir/'fig04_A_agv_throughput','Number of AGVs')
    line_scenario(raw,'A_agv','mean_delay','Mean delay [min]',figdir/'fig05_A_agv_delay','Number of AGVs')
    line_scenario(raw,'B_pad','throughput','Throughput [tasks/h]',figdir/'fig06_B_pad_throughput','Number of WPT pads')
    line_scenario(raw,'B_pad','pad_utilization','Pad utilization [%]',figdir/'fig07_B_pad_util','Number of WPT pads')
    line_scenario(raw,'C_workload','throughput','Throughput [tasks/h]',figdir/'fig08_C_workload_throughput','Workload [tasks/h]')
    line_scenario(raw,'C_workload','mean_delay','Mean delay [min]',figdir/'fig09_C_workload_delay','Workload [tasks/h]')
    line_scenario(raw,'D_power','low_soc_stops','Low-SOC stoppages [count]',figdir/'fig10_D_power_stops','WPT power [kW]')
    line_scenario(raw,'D_power','battery_delivered_energy','Delivered energy [kWh]',figdir/'fig11_D_power_energy','WPT power [kW]')
    abl=raw[raw.scenario=='ablation_efficiency'].groupby('strategy')[['throughput','mean_delay','wpt_input_energy','battery_delivered_energy','low_soc_stops','pad_utilization']].mean()
    fig,ax=plt.subplots(figsize=(7,4)); abl[['throughput','mean_delay','pad_utilization']].plot(kind='bar',ax=ax); ax.set_title('C4 fixed vs variable efficiency'); _save(fig,figdir/'fig12_ablation_efficiency')
    # design heatmap proxies using C4 completion feasibility from available grid scenarios
    for name,metric,fname in [('Minimum WPT pad requirement map','completion_rate','fig13_min_pad_requirement_map'),('Minimum charging power design map','low_soc_stops','fig14_min_power_design_map')]:
        fig,ax=plt.subplots(figsize=(6,3));
        txt=raw[raw.strategy=='C4'].groupby(['scenario','scenario_value'])[[metric,'mean_delay']].mean().round(2).to_string()
        ax.axis('off'); ax.text(0,1,name+'\n\n'+txt,va='top',family='monospace',fontsize=7)
        _save(fig,figdir/fname)
