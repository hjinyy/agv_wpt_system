# Captions for Contribution Figures

## Figure 1. Strategy별 AGV 배터리(SOC) 24시간 변화 궤적
Representative Challenge Case replication(seed 1007)에서 AGV 1의 SOC time-series를 C1, C2, C4에 대해 비교하였다. C1은 critical SOC 근처까지 방전된 후 mandatory full charging으로 회복하는 큰 saw-tooth 패턴을 보이며, 이는 threshold charging의 긴 이탈 가능성을 시사한다. C2는 opportunity charging을 빈번히 수행하여 높은 SOC를 유지하지만, 그만큼 pad 접근/복귀 detour와 charging session이 많아질 수 있다. C4는 critical SOC 이하로 떨어지는 것을 방지하면서 priority score에 따라 charging opportunity를 선택적으로 활용하는 동작을 보여준다.

## Figure 2. 전략별 물류 지연 분포(Boxplot)
Primary Challenge Case의 50회 Monte Carlo replication에서 strategy별 mean task delay 분포를 boxplot으로 나타냈다. Box는 IQR, 중앙선은 median, 흰 diamond는 mean을 나타내며, 상단 주석은 평균 throughput을 함께 표시한다. 이 그림은 단일 평균값뿐 아니라 전략별 delay variability와 worst-case tail을 함께 보여준다. Challenge 조건에서 C2, C3, C4는 서로 다른 delay 안정성을 보이며, C4는 C3 대비 delay를 줄이는 절충형 전략으로 해석된다.

## Figure 3. 운영 조건별 최소 WPT 패드 수 Heatmap
Dedicated design grid 결과를 사용하여 AGV 수와 workload 조합별로 99% completion 및 low-SOC stoppage-free criterion을 만족하는 최소 WPT pad 수를 표시하였다. 셀의 숫자는 가장 작은 feasible pad count를 의미하며, N/A는 후보 pad 범위 내에서 기준을 만족하지 못한 조건이다. 이 figure는 알고리즘 성능 분석을 실제 물류센터 WPT 인프라 sizing guideline으로 연결한다.

## Figure 4. C4-Fixed vs C4-Variable WPT 에너지 손실 비교
Challenge ablation에서 C4 fixed-efficiency(η=90%)와 predicted variable-efficiency C4의 WPT energy loss 분포를 violin plot으로 비교하였다. Violin은 replication별 분포, 내부 box는 IQR/median, diamond는 mean ± 95% CI를 나타낸다. 이 figure는 위치/정렬 상태에 따른 WPT 효율 변동을 scheduling score에 반영했을 때 송신 에너지 중 손실되는 비율이 어떻게 달라지는지 보여주며, Contribution 3의 에너지 측면 근거로 사용된다.
