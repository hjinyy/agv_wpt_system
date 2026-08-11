from pathlib import Path
import pandas as pd
import numpy as np

def fmt(mean,sd,unit=''):
    return f'{mean:.2f} ± {sd:.2f}{unit}'

def write_report(results_dir):
    rd=Path(results_dir)
    raw=pd.read_csv(rd/'raw_runs.csv')
    summ=pd.read_csv(rd/'summary_by_scenario.csv')
    cal=pd.read_csv(rd/'energy_calibration.csv')
    feat=pd.read_csv(rd/'priority_feature_statistics.csv') if (rd/'priority_feature_statistics.csv').exists() else pd.DataFrame()
    base=raw[(raw.scenario=='base') & (raw.strategy.isin(['C1','C2','C3','C4']))]
    lines=[]
    lines.append('# WPT 기반 다중 AGV Opportunity Charging Scheduling 시뮬레이션 보고서\n')
    lines.append('## 1. Simulation Model\nPython 3.11, SimPy(의존성 및 DES 환경 객체), NumPy/pandas 기반 이산사건형 AGV 작업-충전 시뮬레이션입니다. 작업은 Poisson arrival, FCFS + first-available AGV로 배정했으며, 충전전략 외 난수는 common random numbers로 공유했습니다.\n')
    lines.append('## 2. Assumptions\n- WPT 효율변동은 50 W prototype 절대효율을 kW급 효율로 직접 외삽한 것이 아니라, complete matching 79.96% 대비 상대 민감도를 산업 기준효율 90%에 곱한 synthetic scenario model입니다.\n- Picking–Staging 거리는 Base Case에서 모두 동일하므로 E_next feature는 낮은 분산/비정보적일 수 있습니다.\n- 작업지연은 `actual completion time - earliest physically possible completion time`으로 정의했습니다.\n')
    lines.append('## 3. Base Case\n')
    for st,g in base.groupby('strategy'):
        lines.append(f'- {st}: throughput {fmt(g.throughput.mean(),g.throughput.std()," tasks/h")}, completion {fmt(g.completion_rate.mean(),g.completion_rate.std(),"%")}, delay {fmt(g.mean_delay.mean(),g.mean_delay.std()," min")}, stoppage {fmt(g.low_soc_stops.mean(),g.low_soc_stops.std())}.')
    lines.append('\n## 4. Energy-model calibration\n')
    best=cal.sort_values(['mean_stops','mean_fleet_min_soc']).tail(1)
    lines.append('No/near-zero WPT sanity 결과 일부:\n\n'+cal.head(10).to_markdown(index=False)+'\n')
    lines.append('메인 실험은 config.yaml의 e_dist=0.20 kWh/km, P_aux=0.05 kW를 고정 사용했습니다. 이 조합은 24 h 동안 충전 필요성이 발생하면서도 모든 조건을 물리적으로 완전히 붕괴시키지 않는 operating region으로 선택했습니다.\n')
    lines.append('## 5. C1~C4 definition\nC1 threshold full charging, C2 always opportunity, C3 low-SOC priority, C4 normalized priority score(1-SOC, E_next, T_idle, eta, delay penalty)를 구현했습니다. C4도 SOC 안전규칙에 따라 critical SOC 이하는 mandatory charging 후보로 처리했습니다.\n')
    for title,sc in [('6. Scenario A results','A_agv'),('7. Scenario B results','B_pad'),('8. Scenario C results','C_workload'),('9. Scenario D results','D_power')]:
        lines.append(f'## {title}\n')
        tab=raw[(raw.scenario==sc)&(raw.strategy.isin(['C1','C2','C3','C4']))].groupby(['scenario_value','strategy'])[['throughput','completion_rate','mean_delay','low_soc_stops','pad_utilization']].agg(['mean','std']).round(2)
        lines.append(tab.to_markdown()+'\n')
    lines.append('## 10. WPT efficiency ablation\n')
    abl=raw[raw.scenario=='ablation_efficiency'].groupby('strategy')[['throughput','mean_delay','wpt_input_energy','battery_delivered_energy','low_soc_stops','pad_utilization']].agg(['mean','std']).round(2)
    lines.append(abl.to_markdown()+'\n')
    lines.append('## 11. Design guideline\n')
    dg=pd.read_csv(rd/'design_guideline.csv')
    lines.append('Provisional criterion: mean completion rate >= 99% and stop-free replications >= 95%. Threshold sensitivity(95/97/99%)는 design_guideline.csv에 저장했습니다.\n')
    lines.append(dg[(dg.criterion_completion==0.99)&(dg.strategy=='C4')].head(20).to_markdown(index=False)+'\n')
    lines.append('## 12. Unexpected/negative findings\n')
    if not feat.empty:
        if 'one_minus_soc_mean' in feat.columns:
            fs=feat[[c for c in feat.columns if c.endswith('_mean') or c.endswith('_std')]].mean(numeric_only=True).round(4).to_frame('average_across_scenarios')
        else:
            fs=feat[['one_minus_soc','E_next','T_idle','eta_WPT','D','score']].agg(['mean','std']).T.round(4)
        lines.append('Priority feature variance:\n\n'+fs.to_markdown()+'\n')
        low=[]
        if 'E_next_std' in feat.columns:
            low=[c[:-4] for c in feat.columns if c.endswith('_std') and feat[c].mean() < 1e-3]
        else:
            low=fs[fs.get('std',1)<1e-3].index.tolist()
        if low: lines.append(f'비정보적 feature 후보: {low}. Base Case 고정 route 때문에 E_next 또는 D가 거의 일정할 수 있으므로 ablation 해석 시 주의가 필요합니다.\n')
    lines.append('## 13. Limitations\n실제 docking error 분포와 kW급 WPT 효율 실측분포가 없으므로 효율 state 확률은 synthetic assumption입니다. Pad 위치효과는 staging/picking 균형 배치 규칙으로 단순화했습니다.\n')
    lines.append('## 14. Conclusions\nOpportunity charging은 유휴시간이 충분하고 WPT가 과잉도 부족도 아닌 영역에서 threshold charging 대비 SOC 안정성과 지연 감소를 제공하는지 평가할 수 있었습니다. C4의 추가 이점은 raw/paired comparison에서 C2/C3 대비 실제 차이로 판단해야 하며, C4가 항상 최고라고 가정하지 않았습니다.\n')
    lines.append('## 15. Recommended next experiments\n- 실제 AGV 전력/주행거리 계측값으로 e_dist/P_aux 재보정\n- 실제 docking error 로그 기반 효율 state 분포 추정\n- heterogeneous picking distance와 pad 위치 모델 확장\n- C4 feature ablation 및 calibration seed 전용 weight sensitivity 확장\n')
    (rd/'REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
