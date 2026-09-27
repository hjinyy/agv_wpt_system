# [3]-Based Experimental WPT-Condition Redesign

## Scope

The active DES physical input is the experimental lateral-misalignment lookup from Jeebklum, Imura, and Sumpavakup, *Improving Coil Misalignment Performance in Wireless Power Transfer for Electric Vehicles Using Magnetic Flux Density Analysis*, Table 2. It is a **reference WPT-condition model**: it does not claim that the source paper's EV hardware is the simulated AGV hardware.

The active table is `data/wpt_reference/jeebklum_imura_sumpavakup_2026_table2_misalignment_measurements.csv`. X/Y means are stored explicitly and derived quantities are calculated from raw values:

\[
g_P(\delta)=\bar P_{out,[3]}(\delta)/\bar P_{out,[3]}(0),\qquad
P_{charge}(\delta)=3\,g_P(\delta)\ \mathrm{kW}.
\]

\[
\eta(\delta)=\left(\eta_X(\delta)+\eta_Y(\delta)\right)/2.
\]

For a charge duration \(\Delta t\):

\[
E_{delivered}=P_{charge}\Delta t,\quad E_{input}=E_{delivered}/\eta,\quad E_{loss}=E_{input}-E_{delivered}.
\]

`P_charge` is already battery-side available power; eta is therefore not multiplied into it again.

## Alignment conditions

Good, moderate, and severe are **controlled misalignment-sensitivity conditions**, not empirical AGV docking distributions. Literature indicates docking accuracy depends strongly on navigation and sensing stack, ranging from sub-mm marker systems to centimetre-scale docking; it does not justify a universal fleet distribution. The 250–350 mm table states are extreme/failure sensitivity only and excluded from normal-operation representative scenarios.

## Prediction information

C4 and C5 use only the predicted lookup state. The realized state is `predicted state + epsilon`, where epsilon is a clipped, zero-mean discrete error. The active representative severe/moderate cases use `P(epsilon=-50 mm,0,+50 mm)=(0.2,0.6,0.2)`; good alignment uses perfect-prediction sensitivity. This is a controlled sensitivity assumption, not an empirical error estimate.

## Provisional deadlines

The historical fixed urgent 4-minute deadline is structurally infeasible at long distances: at 80 m, minimum task service time is 250 s. The pre-tuning proposal is:

\[
deadline_j=arrival_j+minimum\ service\ time_j+slack_{urgency},
\]

with 240 s urgent and 480 s normal slack. These are **not frozen**; approval is required before tuning.

## C4

\[
S_{i,p}=w_{SOC}f_{SOC,i}+w_Ef_{E,i}+w_{idle}f_{idle,i}+w_P f_{P,i,p}-w_Df_{D,i},
\qquad f_{P,i,p}=\hat P_{charge,i,p}/3\ \mathrm{kW}.
\]

All weights are nonnegative and sum to one. The C4 implementation remains a lightweight greedy heuristic. The reference lookup currently provides a condition per charging opportunity rather than independently measured pad-specific effects; `pad_id` is nevertheless accepted at the scoring interface so future pad-specific condition data can be represented without changing the equation. No positive `w_P` is forced.

## Separation from historical model

`simulation/physical_wpt.py` and `config/wpt_model.yaml` remain available only for analytical/supplementary comparison. They are not called by the active [3]-based DES condition interface.
