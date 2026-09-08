from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd  # noqa: PANDAS_OK

import v2_runner
import v3_extended_experiments as v3_extended
import v3_runner
from simulation.physical_wpt import default_square_spiral_model


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results_v_physical_wpt_175mm"
FIG_OUT = ROOT / "results_v_physical_wpt_175mm_figures"
MISALIGNMENT_MM = np.arange(0.0, 176.0, 25.0)
ORIGINAL_LOAD_CFG = v2_runner.load_cfg
MODEL = default_square_spiral_model()
CURVE = MODEL.efficiency_curve(MISALIGNMENT_MM)


def physical_efficiency_values(_: dict) -> np.ndarray:
    return CURVE.efficiency


def load_physical_wpt_cfg():
    cfg = deepcopy(ORIGINAL_LOAD_CFG())
    cfg["efficiency_states"] = {
        "labels": [f"lateral_{int(offset)}mm" for offset in CURVE.misalignment_mm],
        "misalignment_mm": CURVE.misalignment_mm.tolist(),
        "physical_efficiency": CURVE.efficiency.tolist(),
        "probabilities": [1.0 / len(CURVE.efficiency)] * len(CURVE.efficiency),
        "source_note": "Uniform discrete lateral misalignment sensitivity assumption over 0-175 mm.",
    }
    cfg["eta_input_source"] = "geometry_neumann_ss_fha"
    return cfg


def patch_experiment_modules() -> None:
    v2_runner.eta_values = physical_efficiency_values
    v3_runner.eta_values = physical_efficiency_values
    v2_runner.load_cfg = load_physical_wpt_cfg
    v3_runner.load_cfg = load_physical_wpt_cfg
    v3_extended.load_cfg = load_physical_wpt_cfg
    v3_runner.RESULTS = OUT
    v3_extended.OUT = OUT


def write_model_artifacts() -> None:
    OUT.mkdir(exist_ok=True)
    FIG_OUT.mkdir(exist_ok=True)
    curve_frame = pd.DataFrame(
        {
            "lateral_misalignment_mm": CURVE.misalignment_mm,
            "mutual_inductance_uH": CURVE.mutual_inductance_h * 1e6,
            "coupling_coefficient": CURVE.coupling,
            "ss_fha_efficiency_pct": CURVE.efficiency * 100.0,
        }
    )
    curve_frame.to_csv(OUT / "physical_wpt_efficiency_curve.csv", index=False)
    metadata = {
        "topology": "identical planar square spirals",
        "outer_side_mm": 300.0,
        "inner_side_mm": 100.0,
        "turns": 15,
        "turn_pitch_mm": 7.142857,
        "air_gap_mm": 40.0,
        "frequency_khz": 85.0,
        "compensation": "series-series",
        "coil_resistance_ohm_each": 0.15,
        "fha_ac_load_ohm": 0.623,
        "rated_power_kw": 3.0,
        "self_inductance_uH_each": MODEL.self_inductance_h * 1e6,
        "resonance_capacitance_nF_each": MODEL.resonance_capacitance_f * 1e9,
        "quality_factor_each": MODEL.quality_factor,
        "mutual_inductance_method": "segmented Neumann line integral over all 15 square turns",
        "efficiency_method": "lossy SS compensated resonant-link fundamental harmonic approximation",
        "des_misalignment_distribution": "uniform discrete 0-175 mm in 25 mm increments",
    }
    (OUT / "physical_wpt_model_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    figure, axes = plt.subplots(1, 2, figsize=(11.0, 4.2))
    axes[0].plot(CURVE.misalignment_mm, CURVE.mutual_inductance_h * 1e6, marker="o", label="Mutual inductance")
    axes[0].set_xlabel("Lateral misalignment [mm]")
    axes[0].set_ylabel("Mutual inductance [uH]")
    axes[0].grid(alpha=0.3)
    coupling_axis = axes[0].twinx()
    coupling_axis.plot(CURVE.misalignment_mm, CURVE.coupling, color="#e15759", marker="s", label="Coupling coefficient")
    coupling_axis.set_ylabel("Coupling coefficient k")
    axes[1].plot(CURVE.misalignment_mm, CURVE.efficiency * 100.0, color="#59a14f", marker="o")
    axes[1].set_xlabel("Lateral misalignment [mm]")
    axes[1].set_ylabel("SS-FHA efficiency [%]")
    axes[1].grid(alpha=0.3)
    figure.suptitle("Geometry-derived WPT coupling and SS-FHA efficiency")
    figure.tight_layout()
    figure.savefig(FIG_OUT / "Figure_Physical_WPT_Efficiency.png", dpi=300, bbox_inches="tight")
    figure.savefig(FIG_OUT / "Figure_Physical_WPT_Efficiency.pdf", bbox_inches="tight")
    plt.close(figure)


def write_report() -> None:
    primary = pd.read_csv(OUT / "c1_c5_results.csv")
    replication_count = primary["replication"].nunique()
    summary = primary.groupby("strategy")[
        ["mean_delay", "urgent_on_time_rate", "completion_rate", "wpt_loss", "fleet_min_soc", "charging_wait"]
    ].mean()
    lines = [
        "# Physical WPT efficiency experiment",
        "",
        "## Method",
        "",
        "Mutual inductance is computed with a segmented Neumann line integral over each pair of segments in two identical 15-turn 300 mm by 300 mm planar square spirals. The geometry uses a 100 mm inner side, 7.142857 mm turn pitch, 40 mm air gap, and 0-175 mm lateral offset.",
        "",
        "Self-inductance uses the Mohan square-spiral current-sheet expression. The electrical link uses a lossy series-series compensated 85 kHz fundamental harmonic approximation with R1 = R2 = 0.15 ohm and FHA AC load resistance 0.623 ohm. This electromagnetic/FHA calculation supplies efficiency states to the DES; the DES itself does not solve the field or circuit equations.",
        "",
        "## Derived circuit parameters",
        "",
        f"- L1 = L2 = {MODEL.self_inductance_h * 1e6:.3f} uH",
        f"- C1 = C2 = {MODEL.resonance_capacitance_f * 1e9:.3f} nF",
        f"- Q1 = Q2 = {MODEL.quality_factor:.3f}",
        f"- M(0 mm) = {CURVE.mutual_inductance_h[0] * 1e6:.3f} uH; M(175 mm) = {CURVE.mutual_inductance_h[-1] * 1e6:.3f} uH",
        f"- SS-FHA efficiency: {CURVE.efficiency[0] * 100.0:.3f}% at 0 mm and {CURVE.efficiency[-1] * 100.0:.3f}% at 175 mm",
        "",
        "## DES efficiency-state assumption",
        "",
        "Because field data for actual AGV parking error were not supplied, DES samples the eight 0-175 mm states at equal probability. This is a sensitivity assumption, not a measured parking distribution.",
        "",
        f"## Primary Challenge {replication_count}-replication mean",
        "",
        summary.to_markdown(),
        "",
    ]
    (OUT / "REPORT_PHYSICAL_WPT.md").write_text("\n".join(lines), encoding="utf-8")


def write_primary_challenge_figure() -> None:
    primary = pd.read_csv(OUT / "c1_c5_results.csv")
    summary = primary.groupby("strategy")[["mean_delay", "urgent_on_time_rate"]].mean().reindex(
        ["C1", "C2", "C3", "C4", "C5"]
    )
    figure, delay_axis = plt.subplots(figsize=(8.5, 4.5))
    strategies = summary.index.to_list()
    positions = np.arange(len(strategies))
    delay_axis.bar(positions, summary["mean_delay"], color=["#6c757d", "#4c78a8", "#59a14f", "#e15759", "#7b3294"])
    delay_axis.set_xticks(positions, strategies)
    delay_axis.set_xlabel("Charging strategy")
    delay_axis.set_ylabel("Mean task delay [min]")
    delay_axis.grid(axis="y", alpha=0.3)
    urgent_axis = delay_axis.twinx()
    urgent_axis.plot(positions, summary["urgent_on_time_rate"], color="black", marker="o", linewidth=1.5)
    urgent_axis.set_ylabel("Urgent-task on-time completion [%]")
    figure.suptitle("Primary Challenge with geometry-derived 0-175 mm WPT efficiency states")
    figure.tight_layout()
    figure.savefig(FIG_OUT / "Figure_Physical_WPT_175mm_Primary_Challenge.png", dpi=300, bbox_inches="tight")
    figure.savefig(FIG_OUT / "Figure_Physical_WPT_175mm_Primary_Challenge.pdf", bbox_inches="tight")
    plt.close(figure)


def main(debug: bool = False) -> None:
    patch_experiment_modules()
    write_model_artifacts()
    v3_runner.main(debug=debug)
    v3_extended.main(debug=debug)
    write_report()
    write_primary_challenge_figure()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    arguments = parser.parse_args()
    main(debug=arguments.debug)
