# Pre-final Audit — approved 6-AGV Primary

## C4 terminology and active rule

The general candidate formulation remains:

```text
S_i = w_SOC f_SOC + w_E f_E + w_idle f_idle - w_D f_D
```

with non-negative weights summing to one. WPT efficiency is excluded from the score and remains in actual charging physics only.

The robustly selected final C4 rule is:

```text
S_i = 0.75 f_SOC - 0.25 f_D
```

Recommended terminology: **SOC-deadline risk priority** or **robust charging-priority heuristic**. The zero next-task-energy and idle weights are selection outcomes, not added hard rules.

## Approved Primary

```text
6 AGVs; 40/50/60/70/80 m; 1 pad; 3 kW; 90 tasks/h; urgent ratio 0.20
rho analytical ≈ 1.01; logistics utilization ≈ 0.875
```

The superseded 7-AGV Primary and its former C4 tuning are preserved only by `archive/pre-6agv-primary-freeze-20260919`.

## C5

C5 structure is unchanged: 15-minute rolling horizon, 60-second slots, and first-slot receding-horizon execution. It is termed a **rolling-horizon MILP reference** / **optimization-based reference**, not an independent or clairvoyant global benchmark.

The new rho-catalog OAT revalidation uses seeds 5007–5056 and freezes:

```text
lambda_soc = 2.0
lambda_task = 1.5
lambda_kpi = 2.0
```

See `C5_REVALIDATION_REPORT.md` and `frozen_experiment_manifest.json` for provenance and full results.

## Scope stop

Final seeds 6007–6056 remain unused. No unseen final evaluation, final figures, or main cleanup has been performed.
