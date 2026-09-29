"""Create paper figures/tables from frozen final CSVs only. Never runs a simulation."""
from __future__ import annotations
import gzip, json, shutil
from math import sqrt
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
from scipy import stats
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
FINAL=ROOT/'results/final_literature_wpt'
PRE=ROOT/'results/pre_final_literature_wpt'
OUT=FINAL/'paper_outputs'; FIG=OUT/'figures'; DATA=OUT/'figure_data'; TABLE=OUT/'tables'; CAP=OUT/'captions'
ORDER=['non_binding_good','near_transition_good','moderately_constrained_moderate','strongly_constrained_moderate','strongly_constrained_severe']
DISPLAY={'non_binding_good':'Non-binding\nGood','near_transition_good':'Near-transition\nGood','moderately_constrained_moderate':'Moderate\nModerate','strongly_constrained_moderate':'Strong\nModerate','strongly_constrained_severe':'Strong\nSevere'}
COLORS={'C1':'#4D4D4D','C2':'#0072B2','C3':'#009E73','C4':'#D55E00','C5':'#7B61A8'}
MARKERS={'C1':'o','C2':'s','C3':'^','C4':'D','C5':'P'}
STRATEGIES=['C1','C2','C3','C4','C5']


def setup():
    for p in [FIG,DATA,TABLE,CAP]: p.mkdir(parents=True,exist_ok=True)
    mpl.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.labelsize':10.5,'xtick.labelsize':9,'ytick.labelsize':9,'legend.fontsize':9,'axes.linewidth':0.7,'lines.linewidth':1.8,'lines.markersize':6.5,'pdf.fonttype':42,'ps.fonttype':42,'figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white'})

def style(ax):
    ax.grid(axis='y',color='#D9D9D9',lw=.55,alpha=.8); ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)

def save(fig,name):
    fig.savefig(FIG/f'{name}.pdf',bbox_inches='tight'); fig.savefig(FIG/f'{name}.png',dpi=600,bbox_inches='tight'); plt.close(fig)

def md(df,path):
    path.write_text(df.to_markdown(index=False)+'\n',encoding='utf8')

def latex(df,path,caption,label):
    cols=[str(c).replace('_','\\_') for c in df.columns]
    def esc(v): return str(v).replace('&','\\&').replace('%','\\%').replace('_','\\_')
    lines=['\\begin{table}[t]','\\centering',f'\\caption{{{caption}}}',f'\\label{{{label}}}','\\begin{tabular}{'+'l'*len(cols)+'}','\\hline',' & '.join(cols)+' \\\\','\\hline']
    lines += [' & '.join(esc(v) for v in row)+' \\\\' for row in df.itertuples(index=False,name=None)]
    lines += ['\\hline','\\end{tabular}','\\end{table}']
    path.write_text('\\n'.join(lines)+'\\n',encoding='utf8')

def ci(x):
    x=np.asarray(x,float); n=len(x); h=stats.t.ppf(.975,n-1)*x.std(ddof=1)/sqrt(n); return x.mean(),h

def paired(raw,left,right,metric,scenario):
    a=raw[(raw.scenario==scenario)&(raw.strategy==left)].set_index('replication')[metric]
    b=raw[(raw.scenario==scenario)&(raw.strategy==right)].set_index('replication')[metric]
    d=(a-b).to_numpy(float); mean,h=ci(d); p=float(stats.ttest_1samp(d,0).pvalue)
    return {'Scenario':scenario,'Comparator':f'{left} − {right}','Metric':metric,'Mean paired difference':mean,'CI low':mean-h,'CI high':mean+h,'p_value':p,'Replications':len(d)}

def bh(df):
    out=df.copy(); order=out.p_value.sort_values().index; q=np.empty(len(out)); prev=1.
    for rank,idx in reversed(list(enumerate(order,1))): prev=min(prev,float(out.loc[idx,'p_value'])*len(out)/rank);q[idx]=prev
    out['BH-adjusted p-value']=q; return out

def audit(raw,summary,paired_csv,catalog,manifest,cfg):
    errors=[]
    if len(raw)!=1250: errors.append(f'raw rows={len(raw)}, expected 1250')
    if set(raw.strategy)!=set(STRATEGIES): errors.append('strategy set mismatch')
    if set(raw.scenario)!=set(ORDER): errors.append('scenario set mismatch')
    if not (raw.groupby(['scenario','strategy']).size()==50).all(): errors.append('replication cell count mismatch')
    if set(raw.replication)!=set(range(8007,8057)): errors.append('final seed set mismatch')
    if manifest['final_seeds']!=list(range(8007,8057)): errors.append('manifest seed mismatch')
    if set(catalog.scenario)!=set(ORDER): errors.append('rho catalog scenario mismatch')
    for _,r in catalog.iterrows():
        c=cfg['scenarios'][r.scenario]
        for k in ['n_agvs','n_pads','task_arrival_rate_per_h','wpt_power_kw','urgent_ratio']:
            if not np.isclose(float(r[k]),float(c[k])): errors.append(f'catalog config mismatch {r.scenario} {k}')
    metrics=['mean_delay','urgent_on_time_rate','completion_rate','fleet_min_soc']
    agg=raw.groupby(['scenario','strategy'])[metrics].agg(['mean','std'])
    for _,r in summary.iterrows():
        idx=(r.scenario,r.strategy)
        for m in metrics:
            if not np.isclose(r[f'{m}_mean'],agg.loc[idx,(m,'mean')],rtol=1e-10,atol=1e-10):errors.append(f'summary mean mismatch {idx} {m}')
            if not np.isclose(r[f'{m}_std'],agg.loc[idx,(m,'std')],rtol=1e-10,atol=1e-10):errors.append(f'summary std mismatch {idx} {m}')
    for _,r in paired_csv.iterrows():
        calc=paired(raw,'C4','C3',r.metric,r.scenario)
        for src,dst in [('mean_difference','Mean paired difference'),('ci95_low','CI low'),('ci95_high','CI high'),('p_value','p_value')]:
            if not np.isclose(float(r[src]),float(calc[dst]),rtol=1e-9,atol=1e-9):errors.append(f'paired mismatch {r.scenario} {r.metric} {src}')
    if errors: raise RuntimeError('AUDIT FAILED: '+'; '.join(errors))

def figure1(table):
    d=table[table.delta_mm<=250].copy(); d['available_charging_power_kw']=3*d.pout_mean_kw/d.pout_mean_kw.iloc[0]; d.to_csv(DATA/'Figure1_data.csv',index=False)
    fig,axs=plt.subplots(1,2,figsize=(7.2,2.85),constrained_layout=True)
    axs[0].plot(d.delta_mm,d.available_charging_power_kw,color='#0072B2',marker='o',label='Scaled available charging power')
    axs[0].set(xlabel='Lateral misalignment, δ [mm]',ylabel='Available charging power [kW]',ylim=(0,3.2));axs[0].legend(frameon=False,loc='upper right');style(axs[0]);axs[0].text(-.15,1.04,'(a)',transform=axs[0].transAxes,fontweight='bold',fontsize=11)
    axs[1].plot(d.delta_mm,d.eta_mean_percent,color='#009E73',marker='s',label='Measured WPT efficiency')
    axs[1].set(xlabel='Lateral misalignment, δ [mm]',ylabel='Measured WPT efficiency [%]',ylim=(0,82));axs[1].legend(frameon=False,loc='upper right');style(axs[1]);axs[1].text(-.15,1.04,'(b)',transform=axs[1].transAxes,fontweight='bold',fontsize=11)
    save(fig,'Figure1_WPT_Physical_Characteristics')

def figure2(catalog):
    d=catalog.set_index('scenario').loc[ORDER].reset_index().copy(); d['display_label']=d.scenario.map(DISPLAY); d.to_csv(DATA/'Figure2_data.csv',index=False)
    fig,ax=plt.subplots(figsize=(7.1,3.35),constrained_layout=True); bands=[(0,.7,'Non-binding'),(.7,.9,'Near-transition'),(.9,1,'Transition'),(1,1.3,'Moderately\nconstrained'),(1.3,2.35,'Strongly\nconstrained')]
    for i,(a,b,label) in enumerate(bands): ax.axvspan(a,b,color=['#EAF3F8','#F8F5E8','#F7EFE5','#FBEEE8','#F9E8E8'][i],alpha=.75)
    for x in [.7,.9,1,1.3]:ax.axvline(x,color='#888',lw=.7,ls='--')
    for _,r in d.iterrows(): ax.scatter(r.rho_analytical,r.mean_available_charge_power_kw,s=55,color='#D55E00',edgecolor='black',lw=.45,zorder=3);ax.annotate(r.display_label,(r.rho_analytical,r.mean_available_charge_power_kw),xytext=(5,5),textcoords='offset points',fontsize=8)
    ax.set(xlabel='Charging adequacy, ρ',ylabel='Mean available charging power [kW]',xlim=(0,2.35),ylim=(0,3.0));style(ax);save(fig,'Figure2_Operating_Region_Map')

def figure3(raw,catalog):
    rho=catalog.set_index('scenario').loc[ORDER].rho_analytical.to_numpy(); rows=[]
    for sc in ORDER:
      for st in STRATEGIES:
       x=raw[(raw.scenario==sc)&(raw.strategy==st)]
       for metric in ['mean_delay','urgent_on_time_rate','completion_rate']:
        m,h=ci(x[metric]);rows.append({'scenario':sc,'strategy':st,'metric':metric,'mean':m,'ci95_halfwidth':h,'rho':float(catalog.set_index('scenario').loc[sc,'rho_analytical'])})
    d=pd.DataFrame(rows);d.to_csv(DATA/'Figure3_data.csv',index=False)
    fig,axs=plt.subplots(3,1,figsize=(7.1,7.0),sharex=True,constrained_layout=True); specs=[('mean_delay','Mean task delay [min]',1/60),('urgent_on_time_rate','Urgent on-time rate [%]',1),('completion_rate','Completion rate [%]',1)]
    xx=np.arange(len(ORDER))
    for ax,(metric,ylabel,scale) in zip(axs,specs):
      for st in STRATEGIES:
       q=d[(d.strategy==st)&(d.metric==metric)].set_index('scenario').loc[ORDER]
       ax.errorbar(xx,q['mean']*scale,yerr=q.ci95_halfwidth*scale,color=COLORS[st],marker=MARKERS[st],capthick=.8,capsize=2.5,label=st)
      ax.set_ylabel(ylabel);style(ax)
    axs[0].legend(ncol=5,frameon=False,loc='upper left');axs[2].set_xticks(xx,[f'{v:.2f}\n{DISPLAY[s].split(chr(10))[1]}' for v,s in zip(rho,ORDER)]);axs[2].set_xlabel('Charging adequacy, ρ\n(alignment condition shown below)')
    for ax,label in zip(axs,['(a)','(b)','(c)']):ax.text(-.09,1.02,label,transform=ax.transAxes,fontweight='bold',fontsize=11)
    save(fig,'Figure3_Strategy_Performance')

def figure4(p):
    d=p.copy();d['display_label']=d.scenario.map(DISPLAY);d.to_csv(DATA/'Figure4_data.csv',index=False); fig,axs=plt.subplots(1,2,figsize=(7.2,3.3),sharey=True,constrained_layout=True)
    for ax,metric,xlab in zip(axs,['mean_delay','urgent_on_time_rate'],['Paired delay difference, C4 − C3 [s]','Paired urgent on-time difference, C4 − C3 [pp]']):
      q=d[d.metric==metric].set_index('scenario').loc[ORDER];y=np.arange(len(ORDER)); sig=q['bh_adjusted_p_value'].to_numpy()<.05
      ax.axvline(0,color='#555',lw=.8); ax.errorbar(q.mean_difference,y,xerr=[q.mean_difference-q.ci95_low,q.ci95_high-q.mean_difference],fmt='none',ecolor='#555',capsize=3,lw=1)
      ax.scatter(q.mean_difference,y,c=np.where(sig,'#D55E00','#FFFFFF'),edgecolor='#D55E00',marker='D',s=45,zorder=3)
      ax.set(xlabel=xlab,yticks=y,yticklabels=[DISPLAY[s].replace('\n',' / ') for s in ORDER]);ax.invert_yaxis();style(ax)
    axs[0].text(-.12,1.03,'(a)',transform=axs[0].transAxes,fontweight='bold',fontsize=11);axs[1].text(-.12,1.03,'(b)',transform=axs[1].transAxes,fontweight='bold',fontsize=11)
    save(fig,'Figure4_C4_C3_Paired_Comparison')

def figure5(feature,ablation):
    f=feature[feature.ablation=='full'].set_index('scenario').loc[ORDER].reset_index(); a=ablation[ablation.scenario.isin(['near_transition_good','moderately_constrained_moderate','strongly_constrained_severe'])].groupby(['scenario','ablation']).mean(numeric_only=True).reset_index(); f.to_csv(DATA/'Figure5_feature_data.csv',index=False);a.to_csv(DATA/'Figure5_ablation_data.csv',index=False); fig5data=pd.concat([pd.DataFrame({'panel':'physical_feature','scenario':f.scenario,'series':'overall','value':f.f_P_std_mean}),pd.DataFrame({'panel':'physical_feature','scenario':f.scenario,'series':'contention_only','value':f.f_P_std_contention_mean}),pd.DataFrame({'panel':'ablation','scenario':a.scenario,'series':a.ablation,'value':a.mean_delay})],ignore_index=True); fig5data.to_csv(DATA/'Figure5_data.csv',index=False)
    fig,axs=plt.subplots(1,2,figsize=(8.25,3.15),constrained_layout=True);x=np.arange(len(ORDER));w=.36
    short=['NB\nGood','Near\nGood','Moderate\nModerate','Strong\nModerate','Strong\nSevere']
    axs[0].bar(x-w/2,f.f_P_std_mean,w,label='Overall decisions',color='#6BAED6',edgecolor='black',lw=.35);axs[0].bar(x+w/2,f.f_P_std_contention_mean,w,label='Contention-only',color='#E6550D',edgecolor='black',lw=.35);axs[0].set(xticks=x,xticklabels=short,ylabel='Std. of predicted feature, $f_P$');axs[0].legend(frameon=False,fontsize=8);style(axs[0])
    names=['full','no_P','soc_only','no_deadline'];labels=['Full C4','No-P','SOC-only','No-deadline'];scs=['near_transition_good','moderately_constrained_moderate','strongly_constrained_severe'];x=np.arange(len(scs));w=.18
    for i,(name,label) in enumerate(zip(names,labels)):
      q=a[a.ablation==name].set_index('scenario').reindex(scs);axs[1].bar(x+(i-1.5)*w,q.mean_delay,w,label=label,color=['#D55E00','#E69F00','#4D4D4D','#0072B2'][i],edgecolor='black',lw=.25)
    axs[1].set(xticks=x,xticklabels=[DISPLAY[s].replace('\n','\n') for s in scs],ylabel='Mean task delay [s]');axs[1].legend(frameon=False,fontsize=7.6,ncol=2);style(axs[1])
    for ax,label in zip(axs,['(a)','(b)']):ax.text(-.14,1.04,label,transform=ax.transAxes,fontweight='bold',fontsize=11)
    save(fig,'Figure5_C4_Feature_Ablation')

def figure6(raw,solver):
    c4=raw[raw.strategy=='C4'][['mean_decision_latency_ms','p95_decision_latency_ms','max_decision_latency_ms']].mean(); c5=np.array([solver.solve_time_s.mean()*1000,solver.solve_time_s.quantile(.95)*1000,solver.solve_time_s.max()*1000]);d=pd.DataFrame({'operation':['C4 priority evaluation']*3+['C5 MILP solve']*3,'statistic':['Mean','P95','Max']*2,'time_ms':list(c4)+list(c5)});d.to_csv(DATA/'Figure6_data.csv',index=False)
    fig,ax=plt.subplots(figsize=(6.6,2.9),constrained_layout=True);y=np.arange(3);ax.plot(d[d.operation=='C4 priority evaluation'].time_ms,y,marker='D',color=COLORS['C4'],label='C4 priority evaluation');ax.plot(d[d.operation=='C5 MILP solve'].time_ms,y,marker='P',color=COLORS['C5'],label='C5 rolling-MILP solve');ax.set(xscale='log',yticks=y,yticklabels=['Mean','P95','Max'],xlabel='Computation time per decision/call [ms]');ax.legend(frameon=False,loc='lower right');style(ax);save(fig,'Figure6_Computational_Cost')

def tables(raw,catalog,cfg,paired_all,feature,ablation,solver):
    base=yaml.safe_load((ROOT/'config.yaml').read_text())['base']; c4=json.loads((PRE/'frozen_c4_parameters.json').read_text())['weights']; c5=json.loads((PRE/'frozen_c5_parameters.json').read_text())['scales']
    t1=pd.DataFrame([['Simulation','Operation horizon','—','24 h','Frozen final design'],['Simulation','Final replications','—','50','Seeds 8007–8056'],['AGV','Speed','$v$','1.0 m/s',''],['Service','Picking service','$T_{pick}$','45 s',''],['Service','Staging service','$T_{stage}$','45 s',''],['Battery','Capacity','—','5 kWh',''],['Battery','Initial SOC','—','Uniform(50%, 80%)',''],['Battery','Minimum / critical / maximum SOC','—','15% / 20% / 90%',''],['Energy','Traction / auxiliary','—','0.20 kWh km$^{-1}$ / 0.05 kW',''],['Energy','Pad detour','—','5 m one-way',''],['WPT','Nominal pad rating','—','3.0 kW','[3]-normalized availability'],['Deadline','Urgent / normal slack','—','240 s / 480 s','$T_{min}+slack$'],['C4','Frozen weights','—','0.00 / 0.70 / 0.00 / 0.00 / 0.30','SOC / E / idle / P / deadline'],['C5','Horizon / slot','—','15 min / 60 s',''],['C5','Time limit / MIP gap','—','0.10 s / 0.001',''] ],columns=['Category','Parameter','Symbol','Value','Note'])
    t2=catalog.set_index('scenario').loc[ORDER].reset_index();t2=pd.DataFrame({'Scenario':[DISPLAY[x].replace('\n',' / ') for x in t2.scenario],'AGVs':t2.n_agvs.astype(int),'Pads':t2.n_pads.astype(int),'Task rate [h$^{-1}$]':t2.task_arrival_rate_per_h.astype(int),'Distances [m]':t2.distances_m,'Urgent ratio':t2.urgent_ratio.map(lambda x:f'{x:.2f}'),'Alignment':t2.physical_condition.str.title(),'Mean $P_{charge}$ [kW]':t2.mean_available_charge_power_kw.map(lambda x:f'{x:.3f}'),'$\\rho$':t2.rho_analytical.map(lambda x:f'{x:.3f}'),'Logistics utilization':t2.logistics_utilization.map(lambda x:f'{x:.3f}')})
    perf=raw.groupby(['scenario','strategy'])[['mean_delay','urgent_on_time_rate','completion_rate','fleet_min_soc']].agg(['mean','std']).reset_index();perf.columns=['scenario','strategy','delay_mean','delay_std','urgent_mean','urgent_std','completion_mean','completion_std','soc_mean','soc_std'];t3=pd.DataFrame({'Scenario':perf.scenario.map(lambda x:DISPLAY[x].replace('\n',' / ')),'Strategy':perf.strategy,'Delay [s]':perf.apply(lambda r:f'{r.delay_mean:.1f} ± {r.delay_std:.1f}',axis=1),'Urgent on-time [%]':perf.apply(lambda r:f'{r.urgent_mean:.2f} ± {r.urgent_std:.2f}',axis=1),'Completion [%]':perf.apply(lambda r:f'{r.completion_mean:.2f} ± {r.completion_std:.2f}',axis=1),'Min SOC [%]':perf.apply(lambda r:f'{r.soc_mean:.2f} ± {r.soc_std:.2f}',axis=1)})
    t4=paired_all.copy();t4['Scenario']=t4.Scenario.map(lambda x:DISPLAY[x].replace('\n',' / '));t4['Metric']=t4.Metric.map({'mean_delay':'Mean delay [s]','urgent_on_time_rate':'Urgent on-time [pp]'});t4['Difference']=t4['Mean paired difference'].map(lambda x:f'{x:.3f}');t4['95% CI']=t4.apply(lambda r:f'[{r["CI low"]:.3f}, {r["CI high"]:.3f}]',axis=1);t4['BH p']=t4['BH-adjusted p-value'].map(lambda x:f'{x:.3g}')
    def interp(r):
      lo,hi=r['CI low'],r['CI high']; delay=r.Metric=='mean_delay'
      if lo<=0<=hi:return 'No resolved difference'
      if delay:return 'Lower delay for C4' if hi<0 else 'Higher delay for C4'
      return 'Higher urgent on-time for C4' if lo>0 else 'Lower urgent on-time for C4'
    t4['Interpretation']=t4.apply(interp,axis=1);t4=t4[['Scenario','Comparator','Metric','Difference','95% CI','BH p','Interpretation']]
    f=feature[feature.ablation=='full'].set_index('scenario').loc[ORDER].reset_index();sel=raw[raw.strategy=='C4'].groupby('scenario').different_decision_rate_C4_vs_C3.mean().reindex(ORDER)*100;t5a=pd.DataFrame({'Feature':['SOC','Next-task energy','Idle','Predicted WPT power','Deadline risk'],'Weight':[c4['soc'],c4['next_task_energy'],c4['idle'],c4['charging_power_quality'],c4['deadline']]});t5b=pd.DataFrame({'Scenario':[DISPLAY[s].replace('\n',' / ') for s in ORDER],'Overall $f_P$ std':f.f_P_std_mean,'Contention $f_P$ std':f.f_P_std_contention_mean,'C3-vs-C4 selection difference [%]':sel.to_numpy()});t5c=ablation[ablation.scenario.isin(ORDER)].groupby(['scenario','ablation']).mean(numeric_only=True).reset_index().pivot(index='scenario',columns='ablation',values='mean_delay').reindex(ORDER).reset_index();t5c['Scenario']=t5c.scenario.map(lambda x:DISPLAY[x].replace('\n',' / '));t5c=t5c[['Scenario','full','no_P','soc_only','no_deadline']];t5=pd.concat([t5a.assign(Section='Frozen C4 weights'),t5b.assign(Section='Physical-feature diagnostics'),t5c.assign(Section='Tuning-only ablation')],ignore_index=True,sort=False)
    t6=pd.DataFrame({'Metric':['Total MILP calls','Mean solve time/call','P95 solve time/call','Maximum solve time/call','Time-limit hits','Infeasible calls','Fallback calls','Simulation failures','Low-SOC stops'],'Final value':[f'{len(solver):,}',f'{solver.solve_time_s.mean()*1000:.3f} ms',f'{solver.solve_time_s.quantile(.95)*1000:.3f} ms',f'{solver.solve_time_s.max()*1000:.3f} ms',int(solver.time_limit_hit.sum()),int(solver.infeasible.sum()),int(solver.fallback_used.sum()),int(raw.simulation_failure.sum()),int(raw.low_soc_stops.sum())]})
    for n,d,caption,label in [('Table1_Simulation_Inputs',t1,'Simulation inputs for the frozen final evaluation.','tab:inputs'),('Table2_Scenario_Catalog',t2,'Final scenario catalog and charging adequacy.','tab:scenarios'),('Table3_Final_Performance',t3,'Final strategy performance; entries are mean ± standard deviation over 50 final replications.','tab:performance'),('Table4_Paired_Statistics',t4,'Paired C4 comparisons using common-random-number replications and BH correction.','tab:paired'),('Table5_C4_Diagnostics',t5,'Frozen C4 weights, physical-feature diagnostics, and tuning-only ablation summary.','tab:c4diagnostics'),('Table5_C4_Diagnostics_Weights',t5a,'Frozen C4 feature weights.','tab:c4weights'),('Table5_C4_Diagnostics_Features',t5b,'Physical-feature diagnostics.','tab:c4features'),('Table5_C4_Diagnostics_Ablation',t5c,'C4 ablation mean delay [s] on tuning-only data.','tab:c4ablation'),('Table6_C5_Computation',t6,'Final C5 computational and solver summary.','tab:c5cost')]:
      d.to_csv(TABLE/f'{n}.csv',index=False);md(d,TABLE/f'{n}.md');latex(d,TABLE/f'{n}.tex',caption,label)

def captions():
    (CAP/'FIGURE_TABLE_CAPTIONS.md').write_text('''# Figure and table captions\n\n**Figure 1.** Experimental [3]-based WPT characteristics used by the frozen condition model. (a) Battery-side available charging power after 3-kW normalization of the mean measured output-power ratio. (b) Mean measured WPT efficiency. Extreme 250–350 mm failure states are excluded from the main plot.\n\n**Figure 2.** Final scenarios in charging-adequacy and WPT-condition space. Shaded bands indicate the frozen rho taxonomy; all scenarios have logistics utilization below one.\n\n**Figure 3.** C1–C5 performance across final operating regions. Points are means over 50 final replications and error bars are 95% confidence intervals of replication means. Alignment conditions are shown below rho ticks.\n\n**Figure 4.** Paired C4−C3 final comparisons. Points denote paired mean differences across 50 common-random-number replications and bars indicate 95% confidence intervals. Negative delay differences favor lower C4 delay; positive urgent-on-time differences favor C4 urgent service. Filled markers have Benjamini–Hochberg-adjusted p<0.05.\n\n**Figure 5.** C4 physical-feature and ablation diagnostics from tuning-only data. (a) The predicted charging-power feature varies, especially under contention. (b) The predicted-power coefficient was zero after tuning; deadline removal, not physical variability removal, materially changes delay.\n\n**Figure 6.** Computational cost. C4 priority evaluation and C5 rolling-MILP solve are different computational operations; the comparison illustrates implementation burden rather than identical call semantics.\n\n**Table 1.** Frozen simulation inputs. **Table 2.** Final scenario catalog. **Table 3.** Final C1–C5 outcomes. **Table 4.** Paired C4 comparisons. **Table 5.** C4 diagnostic and ablation evidence. **Table 6.** Final C5 solver cost and safety status.\n''')

def validate():
    required=[DATA/f'Figure{i}_data.csv' for i in range(1,7)]
    for p in required:
      assert p.exists(),p
      d=pd.read_csv(p); assert np.isfinite(d.select_dtypes(include=np.number).to_numpy()).all(),p
    for n in ['Figure1_WPT_Physical_Characteristics','Figure2_Operating_Region_Map','Figure3_Strategy_Performance','Figure4_C4_C3_Paired_Comparison','Figure5_C4_Feature_Ablation','Figure6_Computational_Cost']:
      for ext in ['pdf','png']:
       p=FIG/f'{n}.{ext}';assert p.exists() and p.stat().st_size>10_000,p

def main():
    setup(); raw=pd.read_csv(FINAL/'raw/replication_metrics.csv');summary=pd.read_csv(FINAL/'summary/strategy_summary.csv');pold=pd.read_csv(FINAL/'statistics/paired_statistics.csv');catalog=pd.read_csv(FINAL/'summary/rho_catalog.csv');manifest=json.loads((FINAL/'final_result_manifest.json').read_text());cfg=yaml.safe_load((ROOT/'config/rho_redesign.yaml').read_text());table=pd.read_csv(ROOT/cfg['physical_source']['table_path']);feature=pd.read_csv(PRE/'physical_feature_summary.csv');ablation=pd.read_csv(PRE/'c4_ablation_results.csv');
    with gzip.open(FINAL/'raw/c5_solver_calls.csv.gz','rt') as h: solver=pd.read_csv(h)
    audit(raw,summary,pold,catalog,manifest,cfg)
    pairs=bh(pd.DataFrame([paired(raw,'C4',other,m,sc) for other in ['C1','C2','C3','C5'] for sc in ORDER for m in ['mean_delay','urgent_on_time_rate']]))
    pairs.to_csv(TABLE/'Table4_Paired_Statistics_All_Comparators.csv',index=False)
    figure1(table);figure2(catalog);figure3(raw,catalog);figure4(pold);figure5(feature,ablation);figure6(raw,solver);tables(raw,catalog,cfg,pairs,feature,ablation,solver);captions();validate()
    (OUT/'PAPER_OUTPUT_VALIDATION.md').write_text('# Publication-output validation\n\n- Raw final rows: 1,250; all 25 scenario-strategy cells have 50 replications.\n- Strategy/scenario/final-seed sets, paired C4–C3 statistics, and final summary means/stds were recomputed from raw CSV and matched.\n- Final rho catalog was checked against the frozen scenario configuration.\n- Figure plot-data CSVs contain finite values and required PDF/600-dpi PNG outputs exist.\n- No simulator, task generator, C4/C5 tuner, or final-runner function is imported or invoked by this script.\n')
    print('PAPER_OUTPUT_AUDIT_AND_RENDER_OK')
if __name__=='__main__': main()
