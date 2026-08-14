from pathlib import Path
import sys
sys.path.insert(0, '/home/hy/wpt_agv_opportunity_charging')
from copy import deepcopy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from v2_runner import load_cfg, generate_common, V2Sim

ROOT = Path('/home/hy/wpt_agv_opportunity_charging')
OUT = ROOT / 'results_v4_contribution_figures'
OUT.mkdir(exist_ok=True)

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

COLORS = {'C1':'#6c757d', 'C2':'#4c78a8', 'C3':'#59a14f', 'C4':'#e15759'}
LABELS = {'C1':'C1 Threshold full charging', 'C2':'C2 Always opportunity', 'C3':'C3 Low-SOC priority', 'C4':'C4 Proposed priority'}

def save(fig, name):
    fig.savefig(OUT / f'{name}.png', bbox_inches='tight')
    fig.savefig(OUT / f'{name}.pdf', bbox_inches='tight')
    plt.close(fig)

def ci95(x):
    x = pd.Series(x).dropna()
    return 1.96 * x.std(ddof=1) / np.sqrt(len(x)) if len(x) > 1 else 0.0

def make_soc_trace():
    # Generate a common-random-number representative Challenge run and save full traces for C1/C2/C4.
    cfg = load_cfg(); cfg.update({'n_agvs':5, 'n_pads':1, 'task_arrival_rate_per_h':90, 'wpt_power_kw':3})
    dist = {1:20, 2:25, 3:30, 4:35, 5:40}
    tasks, init = generate_common(cfg, cfg['seed0'], distances=dist, urgent_ratio=0.2)
    rows = []
    metrics = []
    for st in ['C1','C2','C4']:
        sim = V2Sim(cfg, st, cfg['seed0'], tasks, init, 'contrib_soc_trace', variable_eta=True)
        m = sim.run(); metrics.append(m)
        # pick AGV 1 consistently to avoid cherry-picking
        a = sim.agvs[0]
        for t, soc in a.trace:
            if t <= 24*3600:
                rows.append({'strategy':st, 'agv_id':1, 'time_h':t/3600, 'soc':soc*100})
    trace = pd.DataFrame(rows)
    trace.to_csv(OUT/'plot_data_Figure1_soc_trace.csv', index=False)
    pd.DataFrame(metrics).to_csv(OUT/'plot_data_Figure1_representative_run_metrics.csv', index=False)
    fig, axes = plt.subplots(1, 3, figsize=(12.2, 3.6), sharey=True)
    for ax, st in zip(axes, ['C1','C2','C4']):
        g = trace[trace.strategy == st]
        ax.step(g.time_h, g.soc, where='post', color=COLORS[st], linewidth=1.2)
        ax.axhline(20, color='#d62728', ls='--', lw=0.9, alpha=0.8, label='Critical SOC 20%')
        ax.axhline(90, color='#444444', ls=':', lw=0.9, alpha=0.8, label='Max SOC 90%')
        ax.set_title(LABELS[st], fontweight='bold')
        ax.set_xlabel('Time [h]')
        ax.set_xlim(0, 24); ax.set_ylim(0, 95)
        if ax is axes[0]: ax.set_ylabel('AGV 1 SOC [%]')
        ax.set_axisbelow(True)
    axes[0].legend(frameon=False, loc='lower left')
    fig.suptitle('Figure 1. Representative AGV battery trajectory over 24 h under different scheduling policies', y=1.03, fontsize=12, fontweight='bold')
    save(fig, 'Figure1_SOC_Time_Series')


def make_delay_boxplot():
    df = pd.read_csv(ROOT/'results_v2/challenge_runs.csv')
    df = df[df.strategy.isin(['C1','C2','C3','C4'])]
    order = ['C1','C2','C3','C4']
    data = [df[df.strategy==s]['mean_delay'].values for s in order]
    fig, ax = plt.subplots(figsize=(6.3, 4.2))
    bp = ax.boxplot(data, patch_artist=True, widths=0.6, showmeans=True,
                    meanprops={'marker':'D','markerfacecolor':'white','markeredgecolor':'black','markersize':5},
                    medianprops={'color':'black','linewidth':1.2},
                    whiskerprops={'linewidth':1.0}, capprops={'linewidth':1.0})
    for patch, st in zip(bp['boxes'], order):
        patch.set_facecolor(COLORS[st]); patch.set_alpha(0.78); patch.set_edgecolor('black')
    ax.set_xticklabels(['C1\nThreshold','C2\nAlways','C3\nLow-SOC','C4\nProposed'])
    ax.set_ylabel('Mean task delay [min]')
    ax.set_title('Figure 2. Monte Carlo distribution of logistics delay in the Challenge Case', loc='left', fontweight='bold')
    # annotate throughput means on top as secondary practical indicator
    means = df.groupby('strategy')['throughput'].mean()
    ymax = ax.get_ylim()[1]
    for i, st in enumerate(order, start=1):
        ax.text(i, ymax*0.93, f'{means[st]:.1f}\ntasks/h', ha='center', va='top', fontsize=8)
    ax.text(0.02, 0.98, 'Text: mean throughput', transform=ax.transAxes, ha='left', va='top', fontsize=8, color='0.25')
    df.to_csv(OUT/'plot_data_Figure2_challenge_delay_boxplot.csv', index=False)
    save(fig, 'Figure2_Delay_Boxplot')


def make_min_pad_heatmap():
    # Use dedicated design grid from results/ to produce AGV × workload minimum pad count under 99% criterion.
    dg = pd.read_csv(ROOT/'results/design_grid_summary.csv')
    pad = dg[(dg.design_mode=='pad')].copy()
    rows = []
    for (agv, wl), g in pad.groupby(['agv_number','workload']):
        feasible = g[g.feasible_99 == True].sort_values('candidate_value')
        if len(feasible):
            val = int(feasible.iloc[0]['candidate_value'])
        else:
            val = np.nan
        rows.append({'agv_number':agv, 'workload':wl, 'min_pads':val})
    mp = pd.DataFrame(rows)
    mat = mp.pivot(index='agv_number', columns='workload', values='min_pads').sort_index()
    mp.to_csv(OUT/'plot_data_Figure3_min_pad_heatmap.csv', index=False)
    # Discrete map: 1,2,3,5 and infeasible.
    vals = mat.values.astype(float)
    display = np.where(np.isnan(vals), 6, vals)
    cmap = ListedColormap(['#e8f3f8', '#b7d8e8', '#73a9c2', '#2f6f8f', '#d8d8d8'])
    bounds = [0.5,1.5,2.5,4.0,5.5,6.5]
    norm = BoundaryNorm(bounds, cmap.N)
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    im = ax.imshow(display, cmap=cmap, norm=norm, aspect='auto')
    ax.set_xticks(np.arange(len(mat.columns)), [str(int(c)) for c in mat.columns])
    ax.set_yticks(np.arange(len(mat.index)), [str(int(i)) for i in mat.index])
    ax.set_xlabel('Workload [tasks/h]')
    ax.set_ylabel('Number of AGVs')
    ax.set_title('Figure 3. Minimum WPT pad requirement for 99% completion and zero stoppage', loc='left', fontweight='bold')
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            v = mat.iloc[i,j]
            txt = 'N/A' if pd.isna(v) else f'{int(v)}'
            ax.text(j, i, txt, ha='center', va='center', fontweight='bold', color='black')
    cbar = fig.colorbar(im, ax=ax, fraction=0.045, pad=0.03, ticks=[1,2,3,5,6])
    cbar.ax.set_yticklabels(['1 pad','2 pads','3 pads','5 pads','not feasible'])
    cbar.set_label('Minimum WPT pads')
    save(fig, 'Figure3_Minimum_Infrastructure_Heatmap')


def make_eta_ablation():
    # Use V2 ablation in challenge setting. Filter only eta ablation and C4 for direct C4-Fixed vs C4-Variable comparison.
    abl = pd.read_csv(ROOT/'results_v2/ablation.csv')
    sub = abl[(abl.ablation_group=='eta') & (abl.strategy=='C4')].copy()
    label_map = {'fixed_eta':'C4-Fixed\nη = 90%', 'variable_eta':'C4-Variable\npredicted η'}
    sub['case_label'] = sub['ablation_case'].map(label_map)
    order = ['C4-Fixed\nη = 90%', 'C4-Variable\npredicted η']
    data = [sub[sub.case_label==o]['wpt_loss'].values for o in order]
    fig, ax = plt.subplots(figsize=(5.8, 4.2))
    parts = ax.violinplot(data, showmeans=False, showmedians=False, showextrema=False)
    for body, color in zip(parts['bodies'], ['#9ecae1', '#f4a261']):
        body.set_facecolor(color); body.set_edgecolor('black'); body.set_alpha(0.8)
    # overlay boxplot for median/IQR
    bp = ax.boxplot(data, widths=0.22, patch_artist=True, showfliers=False,
                    medianprops={'color':'black','linewidth':1.3},
                    boxprops={'facecolor':'white','edgecolor':'black','alpha':0.85},
                    whiskerprops={'color':'black'}, capprops={'color':'black'})
    means = [np.mean(d) for d in data]
    cis = [ci95(d) for d in data]
    ax.errorbar([1,2], means, yerr=cis, fmt='D', color='#222222', markerfacecolor='white', capsize=4, label='Mean ± 95% CI')
    ax.set_xticks([1,2], order)
    ax.set_ylabel('WPT energy loss [kWh]')
    ax.set_title('Figure 4. Value of WPT efficiency-aware scheduling in C4 ablation', loc='left', fontweight='bold')
    ax.legend(frameon=False, loc='upper right')
    sub.to_csv(OUT/'plot_data_Figure4_eta_ablation.csv', index=False)
    save(fig, 'Figure4_WPT_Efficiency_Ablation')


def write_docs():
    captions = '''# Captions for Contribution Figures\n\n## Figure 1. Strategy별 AGV 배터리(SOC) 24시간 변화 궤적\nRepresentative Challenge Case replication(seed 1007)에서 AGV 1의 SOC time-series를 C1, C2, C4에 대해 비교하였다. C1은 critical SOC 근처까지 방전된 후 mandatory full charging으로 회복하는 큰 saw-tooth 패턴을 보이며, 이는 threshold charging의 긴 이탈 가능성을 시사한다. C2는 opportunity charging을 빈번히 수행하여 높은 SOC를 유지하지만, 그만큼 pad 접근/복귀 detour와 charging session이 많아질 수 있다. C4는 critical SOC 이하로 떨어지는 것을 방지하면서 priority score에 따라 charging opportunity를 선택적으로 활용하는 동작을 보여준다.\n\n## Figure 2. 전략별 물류 지연 분포(Boxplot)\nPrimary Challenge Case의 50회 Monte Carlo replication에서 strategy별 mean task delay 분포를 boxplot으로 나타냈다. Box는 IQR, 중앙선은 median, 흰 diamond는 mean을 나타내며, 상단 주석은 평균 throughput을 함께 표시한다. 이 그림은 단일 평균값뿐 아니라 전략별 delay variability와 worst-case tail을 함께 보여준다. Challenge 조건에서 C2, C3, C4는 서로 다른 delay 안정성을 보이며, C4는 C3 대비 delay를 줄이는 절충형 전략으로 해석된다.\n\n## Figure 3. 운영 조건별 최소 WPT 패드 수 Heatmap\nDedicated design grid 결과를 사용하여 AGV 수와 workload 조합별로 99% completion 및 low-SOC stoppage-free criterion을 만족하는 최소 WPT pad 수를 표시하였다. 셀의 숫자는 가장 작은 feasible pad count를 의미하며, N/A는 후보 pad 범위 내에서 기준을 만족하지 못한 조건이다. 이 figure는 알고리즘 성능 분석을 실제 물류센터 WPT 인프라 sizing guideline으로 연결한다.\n\n## Figure 4. C4-Fixed vs C4-Variable WPT 에너지 손실 비교\nChallenge ablation에서 C4 fixed-efficiency(η=90%)와 predicted variable-efficiency C4의 WPT energy loss 분포를 violin plot으로 비교하였다. Violin은 replication별 분포, 내부 box는 IQR/median, diamond는 mean ± 95% CI를 나타낸다. 이 figure는 위치/정렬 상태에 따른 WPT 효율 변동을 scheduling score에 반영했을 때 송신 에너지 중 손실되는 비율이 어떻게 달라지는지 보여주며, Contribution 3의 에너지 측면 근거로 사용된다.\n'''
    (OUT/'CAPTIONS.md').write_text(captions, encoding='utf-8')
    readme = '''# Contribution Figures\n\nThis folder contains four requested contribution-oriented figures generated with matplotlib only.\n\n## Generated files\n\n1. `Figure1_SOC_Time_Series.png/pdf` — Contribution 2, SOC trajectory comparison.\n2. `Figure2_Delay_Boxplot.png/pdf` — Contribution 2, logistics delay distribution.\n3. `Figure3_Minimum_Infrastructure_Heatmap.png/pdf` — Contribution 1, minimum WPT pad guideline.\n4. `Figure4_WPT_Efficiency_Ablation.png/pdf` — Contribution 3, fixed vs variable WPT efficiency ablation.\n\n## Data sources\n\n- Figure 1: regenerated representative Challenge Case trace using `v2_runner.py` with common random numbers, seed 1007, AGV 1.\n- Figure 2: `results_v2/challenge_runs.csv`.\n- Figure 3: `results/design_grid_summary.csv`.\n- Figure 4: `results_v2/ablation.csv`.\n\nAll plots are saved as PNG at 350 dpi and PDF. Plot-ready CSV extracts are also saved as `plot_data_*.csv`.\n'''
    (OUT/'README.md').write_text(readme, encoding='utf-8')

if __name__ == '__main__':
    make_soc_trace()
    make_delay_boxplot()
    make_min_pad_heatmap()
    make_eta_ablation()
    write_docs()
    print(f'Generated contribution figures in {OUT}')
