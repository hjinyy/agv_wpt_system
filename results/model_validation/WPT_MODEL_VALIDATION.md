# WPT Model Validation

## R_L provenance status
- Repository/history search found no explicit historical 48-V, DC-output-voltage, or rectifier/FHA-load derivation.
- The former hard-coded `0.623 ohm` is **consistent with** (not proven to be originally documented as) a 48-V, 3-kW DC load under the full-wave/full-bridge FHA convention:
  `R_L,FHA = (8/pi^2) R_dc = (8/pi^2) V_dc^2 / P_out`.
- `48 V` is now an explicit nominal DC-side paper-model assumption in `config/wpt_model.yaml`; it is not claimed as an empirical AGV specification.

## Scope boundary
- This model computes `eta(delta, P_out)` only. It does not implement `P_deliverable`; source/inverter/current/apparent-power limits are unavailable.

## R_L,FHA and efficiency sanity values
| P_out [kW] | delta [mm] | M [uH] | kappa | kappa Q | R_L,FHA [ohm] | eta [%] |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0 | 28.13385 | 0.507706 | 100.170 | 1.867552 | 92.4413 |
| 1 | 75 | 19.94582 | 0.359944 | 71.017 | 1.867552 | 92.3190 |
| 1 | 175 | 3.06158 | 0.055250 | 10.901 | 1.867552 | 83.1528 |
| 3 | 0 | 28.13385 | 0.507706 | 100.170 | 0.622517 | 80.5416 |
| 3 | 75 | 19.94582 | 0.359944 | 71.017 | 0.622517 | 80.5008 |
| 3 | 175 | 3.06158 | 0.055250 | 10.901 | 0.622517 | 77.2354 |
| 5 | 0 | 28.13385 | 0.507706 | 100.170 | 0.373510 | 71.3225 |
| 5 | 75 | 19.94582 | 0.359944 | 71.017 | 0.373510 | 71.2979 |
| 5 | 175 | 3.06158 | 0.055250 | 10.901 | 0.373510 | 69.3115 |

## Neumann convergence
- At 16 segments/side, maximum absolute M error versus the 64-segment reference across 0/75/175 mm is 0.1947%.

## C4 eta-feature influence diagnostic
- Candidate decision events: 67379; contention events: 32352.
- Mean within-event normalized eta-feature standard deviation: 0.004203; among contention events: 0.008753.
- Removing only the eta term changes selected AGV(s) in 196 events (0.2909%), and 196 contention events (0.6058%).

## Decision
- This report records measured influence only; it does not retune weights or change C4 feature count. A 5-feature versus 4-feature decision must be made after reviewing the recorded rates.
