# PRE_TUNING_METHODOLOGY_FREEZE

## Deadline rule
- `deadline = arrival + T_min(distance) + controlled urgency slack`.
- Selected urgent/normal slack: 240/480 s. This is a **controlled urgency-slack assumption**, not literature-derived.
- The 180/360, 240/480, and 300/600 s sensitivity combinations are structurally feasible because slack is added after irreducible service time; the selected pair preserves a 240-s urgency separation and the legacy 4/8-min allowance magnitudes.

## Physical source
- [3] Table 2 X/Y measured lookup is source-of-truth. Its SHA-256 is recorded in `frozen_methodology.json`.
- `P_charge = 3 kW*g_P`; eta is used only for input/loss accounting and is not multiplied into delivered power.

## Alignment and information
- Good/moderate/severe are controlled misalignment-sensitivity conditions, not empirical fleet distributions. Extreme 250-350 mm is excluded from tuning main scenarios.
- C4/C5 use predicted P_charge; actual SOC/energy/loss use realized state with controlled zero-mean discrete error.

## Scenario naming audit

| scenario                        | physical_condition   |   rho_analytical | rho_region             |   logistics_utilization |
|:--------------------------------|:---------------------|-----------------:|:-----------------------|------------------------:|
| non_binding_good                | good                 |           0.1899 | non_binding            |                  0.6250 |
| near_transition_good            | good                 |           0.8709 | near_transition        |                  0.8750 |
| moderately_constrained_moderate | moderate             |           1.1379 | moderately_constrained |                  0.8750 |
| strongly_constrained_severe     | severe               |           2.2361 | strongly_constrained   |                  0.8750 |
| strongly_constrained_moderate   | moderate             |           1.6441 | strongly_constrained   |                  0.8750 |

All logistics utilizations are below one.
