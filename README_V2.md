# WPT AGV Opportunity Charging Simulation V2

V2는 기존 `results/`를 덮어쓰지 않고 `results_v2/`에 별도 저장합니다.

## 목적

- Layer 1: Original Base Case 재현 — C1 대비 opportunity charging 효과 확인
- Layer 2: Scheduling Challenge Case — 거리/Deadline/WPT 효율 이질성과 pad scarcity에서 C2/C3/C4 차이 평가

## 실행

```bash
cd /home/hy/wpt_agv_opportunity_charging
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python simpy numpy pandas scipy matplotlib pyyaml pytest tabulate

# 단일 seed debug: contention, C3/C4 different decision, feature std 확인
.venv/bin/python v2_runner.py --debug

# 전체 V2 실험: 50 replications, base/challenge/stress/ablation
.venv/bin/python v2_runner.py
```

## 결과 파일

- `results_v2/base_case_runs.csv`
- `results_v2/challenge_runs.csv`
- `results_v2/challenge_summary.csv`
- `results_v2/stress_grid.csv`
- `results_v2/ablation.csv`
- `results_v2/priority_features.csv`
- `results_v2/decision_diagnostics.csv`
- `results_v2/task_level_results.csv`
- `results_v2/agv_level_results.csv`
- `results_v2/pad_level_results.csv`
- `results_v2/paired_comparisons_v2.csv`
- `results_v2/REPORT_V2.md`
- `results_v2/figures/*.png`, `*.pdf`

## 모델 변경 사항

- Challenge Case picking distance: P1~P5 = 20/25/30/35/40 m
- Normal/Urgent task = 80/20%, deadline = arrival+8/4 min
- C2~C4 opportunity charging quantum = 60 s
- C2/C3/C4 동일 candidate generation, pad 배정 rule만 다름
- C2/C3/C4 공통 critical SOC safety rule
- C4 feature diagnostics 및 C4-vs-C3 different decision rate 저장

## 주의

50 W prototype 효율은 산업용 절대효율로 주장하지 않고, relative-efficiency synthetic scenario model로만 사용합니다. predicted eta와 realized eta는 초기 V2에서는 동일하게 둡니다.
