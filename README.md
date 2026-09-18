# AGV-WPT DES: rho-Redesign Tuning Stage

This repository is currently at the reproducible **charging-adequacy redesign and C4 robust-tuning stage** for opportunity charging of logistics-center AGVs. The physical model is frozen; the unseen final evaluation and final paper figures have **not** been run yet.

## Active strategies

- C1: conventional threshold charging baseline
- C2: idle-time priority
- C3: low-SOC priority
- C4: frozen four-feature fleet/logistics priority heuristic
- C5: frozen 15-minute rolling-horizon MILP benchmark

The active C4 score is:

```text
S_i = 0.75 f_SOC - 0.25 f_D
```

`next_task_energy` and `idle` remain defined normalized features in the four-feature formulation but received zero weight under the multi-region robust selection. This is an outcome of tuning, not a special rule.

The frozen tuning artifact is `results/tuning/frozen_c4_parameters.json`. It used tuning-only CRN seeds `5007–5056`; no unseen final seed block has been used in this stage.

## Active reproducibility entry points

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python simpy numpy pandas scipy matplotlib pyyaml pytest tabulate
AGV_WPT_MPL_CONFIG=/tmp/agv_wpt_mpl MPLCONFIGDIR=/tmp/agv_wpt_mpl .venv/bin/python run_wpt_model_validation.py
AGV_WPT_MPL_CONFIG=/tmp/agv_wpt_mpl MPLCONFIGDIR=/tmp/agv_wpt_mpl .venv/bin/python run_rho_tuning.py
.venv/bin/python -m pytest -q
```

`run_rho_tuning.py` writes only `results/tuning/`. It creates the rho catalog, C1/C2/C3 CRN references, 4-feature C4 coarse/local searches, paired C4-C3 statistics, scenario-design report, and frozen C4 parameters. It does **not** run an unseen final evaluation or paper figures.

## WPT model validation

The SS-compensated geometry model is configured only in `config/wpt_model.yaml`. It uses a nominal 48-V DC-side design assumption and a full-wave/full-bridge FHA load convention:

```text
R_L,FHA(P_out) = (8/pi^2) * V_dc^2 / P_out
```

This is a nominal paper-model assumption, not an empirical AGV battery specification. The model recomputes `eta(misalignment, P_out)` for each configured 1/3/5-kW output power; it does not implement a deliverable-power limit because converter/current constraints are not parameterized.

```bash
AGV_WPT_MPL_CONFIG=/tmp/agv_wpt_mpl MPLCONFIGDIR=/tmp/agv_wpt_mpl .venv/bin/python run_wpt_model_validation.py
```

Outputs are written to `results/model_validation/`, including Neumann convergence, power-dependent FHA curves, a WPT validation figure, and C4 eta-feature influence diagnostics. This validation entry point does not run rho redesign, C4 retuning, or a new final evaluation.

## Archive

The immutable pre-rho state is preserved at `archive/pre-rho-redesign-20260917` (commit `b8ac79046609bbd08b078624d2a68976244d1b6b`). Historical final-evaluation materials remain legacy until the separately frozen unseen evaluation is executed after this tuning stage.
