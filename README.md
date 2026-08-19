# AGV WPT System — Latest Mainline (V3)

이 저장소의 `main` 브랜치는 항상 **최신 연구 버전만** 유지합니다. 과거 실험 결과와 중간 산출물은 별도 archive branch로 보존합니다.

## 현재 main 버전

**V3 — revised C1 baseline + corrected C4 + C5 15-min rolling-horizon MILP charging benchmark**

핵심 내용:

- C1 revised baseline: 기존 20%→90% full-charge 대신 SOC≤30%에서 시작해 70%에서 종료하는 conventional threshold charging을 공식 baseline으로 사용합니다.
- C4 수정: contention 시 모든 AGV가 동일한 `next_task`를 보던 문제를 수정하고, WMS preview 가정하에 AGV별 next assigned task 기반 `E_next_i`, `D_i`를 계산합니다.
- C5 추가: `scipy.optimize.milp` / HiGHS 기반 **15-min rolling-horizon MILP charging benchmark**를 사용합니다. 15개 60초 charging slot을 동시에 최적화하고 첫 slot만 실행하는 MPC/receding-horizon 방식입니다. 최신 C5 objective는 SOC reserve risk, forecast task-impact slack, forecast conflict penalty, 독립 KPI-risk charging term을 포함하며, C4 priority score는 사용하지 않습니다. C5에도 C2~C4와 동일한 mandatory SOC safety check를 적용합니다.
- C1~C5 동일 seed/common random numbers로 비교합니다.
- 결과는 `results_v3/`에 저장되어 있습니다.

## 실행 환경

```bash
cd /home/hy/wpt_agv_opportunity_charging
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python simpy numpy pandas scipy matplotlib pyyaml pytest tabulate
```

## V3 실행

```bash
# 빠른 debug / smoke test
.venv/bin/python v3_runner.py --debug

# V3 50 replication 실행
.venv/bin/python v3_runner.py

# 테스트
.venv/bin/python -m pytest -q
```

## 주요 V3 산출물

- `results_v3/REPORT_V3.md`
- `results_v3/c1_c5_results.csv`
- `results_v3/base_case_runs.csv`
- `results_v3/stress_grid.csv`
- `results_v3/c4_c5_comparison.csv`
- `results_v3/milp_schedule.csv`
- `results_v3/solver_statistics.csv`
- `results_v3/horizon_sensitivity.csv`
- `results_v3/priority_feature_statistics.csv`
- `results_v3_figures/Figure*_V3_*.png`, `*.pdf`
- `README_V3.md`

## Branch policy

- `main`: 최신 버전만 유지합니다.
- `archive/v1-v2-results`: V1/V2 결과와 기존 `results/`, `results_v2/` 보존용 branch입니다.
- `archive/all-experiments-pre-cleanup`: main 정리 전 전체 실험/figure 산출물 보존용 branch입니다.

자세한 규칙은 `docs/BRANCH_POLICY.md`를 참고하세요.
