from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

ROOT = Path('/home/hy/wpt_agv_opportunity_charging')
SRC = ROOT / 'results_v3'
OUT = ROOT / 'results_v3_figures'
OUT.mkdir(exist_ok=True)

# HARD PROVENANCE RULE: this script is for V3 only.
REQUIRED = [
    'base_case_runs.csv', 'c1_c5_results.csv', 'stress_grid.csv',
    'priority_feature_statistics.csv', 'priority_features_raw.csv', 'decision_diagnostics.csv'
]
missing = [f for f in REQUIRED if not (SRC / f).exists()]
if missing:
    raise FileNotFoundError(f'Missing V3 inputs in {SRC}: {missing}')
if SRC.name != 'results_v3':
    raise RuntimeError(f'Invalid source directory for V3 figures: {SRC}')

base = pd.read_csv(SRC / 'base_case_runs.csv')
challenge = pd.read_csv(SRC / 'c1_c5_results.csv')
stress = pd.read_csv(SRC / 'stress_grid.csv')
features_stats = pd.read_csv(SRC / 'priority_feature_statistics.csv')
features_raw = pd.read_csv(SRC / 'priority_features_raw.csv')
decisions = pd.read_csv(SRC / 'decision_diagnostics.csv')

STRATEGIES = ['C1', 'C2', 'C3', 'C4', 'C5']
STRATEGIES_4 = ['C1', 'C2', 'C3', 'C4']
COLORS = {'C1': '#6c757d', 'C2': '#4c78a8', 'C3': '#59a14f', 'C4': '#e15759', 'C5': '#7b3294'}
MARKERS = {'C1': 'o', 'C2': 's', 'C3': '^', 'C4': 'D', 'C5': 'P'}
plt.rcParams.update({
    'font.size': 10, 'axes.labelsize': 10, 'axes.titlesize': 11, 'legend.fontsize': 8.5,
    'xtick.labelsize': 9, 'ytick.labelsize': 9, 'figure.dpi': 140, 'savefig.dpi': 350,
    'axes.spines.top': False, 'axes.grid': True, 'grid.alpha': 0.25, 'grid.linewidth': 0.6,
})

def save(fig, name):
    fig.savefig(OUT / f'{name}.png', bbox_inches='tight')
    fig.savefig(OUT / f'{name}.pdf', bbox_inches='tight')
    plt.close(fig)

def mean_ci(df, metric):
    g = df.groupby('strategy')[metric]
    out = g.agg(['mean','std','count']).reindex(STRATEGIES)
    out['ci95'] = 1.96 * out['std'] / np.sqrt(out['count'])
    return out.reset_index()

def fig1():
    b_delay = mean_ci(base, 'mean_delay'); b_comp = mean_ci(base, 'completion_rate')
    c_delay = mean_ci(challenge, 'mean_delay'); c_urgent = mean_ci(challenge, 'urgent_on_time_rate')
    b_delay.to_csv(OUT/'plot_data_Figure1_base_delay.csv', index=False)
    b_comp.to_csv(OUT/'plot_data_Figure1_base_completion.csv', index=False)
    c_delay.to_csv(OUT/'plot_data_Figure1_challenge_delay.csv', index=False)
    c_urgent.to_csv(OUT/'plot_data_Figure1_challenge_urgent.csv', index=False)
    fig, axes = plt.subplots(1,2,figsize=(12.4,4.2))
    for ax, d1, d2, title, y2label in [
        (axes[0], b_delay, b_comp, '(a) V3 Base Case', 'Completion rate [%]'),
        (axes[1], c_delay, c_urgent, '(b) V3 Primary Challenge', 'Urgent on-time completion [%]')]:
        x = np.arange(len(STRATEGIES)); w=.35
        ax.bar(x-w/2, d1['mean'], width=w, color=[COLORS[s] for s in STRATEGIES], alpha=.80, yerr=d1['ci95'], capsize=3, label='Mean task delay')
        ax.set_ylabel('Mean task delay [min]')
        ax.set_xticks(x, STRATEGIES)
        ax.set_title(title, fontweight='bold')
        ax2 = ax.twinx()
        ax2.plot(x+w/2, d2['mean'], color='black', marker='o', lw=1.4, label=y2label)
        ax2.errorbar(x+w/2, d2['mean'], yerr=d2['ci95'], fmt='none', ecolor='black', capsize=3, lw=.8)
        ax2.set_ylabel(y2label)
        ax2.grid(False)
        lines, labels = ax.get_legend_handles_labels(); lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines+lines2, labels+labels2, frameon=False, loc='upper left')
    fig.suptitle('Figure 1. V3 Base vs Primary Challenge performance using corrected C4 and C5 benchmark', y=1.02, fontweight='bold')
    save(fig, 'Figure1_V3_Base_vs_Challenge')

def fig2():
    metrics = challenge.groupby('strategy')[['mean_delay','urgent_on_time_rate','completion_rate','wpt_loss']].agg(['mean','std']).reindex(STRATEGIES)
    rows=[]
    for s in STRATEGIES:
        rows.append({'strategy':s,
                     'mean_delay':metrics.loc[s,('mean_delay','mean')],
                     'urgent_on_time_rate':metrics.loc[s,('urgent_on_time_rate','mean')],
                     'completion_rate':metrics.loc[s,('completion_rate','mean')],
                     'wpt_loss':metrics.loc[s,('wpt_loss','mean')]})
    df=pd.DataFrame(rows); df.to_csv(OUT/'plot_data_Figure2_tradeoff.csv',index=False)
    fig, ax = plt.subplots(figsize=(6.6,4.8))
    sizes = 35 + (df['completion_rate'] - df['completion_rate'].min()) / max(1e-9, (df['completion_rate'].max()-df['completion_rate'].min())) * 180
    for _, r in df.iterrows():
        ax.scatter(r.mean_delay, r.urgent_on_time_rate, s=float(sizes.loc[_]), color=COLORS[r.strategy], marker=MARKERS[r.strategy], edgecolor='black', linewidth=.7, alpha=.88)
        ax.annotate(r.strategy, (r.mean_delay, r.urgent_on_time_rate), xytext=(6,5), textcoords='offset points', fontweight='bold')
    ax.set_xlabel('Mean task delay [min]')
    ax.set_ylabel('Urgent-task on-time completion [%]')
    ax.set_title('Figure 2. V3 trade-off map: C3 beats C4 on primary challenge, C5 is benchmark', loc='left', fontweight='bold')
    ax.text(.02,.02,'Point size encodes completion rate [%]', transform=ax.transAxes, fontsize=8, color='0.25')
    save(fig, 'Figure2_V3_Challenge_Tradeoff')

def fig3():
    c4 = challenge[challenge.strategy=='C4']
    diag = pd.DataFrame({
        'metric':['Contention events / rep.', 'C4 differs from C3 [%]'],
        'mean':[c4['charging_contention_events'].mean(), c4['different_decision_rate_C4_vs_C3'].mean()],
        'ci95':[1.96*c4['charging_contention_events'].std()/np.sqrt(len(c4)), 1.96*c4['different_decision_rate_C4_vs_C3'].std()/np.sqrt(len(c4))]
    })
    feat_cols = [('1-SOC','one_minus_soc_std'),('E_next','E_next_std'),('T_idle','T_idle_std'),('eta_WPT','eta_WPT_std'),('D','D_std')]
    fs = features_stats[features_stats['strategy']=='C4']
    fdat = pd.DataFrame({'feature':[x[0] for x in feat_cols], 'std_mean':[fs[x[1]].mean() for x in feat_cols], 'std_ci95':[1.96*fs[x[1]].std()/np.sqrt(len(fs)) for x in feat_cols]})
    diag.to_csv(OUT/'plot_data_Figure3_contention.csv', index=False)
    fdat.to_csv(OUT/'plot_data_Figure3_feature_std.csv', index=False)
    fig, axes = plt.subplots(1,2,figsize=(11.2,4.1))
    axes[0].bar(diag['metric'], diag['mean'], yerr=diag['ci95'], color=['#9ecae1','#f4a261'], edgecolor='black', capsize=4)
    axes[0].set_title('(a) V3 contention diagnostics', fontweight='bold')
    axes[0].set_ylabel('Mean ± 95% CI')
    axes[0].tick_params(axis='x', rotation=15)
    axes[1].bar(fdat['feature'], fdat['std_mean'], yerr=fdat['std_ci95'], color='#bdbdbd', edgecolor='black', capsize=4)
    axes[1].set_title('(b) C4 feature standard deviation', fontweight='bold')
    axes[1].set_ylabel('Mean within-replication std. [normalized]')
    fig.suptitle('Figure 3. V3 corrected C4 uses non-identical candidate features under contention', y=1.02, fontweight='bold')
    save(fig, 'Figure3_V3_C4_Diagnostics')

def fig4():
    # Positive value means C4 has lower mean delay than C3. Negative means C4 is worse.
    rows=[]
    for (wl,pad,pw), g in stress.groupby(['workload','n_pads','wpt_power_kw']):
        gg=g.groupby('strategy').agg(mean_delay=('mean_delay','mean'), urgent=('urgent_on_time_rate','mean')).reindex(STRATEGIES_4)
        if pd.notna(gg.loc['C3','mean_delay']) and pd.notna(gg.loc['C4','mean_delay']):
            delay_imp=(gg.loc['C3','mean_delay']-gg.loc['C4','mean_delay'])/abs(gg.loc['C3','mean_delay'])*100
            urgent_diff=gg.loc['C4','urgent']-gg.loc['C3','urgent']
            rows.append({'workload':wl,'n_pads':pad,'wpt_power_kw':pw,'c4_vs_c3_delay_improvement_pct':delay_imp,'c4_minus_c3_urgent_pp':urgent_diff})
    df=pd.DataFrame(rows); df.to_csv(OUT/'plot_data_Figure4_v3_stress_c4_c3.csv',index=False)
    vmax=max(1, np.nanmax(np.abs(df['c4_vs_c3_delay_improvement_pct'])))
    norm=TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
    fig, axes=plt.subplots(1,3,figsize=(13.0,4.0),sharey=True)
    for ax,pw in zip(axes,[1,3,5]):
        sub=df[df.wpt_power_kw==pw]
        mat=sub.pivot(index='n_pads',columns='workload',values='c4_vs_c3_delay_improvement_pct').sort_index()
        ann=sub.pivot(index='n_pads',columns='workload',values='c4_minus_c3_urgent_pp').sort_index()
        im=ax.imshow(mat.values, cmap='RdBu', norm=norm, aspect='auto')
        ax.set_xticks(range(len(mat.columns)), [str(int(c)) for c in mat.columns])
        ax.set_yticks(range(len(mat.index)), [str(int(i)) for i in mat.index])
        ax.set_xlabel('Workload [tasks/h]')
        if ax is axes[0]: ax.set_ylabel('Number of WPT pads')
        ax.set_title(f'Power = {pw} kW', fontweight='bold')
        for i in range(mat.shape[0]):
            for j in range(mat.shape[1]):
                val=mat.iloc[i,j]; u=ann.iloc[i,j]
                ax.text(j,i,f'{val:+.1f}%\n({u:+.1f} pp)',ha='center',va='center',fontsize=8,color='black')
    cb=fig.colorbar(im,ax=axes.ravel().tolist(),fraction=.035,pad=.03)
    cb.set_label('C4 vs C3 delay improvement [%]\npositive = C4 lower delay')
    fig.suptitle('Figure 4. V3 stress grid: corrected C4 advantage/disadvantage is condition-dependent', y=1.03, fontweight='bold')
    save(fig, 'Figure4_V3_C4_vs_C3_Stress_Grid')

def write_docs():
    captions = '''# V3 Main Figure Captions\n\n## Figure 1. V3 Base vs Primary Challenge performance\nThis figure uses only `results_v3/base_case_runs.csv` and `results_v3/c1_c5_results.csv`. Panel (a) shows that the corrected C4 does not create artificial differences in the homogeneous Base Case. Panel (b) shows the V3 Primary Challenge after the per-AGV next-task fix and includes C5 as a rolling MILP benchmark.\n\n## Figure 2. V3 Primary Challenge trade-off map\nThis scatter plot uses `results_v3/c1_c5_results.csv`. The x-axis is mean task delay and the y-axis is urgent-task on-time completion; marker size encodes completion rate. In V3, C3 outperforms C4 on the Primary Challenge urgent/on-time trade-off, while C5 provides a lower-delay optimization benchmark.\n\n## Figure 3. V3 corrected C4 diagnostics\nThis figure uses `results_v3/c1_c5_results.csv` and `results_v3/priority_feature_statistics.csv`. Panel (a) reports contention frequency and how often C4 selects a different AGV than C3. Panel (b) verifies that corrected C4 candidate features have real nonzero variance, especially `E_next`, rather than all candidates sharing one `next_task`.\n\n## Figure 4. V3 C4-vs-C3 stress grid\nThis figure uses `results_v3/stress_grid.csv`, generated with the corrected V3 C4. Cell color is the C4 delay improvement relative to C3; positive values mean C4 has lower delay, negative values mean C4 is worse. Parenthesized cell annotations give C4 minus C3 urgent on-time difference in percentage points. This replaces the invalid V2-based advantage heatmap.\n'''
    (OUT/'CAPTIONS.md').write_text(captions,encoding='utf-8')
    selection = '''# V3 Figure Provenance and Selection\n\n## Critical provenance rule\n\nThese figures read only from `results_v3/`. The previous `create_v3_main_figures.py` incorrectly read `results_v2/`; that output is invalid for final V3 reporting.\n\n## V3 input files\n\n- `results_v3/base_case_runs.csv`\n- `results_v3/c1_c5_results.csv`\n- `results_v3/stress_grid.csv`\n- `results_v3/priority_feature_statistics.csv`\n- `results_v3/priority_features_raw.csv`\n- `results_v3/decision_diagnostics.csv`\n\n## Why these four figures\n\n1. Figure 1 establishes Base vs Challenge behavior under the corrected V3 model.\n2. Figure 2 honestly shows the V3 trade-off, including that C3 can beat C4 in Primary Challenge.\n3. Figure 3 verifies the actual C4 fix: AGV-specific feature variance under contention.\n4. Figure 4 replaces the invalid V2 heatmap with a V3 stress-grid C4-vs-C3 map, including negative regions.\n\nNo V2 stress-grid or V2 priority-feature data are used.\n'''
    (OUT/'FIGURE_SELECTION.md').write_text(selection,encoding='utf-8')

if __name__ == '__main__':
    fig1(); fig2(); fig3(); fig4(); write_docs()
    print(f'Generated V3-only figures in {OUT}')
