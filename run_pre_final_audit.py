from __future__ import annotations

"""Pre-final audit only. It never runs 6007-6056 or C5 refinement."""

import json
from pathlib import Path

import pandas as pd

from rho_pipeline import configuration_for, scenarios, tuning_seeds
from simulation.charging_adequacy import adequacy_for_scenario

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "pre_final"
TUNING = ROOT / "results" / "tuning"
FROZEN_C4 = {"soc": 0.75, "next_task_energy": 0.0, "idle": 0.0, "deadline": 0.25}


def fleet_candidate(name: str, n_agvs: int, distances_m: tuple[float, ...], rate: float) -> dict[str, object]:
    base = scenarios()["primary"]
    scenario = type(base)(name=name, role="fleet_size_audit", n_agvs=n_agvs, n_pads=1, task_arrival_rate_per_h=rate,
                          wpt_power_kw=3.0, distances_m=distances_m, urgent_ratio=0.2)
    configuration = configuration_for(scenario, FROZEN_C4)
    adequacy = adequacy_for_scenario(configuration, scenario.distances, tuning_seeds())
    return {"candidate": name, "n_agvs": n_agvs, "distances_m": "|".join(map(str, distances_m)), "task_arrival_rate_per_h": rate,
            "mean_task_energy_kwh": adequacy.mean_task_energy_kwh, "rho_analytical": adequacy.rho_analytical,
            "rho_simulation_based": adequacy.rho_simulation_based, "logistics_utilization": adequacy.logistics_utilization,
            "service_capacity_tasks_per_h": n_agvs / ((2 * adequacy.mean_task_distance_m / configuration["agv_speed_mps"] + configuration["picking_service_s"] + configuration["staging_service_s"]) / 3600.0),
            "fleet_per_pad": n_agvs, "charging_contention_pressure_proxy": adequacy.rho_analytical * n_agvs}


def c4_primary_sanity() -> dict[str, object]:
    c4 = pd.read_csv(TUNING / "c4_local_refinement.csv")
    c3 = pd.read_csv(TUNING / "reference_strategies.csv")
    mask = ((c4.soc == 0.75) & (c4.next_task_energy == 0.0) & (c4.idle == 0.0) & (c4.deadline == 0.25) & (c4.scenario == "primary"))
    left = c4.loc[mask, ["replication", "mean_delay", "urgent_on_time_rate"]].set_index("replication").sort_index()
    right = c3[(c3.strategy == "C3") & (c3.scenario == "primary")][["replication", "mean_delay", "urgent_on_time_rate"]].set_index("replication").sort_index()
    assert len(left) == len(right) == 50
    delay = left.mean_delay - right.mean_delay
    urgent = left.urgent_on_time_rate - right.urgent_on_time_rate
    assert left.urgent_on_time_rate.between(0.0, 100.0).all()
    assert right.urgent_on_time_rate.between(0.0, 100.0).all()
    return {"paired_replications": 50, "C4_minus_C3_mean_delay_min": float(delay.mean()),
            "C4_minus_C3_mean_urgent_on_time_percentage_points": float(urgent.mean()),
            "urgent_metric_unit": "percent (0-100); difference reported in percentage points",
            "C4_urgent_range_percent": [float(left.urgent_on_time_rate.min()), float(left.urgent_on_time_rate.max())],
            "C3_urgent_range_percent": [float(right.urgent_on_time_rate.min()), float(right.urgent_on_time_rate.max())]}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    candidates = [
        fleet_candidate("A_5AGV_40to80m_90perh", 5, (40, 50, 60, 70, 80), 90),
        fleet_candidate("B_6AGV_40to80m_90perh", 6, (40, 50, 60, 70, 80), 90),
        fleet_candidate("C_7AGV_50to90m_90perh_current", 7, (50, 60, 70, 80, 90), 90),
    ]
    fleet = pd.DataFrame(candidates)
    fleet.to_csv(OUT / "primary_fleet_size_sanity.csv", index=False)
    c4 = c4_primary_sanity()
    (OUT / "c4_primary_paired_sanity.json").write_text(json.dumps(c4, indent=2), encoding="utf-8")
    report = [
        "# Pre-final Audit",
        "",
        "## C4 terminology recommendation",
        "- General candidate formulation: `w_SOC f_SOC + w_E f_E + w_idle f_idle - w_D f_D`.",
        "- Robustly selected final rule from the current tuning: `0.75 f_SOC - 0.25 f_D`.",
        "- Recommended terminology: **SOC-deadline risk priority** or **robust charging-priority heuristic**. Do not call the selected rule a four-feature multi-feature heuristic.",
        "",
        "## C4 Primary raw-data sanity", "```json", json.dumps(c4, indent=2), "```",
        "",
        "## Primary fleet-size analytical audit", fleet.to_markdown(index=False, floatfmt=".4f"),
        "",
        "### Finding and stop condition",
        "- A (5 AGVs) reaches rho near 1 only with logistics utilization above 1; it confounds logistics overload with charging constraint.",
        "- B (6 AGVs, 40/50/60/70/80 m) reaches rho about 1.01 with logistics utilization below 1 and changes fleet size by +1 relative to the historical 5-AGV basis.",
        "- C (current 7-AGV Primary) also meets the rho target but changes fleet size by +2.",
        "- Therefore B is the simpler, equally valid Primary design under the stated selection rules. Changing Primary invalidates the C4 tuning that used C; no C5 50-rep revalidation/refinement, manifest freeze, unseen evaluation, or final figure generation was executed.",
        "",
        "## C5 scope status",
        "- No C5 revalidation/refinement results are accepted in this audit because the primary scenario must be changed first.",
        "- A one-seed C5 cost pilot was performed before the fleet verdict solely to estimate compute: 5,015 solver calls over five scenarios. It is not a 50-rep performance result and is not used for parameter selection.",
        "- C5 remains an **optimization-based reference** / **rolling-horizon MILP reference**, never an independent or clairvoyant global-optimal benchmark.",
        "",
        "## Freeze status",
        "- WPT model: frozen.",
        "- Current C4 weights: frozen only for the now-superseded 7-AGV Primary tuning; they must be retuned after approving the 6-AGV Primary.",
        "- C5 scales: not frozen for rho-redesign final evaluation.",
        "- Planned unseen final seeds 6007-6056: unused.",
    ]
    (OUT / "PRE_FINAL_AUDIT.md").write_text("\n".join(report) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
