# WPT AGV Opportunity Charging Simulation

Python 기반 WPT(Wireless Power Transfer) 다중 AGV opportunity charging scheduling 연구용 시뮬레이션입니다.

## 실행 환경

```bash
cd /home/hy/wpt_agv_opportunity_charging
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python simpy numpy pandas scipy matplotlib pyyaml pytest tabulate
```

## 빠른 검증

```bash
.venv/bin/python -m pytest -q
.venv/bin/python main.py --fast
```

## 전체 실험

```bash
.venv/bin/python main.py
```

전체 실험은 Base/Scenario A~D/Ablation을 50 replications로 실행하고 `results/`에 CSV, 그림, 보고서를 저장합니다.

## 주요 결과 파일

- `results/raw_runs.csv`
- `results/summary_by_scenario.csv`
- `results/summary_by_strategy.csv`
- `results/agv_level_results.csv`
- `results/pad_level_results.csv`
- `results/priority_feature_statistics.csv`
- `results/ablation_efficiency.csv`
- `results/design_guideline.csv`
- `results/design_grid_summary.csv`, `results/final_design_table.csv`
- `results/REPORT.md`
- `results/figures/*.png`, `*.pdf`

## 연구상 주의

50 W prototype 효율은 산업용 WPT 절대효율 예측값이 아니라 relative efficiency scenario model로만 사용했습니다. C1~C4는 동일 seed의 task arrival/picking/SOC/efficiency sequence를 공유합니다.
