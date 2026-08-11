from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.colors import TwoSlopeNorm

ROOT = Path('/home/hy/wpt_agv_opportunity_charging')
SRC = ROOT / 'results_v2'
OUT = ROOT / 'results_v3_figures'
OUT.mkdir(exist_ok=True)

# Data sources explicitly used for v3 main figures
base = pd.read_csv(SRC / 'base_case_runs.csv')
challenge = pd.read_csv(SRC / 'challenge_runs.csv')
stress = pd.read_csv(SRC / 'stress_grid.csv')
features = pd.read_csv(SRC / 'priority_features.csv')
feature_sample = pd.read_csv(SRC / 'priority_features_raw_sample.csv')
decisions = pd.read_csv(SRC / 'decision_diagnostics.csv')

STRATEGIES = ['C1', 'C2', 'C3', 'C4']
COLORS = {'C1': '#6c757d', 'C2': '#4c78a8', 'C3': '#59a14f', 'C4': '#e15759'}
MARKERS = {'C1': 'o', 'C2': 's', 'C3': '^', 'C4': 'D'}
plt.rcParams.update({
    'font.size': 10,
    'axes.labelsize': 10,
    'axes.titlesize': 11,
    'legend.fontsize': 9,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'figure.dpi': 140,
    'savefig.dpi': 350,
    'axes.spines.top': False,
    'axes.grid': True,
    'grid.alpha': 0.25,
    'grid.linewidth': 0.6,
})

def ci95(x):
    x = pd.Series(x).dropna()
    if len(x) <= 1:
        return 0.0
    return 1.96 * x.std(ddof=1) / np.sqrt(len(x))

def summarize(df, metrics):
    rows = []
    for st in STRATEGIES:
        g = df[df.strategy == st]
        row = {'strategy': st, 'n': len(g)}
        for m in metrics:
            row[m + '_mean'] = g[m].mean()
            row[m + '_ci95'] = ci95(g[m])
            row[m + '_std'] = g[m].std(ddof=1)
        rows.append(row)
    return pd.DataFrame(rows)

def label_strategy(st):
    return {'C1': 'C1\nThreshold', 'C2': 'C2\nAlways', 'C3': 'C3\nLow-SOC', 'C4': 'C4\nPriority'}[st]

def save(fig, name):
    fig.savefig(OUT / f'{name}.png', bbox_inches='tight')
    fig.savefig(OUT / f'{name}.pdf', bbox_inches='tight')
    plt.close(fig)

# ---------- Figure 1 ----------
base_sum = summarize(base, ['mean_delay', 'completion_rate'])
chal_sum = summarize(challenge, ['mean_delay', 'urgent_on_time_rate'])
fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.2))
for ax, df, title, right_metric, right_label in [
    (axes[0], base_sum, '(a) Original Base Case', 'completion_rate', 'Completion rate [%]'),
    (axes[1], chal_sum, '(b) Scheduling Challenge Case', 'urgent_on_time_rate', 'Urgent on-time completion [%]'),
]:
    x = np.arange(len(STRATEGIES))
    ax.bar(x, df['mean_delay_mean'], yerr=df['mean_delay_ci95'], capsize=3,
           color=[COLORS[s] for s in STRATEGIES], alpha=0.82, edgecolor='black', linewidth=0.6,
           label='Mean task delay')
    ax.set_xticks(x, [label_strategy(s) for s in STRATEGIES])
    ax.set_ylabel('Mean task delay [min]')
    ax.set_title(title, loc='left', fontweight='bold')
    ax.set_axisbelow(True)
    ax2 = ax.twinx()
    ax2.errorbar(x, df[f'{right_metric}_mean'], yerr=df[f'{right_metric}_ci95'],
                 color='#222222', marker='o', linestyle='--', linewidth=1.4, capsize=3,
                 label=right_label)
    ax2.set_ylabel(right_label)
    ymin = max(0, df[f'{right_metric}_mean'].min() - 8)
    ymax = min(105, df[f'{right_metric}_mean'].max() + 8)
    if ymax - ymin < 8:
        ymin = max(0, ymin - 3); ymax = min(105, ymax + 3)
    ax2.set_ylim(ymin, ymax)
    handles = [Line2D([0], [0], color='0.45', lw=7, label='Mean delay (95% CI)'),
               Line2D([0], [0], color='#222222', marker='o', ls='--', label=f'{right_label} (95% CI)')]
    ax.legend(handles=handles, frameon=False, loc='upper right')
fig.suptitle('Opportunity charging dominates in the base case; priority trade-offs emerge under challenge conditions', y=1.03, fontsize=12, fontweight='bold')
save(fig, 'Figure1_Base_vs_Challenge')

# ---------- Figure 2 ----------
chal_trade = summarize(challenge, ['mean_delay', 'urgent_on_time_rate', 'completion_rate', 'wpt_loss'])
fig, ax = plt.subplots(figsize=(6.3, 4.8))
loss = chal_trade['wpt_loss_mean']
sizes = 80 + 520 * (loss - loss.min()) / (loss.max() - loss.min() + 1e-12)
sc = ax.scatter(chal_trade['mean_delay_mean'], chal_trade['urgent_on_time_rate_mean'],
                s=sizes, c=loss, cmap='Greys', edgecolor='black', linewidth=0.8, zorder=3)
for _, r in chal_trade.iterrows():
    st = r['strategy']
    ax.scatter(r['mean_delay_mean'], r['urgent_on_time_rate_mean'], s=sizes.loc[_],
               marker=MARKERS[st], color=COLORS[st], edgecolor='black', linewidth=0.7, zorder=4)
    dx = 0.45 if st != 'C1' else -1.7
    dy = 0.7 if st != 'C2' else -2.2
    ax.annotate(st, (r['mean_delay_mean'], r['urgent_on_time_rate_mean']), xytext=(dx, dy),
                textcoords='offset fontsize', fontweight='bold')
ax.set_xlabel('Mean task delay [min]')
ax.set_ylabel('Urgent-task on-time completion [%]')
ax.set_title('Challenge Case trade-off among delay, urgent service, and WPT loss', loc='left', fontweight='bold')
cb = fig.colorbar(sc, ax=ax, pad=0.02)
cb.set_label('WPT energy loss [kWh]')
legend_elements = [Line2D([0], [0], marker=MARKERS[s], color='w', label=s, markerfacecolor=COLORS[s], markeredgecolor='black', markersize=8) for s in STRATEGIES]
ax.legend(handles=legend_elements, title='Strategy', frameon=False, loc='lower right')
ax.grid(True, alpha=0.25)
save(fig, 'Figure2_Challenge_Tradeoff')

# ---------- Figure 3 ----------
chal_c4 = challenge[challenge.strategy == 'C4']
contention_mean, contention_ci = chal_c4['charging_contention_events'].mean(), ci95(chal_c4['charging_contention_events'])
diff_mean, diff_ci = chal_c4['different_decision_rate_C4_vs_C3'].mean(), ci95(chal_c4['different_decision_rate_C4_vs_C3'])
feat_ch = features[(features.scenario == 'challenge_primary') & (features.strategy == 'C4')]
feat_names = ['1-SOC', 'E_next', 'T_idle', 'eta_WPT', 'D']
feat_cols = ['one_minus_soc_std', 'E_next_std', 'T_idle_std', 'eta_WPT_std', 'D_std']
feat_std = [float(feat_ch[c].iloc[0]) for c in feat_cols]
fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.2))
ax = axes[0]
ax.bar([0], [contention_mean], yerr=[contention_ci], capsize=4, color='#4c78a8', edgecolor='black', width=0.55)
ax.set_xticks([0], ['Contention events\nper replication'])
ax.set_ylabel('Events / replication')
ax.set_title('(a) C4 had many chances to differ from C3', loc='left', fontweight='bold')
ax2 = ax.twinx()
ax2.bar([1], [diff_mean], yerr=[diff_ci], capsize=4, color='#e15759', edgecolor='black', width=0.55)
ax2.set_ylabel('Different decision rate [%]')
ax.set_xlim(-0.7, 1.7)
ax.set_xticks([0, 1], ['Charging\ncontention', 'C4 ≠ C3\ndecision rate'])
ax.text(0, contention_mean + contention_ci + 25, f'{contention_mean:.0f}', ha='center', va='bottom', fontweight='bold')
ax2.text(1, diff_mean + diff_ci + 2, f'{diff_mean:.1f}%', ha='center', va='bottom', fontweight='bold')
axes[1].bar(np.arange(len(feat_names)), feat_std, color=['#999999', '#4c78a8', '#76b7b2', '#f28e2b', '#e15759'], edgecolor='black', linewidth=0.6)
axes[1].set_xticks(np.arange(len(feat_names)), feat_names, rotation=20, ha='right')
axes[1].set_ylabel('Standard deviation of normalized feature')
axes[1].set_title('(b) Priority features were informative in the challenge case', loc='left', fontweight='bold')
for i, v in enumerate(feat_std):
    axes[1].text(i, v + 0.01, f'{v:.3f}', ha='center', va='bottom', fontsize=8)
fig.suptitle('Decision diagnostics: C4 differs from C3 because contention and feature variance are present', y=1.03, fontsize=12, fontweight='bold')
save(fig, 'Figure3_C4_vs_C3_Diagnostics')

# ---------- Figure 4 ----------
sg = stress.copy()
parts = sg['scenario'].str.extract(r'stress_w(?P<workload>\d+)_p(?P<pads>\d+)_kw(?P<power>\d+)').astype(int)
sg = pd.concat([sg, parts], axis=1)
mean_sg = sg.groupby(['workload', 'pads', 'power', 'strategy']).agg(
    mean_delay=('mean_delay', 'mean'), urgent=('urgent_on_time_rate', 'mean')
).reset_index()
rows = []
for (wl, pads, pwr), g in mean_sg.groupby(['workload', 'pads', 'power']):
    c3 = g[g.strategy == 'C3'].iloc[0]
    c4 = g[g.strategy == 'C4'].iloc[0]
    improvement = (c3.mean_delay - c4.mean_delay) / max(c3.mean_delay, 1e-9) * 100
    urgent_diff = c4.urgent - c3.urgent
    rows.append({'workload': wl, 'pads': pads, 'power': pwr, 'delay_improvement_pct': improvement, 'urgent_diff_pp': urgent_diff})
adv = pd.DataFrame(rows)
fig, axes = plt.subplots(1, 3, figsize=(12.0, 3.8), sharey=True)
v = np.nanmax(np.abs(adv['delay_improvement_pct']))
norm = TwoSlopeNorm(vmin=-v, vcenter=0, vmax=v)
for ax, pwr in zip(axes, [1, 3, 5]):
    sub = adv[adv.power == pwr]
    mat = sub.pivot(index='pads', columns='workload', values='delay_improvement_pct').sort_index(ascending=True)
    ann = sub.pivot(index='pads', columns='workload', values='urgent_diff_pp').sort_index(ascending=True)
    im = ax.imshow(mat.values, cmap='RdBu_r', norm=norm, aspect='auto')
    ax.set_title(f'WPT power = {pwr} kW', fontweight='bold')
    ax.set_xticks(np.arange(len(mat.columns)), mat.columns)
    ax.set_yticks(np.arange(len(mat.index)), mat.index)
    ax.set_xlabel('Workload [tasks/h]')
    if ax is axes[0]: ax.set_ylabel('Number of WPT pads')
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            val = mat.iloc[i, j]; ud = ann.iloc[i, j]
            color = 'white' if abs(val) > 30 else 'black'
            ax.text(j, i, f'{val:+.0f}%\n({ud:+.1f} pp)', ha='center', va='center', fontsize=8, color=color)
cb = fig.colorbar(im, ax=axes, fraction=0.025, pad=0.02)
cb.set_label('C4 delay improvement over C3 [%]\npositive = lower mean delay with C4')
fig.suptitle('C4 advantage is conditional on resource scarcity and heterogeneous tasks', y=1.02, fontsize=12, fontweight='bold')
save(fig, 'Figure4_C4_Advantage_Region')

# Save concise plotting data summaries for traceability
base_sum.to_csv(OUT / 'plot_data_Figure1_base_summary.csv', index=False)
chal_sum.to_csv(OUT / 'plot_data_Figure1_challenge_summary.csv', index=False)
chal_trade.to_csv(OUT / 'plot_data_Figure2_tradeoff_summary.csv', index=False)
pd.DataFrame({'metric': ['contention_events', 'different_decision_rate'], 'mean': [contention_mean, diff_mean], 'ci95': [contention_ci, diff_ci]}).to_csv(OUT / 'plot_data_Figure3_decision_summary.csv', index=False)
pd.DataFrame({'feature': feat_names, 'std': feat_std}).to_csv(OUT / 'plot_data_Figure3_feature_std.csv', index=False)
adv.to_csv(OUT / 'plot_data_Figure4_advantage_heatmap.csv', index=False)
print('Created 4 publication figures in', OUT)
print('Inputs used: base_case_runs.csv, challenge_runs.csv, stress_grid.csv, priority_features.csv, priority_features_raw_sample.csv, decision_diagnostics.csv')
