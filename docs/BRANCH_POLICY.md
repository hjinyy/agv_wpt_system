# Branch Policy

이 저장소는 앞으로 다음 원칙으로 관리합니다.

## 원칙

1. `main`에는 항상 최신 구현과 최신 핵심 결과만 둡니다.
2. 과거 실험, 중간 figure, 오래된 결과 디렉터리는 `main`에 계속 누적하지 않습니다.
3. 과거 실험을 보존해야 할 때는 삭제 전에 archive branch를 먼저 만들고 push합니다.
4. 결과가 큰 CSV는 가능하면 archive branch 또는 release artifact로 분리하고, `main`에는 최신 분석에 필요한 최소 결과만 남깁니다.

## 현재 branch 구조

| Branch | 용도 |
|---|---|
| `main` | 최신 V3: C4 next-task fix + C5 MILP benchmark |
| `archive/v1-v2-results` | V1/V2 코드와 `results/`, `results_v2/` 보존 |
| `archive/all-experiments-pre-cleanup` | main 정리 전 모든 실험/figure 산출물 보존 |

## 새 실험을 시작할 때 권장 절차

```bash
# 현재 main 상태 보존이 필요하면 archive branch 생성
git switch main
git pull --ff-only

git branch archive/<experiment-name>-pre-cleanup
git push origin archive/<experiment-name>-pre-cleanup

# 최신 실험 구현은 main 또는 별도 작업 branch에서 진행
# 완료 후 main에는 최신 결과만 남기고 오래된 results_*는 archive branch에만 보존
```

## 금지/주의

- `main`에 `results/`, `results_v2/`, 여러 세대의 figure 디렉터리를 계속 누적하지 않습니다.
- 100MB 이상 파일은 GitHub hard limit에 걸리므로 commit하지 않습니다.
- token, password, API key, credential 파일은 절대 commit하지 않습니다.
