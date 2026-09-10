# AGV-WPT DES Final Evaluation

This repository contains the final discrete-event simulation for opportunity charging of logistics-center AGVs using a geometry-derived wireless-power-transfer model.

## Final strategies

- C1: conventional threshold charging baseline
- C2: idle-time priority
- C3: low-SOC priority
- C4: frozen multi-feature priority heuristic
- C5: frozen 15-minute rolling-horizon MILP benchmark

Final frozen parameters are recorded in `results_final/final_frozen_parameters.json`:

- C4: `w1=0.55`, `w2=0.175`, `w3=0.105`, `w4=0.07`, `w5=0.10`
- C5: `lambda_soc=2.0`, `lambda_task=1.5`, `lambda_kpi=1.5`

## Run the final evaluation

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python simpy numpy pandas scipy matplotlib pyyaml pytest tabulate
AGV_WPT_MPL_CONFIG=/tmp/agv_wpt_mpl MPLCONFIGDIR=/tmp/agv_wpt_mpl .venv/bin/python final_evaluation.py
AGV_WPT_MPL_CONFIG=/tmp/agv_wpt_mpl MPLCONFIGDIR=/tmp/agv_wpt_mpl .venv/bin/python generate_final_figures.py
.venv/bin/python -m pytest -q
```

`results_final/` contains replication-level Base Case, Primary Challenge, and Stress Grid results, paired statistics, C5 solver statistics, final figures in PNG/PDF, and `FINAL_REPORT.md`.

## Archive

Historical runners, sensitivity studies, refinement experiments, and intermediate outputs are preserved on the `archive/pre-final-evaluation` branch.
