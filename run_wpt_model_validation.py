from __future__ import annotations

"""Generate SS-FHA physical validation and a C4 eta-feature influence diagnostic.

This is a model-validation diagnostic, not rho redesign, weight tuning, or final evaluation.
It uses the already-examined legacy final seed block only to inspect C4 decision mechanics.
"""

import csv
import json
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import replace
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import v2_runner
import v3_runner
from final_evaluation import FINAL_EVALUATION_SEEDS, PRIMARY_DISTANCES, final_configuration
from simulation.final_wpt import physical_efficiency_values
from simulation.physical_wpt import SquareSpiralWptModel, default_square_spiral_model
from v2_runner import generate_common
from v3_runner import V3Sim

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "model_validation"
MISALIGNMENTS_MM = np.arange(0.0, 176.0, 25.0)
POWERS_KW = (1.0, 3.0, 5.0)


def _git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_physical_rows() -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    model = default_square_spiral_model()
    power_rows: list[dict[str, object]] = []
    for power_kw in POWERS_KW:
        curve = model.efficiency_curve(MISALIGNMENTS_MM, output_power_kw=power_kw)
        for offset, mutual, coupling, eta in zip(curve.misalignment_mm, curve.mutual_inductance_h, curve.coupling, curve.efficiency):
            power_rows.append({
                "git_commit": _git_sha(), "misalignment_mm": float(offset), "output_power_kw": power_kw,
                "mutual_inductance_uH": float(mutual * 1e6), "coupling_kappa": float(coupling),
                "kappa_Q": float(coupling * model.quality_factor), "R_L_FHA_ohm": float(curve.load_resistance_ohm),
                "efficiency_pct": float(eta * 100.0), "dc_output_voltage_v": model.spec.dc_output_voltage_v,
                "rectifier_fha_factor": model.spec.rectifier_fha_factor,
            })
    convergence_rows: list[dict[str, object]] = []
    reference = SquareSpiralWptModel(replace(model.spec, segments_per_side=64))
    reference_curve = reference.efficiency_curve(np.array([0.0, 75.0, 175.0]), output_power_kw=3.0)
    ref_m = dict(zip(reference_curve.misalignment_mm, reference_curve.mutual_inductance_h))
    for segments in (8, 16, 32, 64):
        candidate = SquareSpiralWptModel(replace(model.spec, segments_per_side=segments))
        curve = candidate.efficiency_curve(np.array([0.0, 75.0, 175.0]), output_power_kw=3.0)
        for offset, mutual, coupling, eta in zip(curve.misalignment_mm, curve.mutual_inductance_h, curve.coupling, curve.efficiency):
            convergence_rows.append({
                "git_commit": _git_sha(), "segments_per_side": segments, "misalignment_mm": float(offset),
                "mutual_inductance_uH": float(mutual * 1e6), "coupling_kappa": float(coupling),
                "efficiency_pct": float(eta * 100.0),
                "M_relative_error_vs_64_pct": float((mutual - ref_m[offset]) / ref_m[offset] * 100.0),
            })
    metadata = {
        "git_commit": _git_sha(), "model": "SS-compensated square-spiral WPT under FHA",
        "dc_output_voltage_v": model.spec.dc_output_voltage_v,
        "rectifier_convention": model.spec.rectifier_convention,
        "R_L_FHA_formula": "(8/pi^2) * V_dc^2 / P_out",
        "rated_output_power_kw": model.spec.rated_output_power_kw,
        "P_deliverable_implemented": False,
        "P_deliverable_reason": "Source/inverter/coil-current/apparent-power limits are not parameterized.",
    }
    return power_rows, convergence_rows, metadata


def _run_eta_influence(seed: int) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    v2_runner.eta_values = physical_efficiency_values
    v3_runner.eta_values = physical_efficiency_values
    configuration = final_configuration()
    configuration.update({"n_agvs": 5, "n_pads": 1, "task_arrival_rate_per_h": 90, "wpt_power_kw": 3})
    tasks, initial_soc = generate_common(configuration, seed, distances=PRIMARY_DISTANCES, urgent_ratio=0.2)
    lookup = {task.task_id: index for index, task in enumerate(tasks)}
    simulation = V3Sim(configuration, "C4", seed, tasks, initial_soc, "eta_feature_validation_primary", variable_eta=True, task_index_lookup=lookup, predicted_eta_mode="variable", realized_eta_mode="variable")
    simulation.run()
    return simulation.feature_rows, simulation.eta_influence_rows


def build_eta_diagnostic() -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    features: list[dict[str, object]] = []
    events: list[dict[str, object]] = []
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(_run_eta_influence, seed) for seed in FINAL_EVALUATION_SEEDS]
        for completed, future in enumerate(as_completed(futures), start=1):
            feature_rows, event_rows = future.result()
            features.extend(feature_rows)
            events.extend(event_rows)
            if completed % 10 == 0 or completed == len(FINAL_EVALUATION_SEEDS):
                print(f"eta-feature diagnostic: {completed}/{len(FINAL_EVALUATION_SEEDS)}", flush=True)
    events = sorted(events, key=lambda row: (int(row["replication"]), float(row["time_s"])))
    frame = pd.DataFrame(events)
    contention = frame[frame["contention_event"] == 1]
    summary = {
        "git_commit": _git_sha(), "scenario": "eta_feature_validation_primary",
        "seed_block": f"{FINAL_EVALUATION_SEEDS[0]}-{FINAL_EVALUATION_SEEDS[-1]}",
        "purpose": "post-hoc C4 eta-feature decision-mechanics diagnostic; not a new final evaluation",
        "candidate_decision_events": int(len(frame)),
        "contention_events": int(len(contention)),
        "mean_candidate_eta_feature_std": float(frame["eta_feature_std"].mean()) if len(frame) else 0.0,
        "contention_eta_feature_std_mean": float(contention["eta_feature_std"].mean()) if len(contention) else 0.0,
        "selection_changed_events": int(frame["eta_term_changed_selection"].sum()) if len(frame) else 0,
        "selection_changed_event_rate_pct": float(frame["eta_term_changed_selection"].mean() * 100.0) if len(frame) else 0.0,
        "contention_selection_changed_events": int(contention["eta_term_changed_selection"].sum()) if len(contention) else 0,
        "contention_selection_changed_rate_pct": float(contention["eta_term_changed_selection"].mean() * 100.0) if len(contention) else 0.0,
        "feature_observations": int(len(features)),
        "eta_WPT_feature_std_all_observations": float(pd.DataFrame(features)["eta_WPT"].std(ddof=1)) if features else 0.0,
    }
    return features, events, summary


def _figure(power_rows: list[dict[str, object]]) -> None:
    frame = pd.DataFrame(power_rows)
    figure, axis = plt.subplots(figsize=(7.2, 4.5))
    colors = {1.0: "#4c78a8", 3.0: "#f58518", 5.0: "#54a24b"}
    for power in POWERS_KW:
        data = frame[frame["output_power_kw"] == power]
        axis.plot(data["misalignment_mm"], data["efficiency_pct"], marker="o", linewidth=1.8, color=colors[power], label=f"{power:.0f} kW")
    axis.set_xlabel("Lateral misalignment [mm]")
    axis.set_ylabel("SS-FHA efficiency [%]")
    axis.set_title("Power-dependent SS-FHA efficiency under 48-V nominal DC-side assumption")
    axis.grid(alpha=0.28)
    axis.legend(title="Output power")
    figure.tight_layout()
    figure.savefig(OUT / "Figure_Efficiency_vs_Misalignment_and_Power.png", dpi=220)
    figure.savefig(OUT / "Figure_Efficiency_vs_Misalignment_and_Power.pdf")
    plt.close(figure)


def _write_report(power_rows: list[dict[str, object]], convergence_rows: list[dict[str, object]], eta_summary: dict[str, object]) -> None:
    power = pd.DataFrame(power_rows)
    convergence = pd.DataFrame(convergence_rows)
    selected = power[power["misalignment_mm"].isin([0.0, 75.0, 175.0])]
    convergence_16 = convergence[convergence["segments_per_side"] == 16]
    lines = [
        "# WPT Model Validation",
        "",
        "## R_L provenance status",
        "- Repository/history search found no explicit historical 48-V, DC-output-voltage, or rectifier/FHA-load derivation.",
        "- The former hard-coded `0.623 ohm` is **consistent with** (not proven to be originally documented as) a 48-V, 3-kW DC load under the full-wave/full-bridge FHA convention:",
        "  `R_L,FHA = (8/pi^2) R_dc = (8/pi^2) V_dc^2 / P_out`.",
        "- `48 V` is now an explicit nominal DC-side paper-model assumption in `config/wpt_model.yaml`; it is not claimed as an empirical AGV specification.",
        "",
        "## Scope boundary",
        "- This model computes `eta(delta, P_out)` only. It does not implement `P_deliverable`; source/inverter/current/apparent-power limits are unavailable.",
        "",
        "## R_L,FHA and efficiency sanity values",
        "| P_out [kW] | delta [mm] | M [uH] | kappa | kappa Q | R_L,FHA [ohm] | eta [%] |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        *(f"| {row.output_power_kw:.0f} | {row.misalignment_mm:.0f} | {row.mutual_inductance_uH:.5f} | {row.coupling_kappa:.6f} | {row.kappa_Q:.3f} | {row.R_L_FHA_ohm:.6f} | {row.efficiency_pct:.4f} |" for row in selected.itertuples()),
        "",
        "## Neumann convergence",
        f"- At 16 segments/side, maximum absolute M error versus the 64-segment reference across 0/75/175 mm is {convergence_16['M_relative_error_vs_64_pct'].abs().max():.4f}%.",
        "",
        "## C4 eta-feature influence diagnostic",
        f"- Candidate decision events: {eta_summary['candidate_decision_events']}; contention events: {eta_summary['contention_events']}.",
        f"- Mean within-event normalized eta-feature standard deviation: {eta_summary['mean_candidate_eta_feature_std']:.6f}; among contention events: {eta_summary['contention_eta_feature_std_mean']:.6f}.",
        f"- Removing only the eta term changes selected AGV(s) in {eta_summary['selection_changed_events']} events ({eta_summary['selection_changed_event_rate_pct']:.4f}%), and {eta_summary['contention_selection_changed_events']} contention events ({eta_summary['contention_selection_changed_rate_pct']:.4f}%).",
        "",
        "## Decision",
        "- This report records measured influence only; it does not retune weights or change C4 feature count. A 5-feature versus 4-feature decision must be made after reviewing the recorded rates.",
    ]
    (OUT / "WPT_MODEL_VALIDATION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    power_rows, convergence_rows, metadata = build_physical_rows()
    _write_csv(OUT / "power_dependent_fha_curve.csv", power_rows)
    _write_csv(OUT / "neumann_convergence.csv", convergence_rows)
    _figure(power_rows)
    features, events, eta_summary = build_eta_diagnostic()
    _write_csv(OUT / "c4_eta_feature_observations.csv", features)
    _write_csv(OUT / "c4_eta_feature_influence_events.csv", events)
    (OUT / "c4_eta_feature_influence_summary.json").write_text(json.dumps(eta_summary, indent=2), encoding="utf-8")
    (OUT / "wpt_model_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    _write_report(power_rows, convergence_rows, eta_summary)


if __name__ == "__main__":
    main()
