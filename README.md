# AGV-WPT DES: 6-AGV Final Unseen Package

This repository contains the approved rho-based 6-AGV Primary experiment package and its single completed unseen evaluation (`6007–6056`). Do **not** rerun the unseen block.

## Frozen Primary Challenge

```text
AGVs: 6
Distances: 40 / 50 / 60 / 70 / 80 m
Pads: 1
WPT nominal pad: 3 kW
Task arrival rate: 90 tasks/h
Urgent-task ratio: 0.20
rho analytical: approximately 1.01
logistics utilization: approximately 0.875
```

## Final WPT model

The final DES uses a nominal **3-kW**, 48-V SS-FHA matched operating condition:

```text
P_charge(t) = 3 kW × eta(delta_t)
R_L,FHA = (8/pi²) × 48² / 3000 = 0.622517 ohm
```

The modeled chain is power supply → inverter → Tx coil → Rx coil → rectifier → DC-link capacitor → CCCV buck converter → battery. CCCV duty regulation is represented by a **near-matched resonant-link assumption** over the DES charging range. This does not claim constant efficiency at all output powers or model detailed converter switching/control dynamics.

The generic 1/3/5-kW FHA sweeps are historical/model-development diagnostics only; they are not final-paper curves or final-DES inputs. The 50-W prototype is a **qualitative experimental validation anchor**, not an absolute 3-kW validation or a scale-up dataset.

## Active strategy terminology

- C1: conventional threshold charging baseline
- C2: idle-time priority
- C3: low-SOC priority
- C4: **SOC-deadline risk priority** / robust charging-priority heuristic
- C5: **rolling-horizon MILP reference** / optimization-based reference

```text
C4: S_i = 0.75 f_SOC - 0.25 f_D
C5: lambda_soc = 2.0, lambda_task = 1.5, lambda_kpi = 2.0
```

## Final results and validation

- `results/final_unseen/` — one-time unseen raw/summary/statistics/final figures
- `results/model_validation/WPT_MODEL_VALIDATION.md` — nominal-model and 50-W prototype scope
- `results/model_validation/Figure5_WPT_Model_and_Prototype_Validation.pdf` — final Figure 5
- `results/model_validation/final_unseen_nominal_3kw_regression.json` — non-rerun validity check

## Limitations

- Detailed CCCV switching and control dynamics are not modeled.
- Effective-load regulation is simplified to near-matched operation.
- The prototype is 50 W while the DES pad is 3 kW.
- Prototype evidence is qualitative only.

## Archives

- Pre-rho redesign: `archive/pre-rho-redesign-20260917` at `b8ac79046609bbd08b078624d2a68976244d1b6b`
- Pre-6-AGV Primary: `archive/pre-6agv-primary-freeze-20260919` at `71aa37dc69b1d8e388b28e452a53591ed8089623`
- Pre-unseen final: `archive/pre-unseen-final-20260919` at `63bf5d486e061894a29d136272debe738cdb4871`
