# WPT Model and 50-W Prototype Validation

## Final DES model
- Final DES uses `P_charge(t) = 3 kW × eta(delta_t)` at nominal 3-kW SS-FHA matched operation.
- With `V_dc = 48 V`, `R_L,FHA = (8/pi^2) V_dc^2 / 3,000 = 0.622517 ohm`.
- The modeled chain is power supply → inverter → Tx → Rx → rectifier → DC link → CCCV buck → battery.
- CCCV duty regulation is simplified as a near-matched resonant-link assumption across the DES charging range; it is not a claim of constant efficiency at every output power.

## Unseen-final provenance check
- All frozen final scenarios use 3 kW: `True`.
- Frozen runner routes eta through physical callback: `True`; frozen callback reads configured pad power: `True`.
- Raw final mean efficiencies lie within nominal 3-kW eta(delta) range: `True`.
- 1-kW/5-kW curves were absent from final scenario configuration: `True`.
- **Final unseen numerical results remain valid: True.**

## Nominal 3-kW eta(delta)
| Lateral misalignment [mm] | eta [%] |
| ---: | ---: |
| 0 | 80.5416 |
| 25 | 80.5381 |
| 50 | 80.5264 |
| 75 | 80.5008 |
| 100 | 80.4451 |
| 125 | 80.3072 |
| 150 | 79.8583 |
| 175 | 77.2354 |

## 50-W prototype: qualitative experimental validation anchor
- The matched sweep demonstrates that load-regulated operating points can retain approximately 80% or higher efficiency near the matched region and decline away from it.
- Air-gap X is plotted separately from the matched operating-point sweep.
- The prototype does **not** validate 3-kW absolute efficiency, is not directly scaled to 3 kW, and is not claimed to quantitatively match the analytical model.

## Limitations
- Detailed CCCV switching and control dynamics are not modeled.
- Effective-load regulation is reduced to a near-matched operating assumption.
- The prototype is 50 W whereas the DES pad is 3 kW.
- The prototype is qualitative validation only.
