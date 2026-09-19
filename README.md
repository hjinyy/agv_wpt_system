# AGV-WPT DES: 6-AGV Pre-final Freeze

This repository contains the approved **rho-based 6-AGV Primary** experiment package. The WPT physical model, C4 rule, and C5 objective scales are frozen for a separately authorized unseen evaluation. That unseen evaluation and all final paper figures remain **unexecuted**.

## Frozen Primary Challenge

```text
AGVs: 6
Distances: 40 / 50 / 60 / 70 / 80 m
Pads: 1
WPT nominal output power: 3 kW
Task arrival rate: 90 tasks/h
Urgent-task ratio: 0.20
rho analytical: approximately 1.01
logistics utilization: approximately 0.875
```

## Active strategy terminology

- C1: conventional threshold charging baseline
- C2: idle-time priority
- C3: low-SOC priority
- C4: **SOC-deadline risk priority** / robust charging-priority heuristic
- C5: **rolling-horizon MILP reference** / optimization-based reference

C4 candidate formulation is:

```text
S_i = w_SOC f_SOC + w_E f_E + w_idle f_idle - w_D f_D
```

with non-negative weights summing to one. WPT efficiency is deliberately excluded from the C4 score and retained only in the physical charging/SOC/loss model. The robustly selected active C4 rule is:

```text
S_i = 0.75 f_SOC - 0.25 f_D
```

The zero next-task-energy and idle weights are a tuning result, not a hard override.

## Frozen artifacts

- `results/tuning/frozen_c4_parameters.json`
- `results/pre_final/frozen_c5_parameters.json`
- `results/pre_final/frozen_experiment_manifest.json`
- `results/tuning/SCENARIO_DESIGN.md`
- `results/pre_final/C5_REVALIDATION_REPORT.md`

## Reproducibility entry points

```bash
AGV_WPT_MPL_CONFIG=/tmp/agv_wpt_mpl MPLCONFIGDIR=/tmp/agv_wpt_mpl .venv/bin/python run_wpt_model_validation.py
AGV_WPT_MPL_CONFIG=/tmp/agv_wpt_mpl MPLCONFIGDIR=/tmp/agv_wpt_mpl .venv/bin/python run_rho_tuning.py
AGV_WPT_MPL_CONFIG=/tmp/agv_wpt_mpl MPLCONFIGDIR=/tmp/agv_wpt_mpl .venv/bin/python run_c5_revalidation.py
.venv/bin/python run_freeze_manifest.py
.venv/bin/python run_pre_final_integrity.py
.venv/bin/python -m pytest -q
```

The tuning/revalidation commands use CRN seeds `5007–5056`. The planned unseen final block is `6007–6056`, with overlap zero. Do not run `final_evaluation.py` or `generate_final_figures.py` until separately approved.

## Archives

- Pre-rho redesign: `archive/pre-rho-redesign-20260917` at `b8ac79046609bbd08b078624d2a68976244d1b6b`
- Pre-6-AGV Primary state: `archive/pre-6agv-primary-freeze-20260919` at `71aa37dc69b1d8e388b28e452a53591ed8089623`
