# AGV-WPT DES: [3]-Based Experimental WPT-Condition Redesign

`main` is now the pre-tuning implementation of a major research revision. The prior nominal 3-kW SS-FHA package—including its 6-AGV Primary, C4/C5 parameters, 6007–6056 unseen evaluation, figures, and prototype validation—is preserved intact at:

```text
archive/pre-literature-wpt-redesign-20260927
7cfa5ddcf695e09c363a98e1a749072a02d998aa
```

## Active physical source

The active DES uses a literature-based experimental reference lookup, not the former SS-FHA curve:

```text
data/wpt_reference/jeebklum_imura_sumpavakup_2026_table2_misalignment_measurements.csv
```

For each experimental lateral-offset state:

```text
eta(delta) = mean measured X/Y efficiency
P_charge(delta) = 3 kW × mean Pout_reference(delta) / mean Pout_reference(0)
E_delivered = P_charge × duration
E_input = E_delivered / eta
E_loss = E_input − E_delivered
```

The reference data quantify condition variability; they do not imply the literature EV hardware is this AGV hardware. Existing SS-FHA code is supplementary analytical comparison only.

## Controlled alignment sensitivity scenarios

Good, moderate, and severe alignment conditions are controlled sensitivity scenarios, **not claimed empirical AGV docking distributions**. Extreme 250–350 mm lookup states are failure-sensitivity only.

The active representative grid separates charging adequacy and physical variability:

1. resource-rich + good alignment
2. near-boundary + good alignment
3. near-boundary + moderate alignment
4. near-boundary + severe alignment
5. constrained + moderate alignment

`rho` uses mean available delivered power, without multiplying efficiency a second time:

```text
rho = task-demand power / (N_pads × E[P_charge(delta)])
```

## Pre-tuning status

- New tuning seeds: `7007–7056` — **not yet used**
- New unseen final seeds: `8007–8056` — **not yet used**
- Historical tuning/final seed blocks: `5007–5056`, `6007–6056` — not active evidence
- Provisional deadline reform and scenario parameters require review before tuning.

See `docs/LITERATURE_WPT_CONDITION_MODEL.md` and `results/pre_tuning_literature_wpt/PRE_TUNING_AUDIT.md`.
