from __future__ import annotations

"""Generate final Figure 5 and validate that the unseen raw results used only 3-kW eta(delta)."""
import json
import shutil
import subprocess
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

from simulation.final_wpt import MISALIGNMENT_MM, MODEL, NOMINAL_POWER_KW, physical_efficiency_values

ROOT = Path(__file__).resolve().parent
VALIDATION = ROOT / "results" / "model_validation"
FINAL = ROOT / "results" / "final_unseen"
FROZEN_PARAMETERS_SHA = "63bf5d486e061894a29d136272debe738cdb4871"
FINAL_EXECUTION_CODE_SHA = "f148800863a22002c3ed10aee6a55fac3e0769b5"


def _git_show(path: str, sha: str = FINAL_EXECUTION_CODE_SHA) -> str:
    return subprocess.check_output(["git", "show", f"{sha}:{path}"], cwd=ROOT, text=True)


def final_provenance_check() -> dict[str, object]:
    frozen_config = yaml.safe_load(_git_show("config/rho_redesign.yaml"))
    powers = {name: value["wpt_power_kw"] for name, value in frozen_config["scenarios"].items()}
    frozen_callback = _git_show("simulation/final_wpt.py")
    raw = pd.read_csv(FINAL / "raw" / "replication_metrics.csv")
    nominal = physical_efficiency_values({"wpt_power_kw": NOMINAL_POWER_KW})
    mean_efficiency = raw["mean_efficiency"].dropna()
    checks = {
        "frozen_parameters_sha": FROZEN_PARAMETERS_SHA,
        "final_execution_code_sha": FINAL_EXECUTION_CODE_SHA,
        "all_frozen_final_scenarios_nominal_3kw": set(powers.values()) == {NOMINAL_POWER_KW},
        "frozen_runner_uses_physical_efficiency_callback": "physical_efficiency_values" in _git_show("run_unseen_final.py"),
        "frozen_callback_uses_configuration_wpt_power": "configuration.get(\"wpt_power_kw\"" in frozen_callback,
        "raw_final_mean_eta_within_nominal_3kw_curve_range": bool(mean_efficiency.between(float(nominal.min() * 100.0), float(nominal.max() * 100.0)).all()),
        "one_kw_or_five_kw_not_configured_for_final_scenarios": all(float(power) not in {1.0, 5.0} for power in powers.values()),
        "final_raw_rows": int(len(raw)),
        "nominal_3kw_eta_values": [float(value) for value in nominal],
        "nominal_3kw_eta_min_max": [float(nominal.min()), float(nominal.max())],
    }
    checks["final_unseen_numerical_results_remain_valid"] = all(bool(checks[key]) for key in [
        "all_frozen_final_scenarios_nominal_3kw", "frozen_runner_uses_physical_efficiency_callback",
        "frozen_callback_uses_configuration_wpt_power", "raw_final_mean_eta_within_nominal_3kw_curve_range",
        "one_kw_or_five_kw_not_configured_for_final_scenarios",
    ])
    return checks


def generate_figure() -> None:
    VALIDATION.mkdir(parents=True, exist_ok=True)
    prototype = pd.read_csv(VALIDATION / "prototype_measurements.csv")
    eta = physical_efficiency_values({"wpt_power_kw": NOMINAL_POWER_KW}) * 100.0
    figure, (analytical, measured) = plt.subplots(1, 2, figsize=(11.3, 4.3))
    analytical.plot(MISALIGNMENT_MM, eta, color="#f58518", marker="o", linewidth=2.0, label="Nominal 3-kW SS-FHA")
    analytical.set(xlabel="Lateral misalignment $\\delta$ [mm]", ylabel="SS-FHA efficiency [%]", title="(a) Analytical nominal 3-kW model")
    analytical.grid(alpha=0.3); analytical.legend(frameon=False)
    sweep = prototype[prototype["matched_sweep"]]
    gap = prototype[~prototype["matched_sweep"]]
    measured.plot(sweep["pout_w"], sweep["efficiency_pct"], color="#4c78a8", marker="o", linewidth=1.8, label="Matched operating-point sweep")
    measured.scatter(gap["pout_w"], gap["efficiency_pct"], marker="X", color="#e45756", s=75, label="Air-gap X (separate case)", zorder=3)
    for row in gap.itertuples(): measured.annotate(row.label, (row.pout_w, row.efficiency_pct), xytext=(5, -13), textcoords="offset points", fontsize=8)
    measured.set(xlabel="Measured received output power [W]", ylabel="Measured DC-to-DC efficiency [%]", title="(b) 50-W prototype measurement")
    measured.grid(alpha=0.3); measured.legend(frameon=False, fontsize=8)
    figure.text(0.5, -0.05, "Panels are not a direct scale comparison: the 50-W prototype is a qualitative experimental validation anchor, not a 3-kW absolute-efficiency validation.", ha="center", fontsize=8.5)
    figure.tight_layout()
    for suffix, options in (("png", {"dpi": 220}), ("pdf", {})):
        figure.savefig(VALIDATION / f"Figure5_WPT_Model_and_Prototype_Validation.{suffix}", bbox_inches="tight", **options)
    plt.close(figure)
    final_figures = FINAL / "figures"; final_figures.mkdir(parents=True, exist_ok=True)
    for suffix in ("png", "pdf"):
        shutil.copy2(VALIDATION / f"Figure5_WPT_Model_and_Prototype_Validation.{suffix}", final_figures / f"Figure5_WPT_Model_and_Prototype_Validation.{suffix}")
        shutil.copy2(VALIDATION / f"Figure5_WPT_Model_and_Prototype_Validation.{suffix}", final_figures / f"Figure5_wpt_efficiency.{suffix}")


def write_report(check: dict[str, object]) -> None:
    eta = check["nominal_3kw_eta_values"]
    values = "\n".join(f"| {delta:.0f} | {value * 100:.4f} |" for delta, value in zip(MISALIGNMENT_MM, eta))
    lines = [
        "# WPT Model and 50-W Prototype Validation",
        "", "## Final DES model", "- Final DES uses `P_charge(t) = 3 kW × eta(delta_t)` at nominal 3-kW SS-FHA matched operation.",
        "- With `V_dc = 48 V`, `R_L,FHA = (8/pi^2) V_dc^2 / 3,000 = 0.622517 ohm`.",
        "- The modeled chain is power supply → inverter → Tx → Rx → rectifier → DC link → CCCV buck → battery.",
        "- CCCV duty regulation is simplified as a near-matched resonant-link assumption across the DES charging range; it is not a claim of constant efficiency at every output power.",
        "", "## Unseen-final provenance check", f"- All frozen final scenarios use 3 kW: `{check['all_frozen_final_scenarios_nominal_3kw']}`.",
        f"- Frozen runner routes eta through physical callback: `{check['frozen_runner_uses_physical_efficiency_callback']}`; frozen callback reads configured pad power: `{check['frozen_callback_uses_configuration_wpt_power']}`.",
        f"- Raw final mean efficiencies lie within nominal 3-kW eta(delta) range: `{check['raw_final_mean_eta_within_nominal_3kw_curve_range']}`.",
        f"- 1-kW/5-kW curves were absent from final scenario configuration: `{check['one_kw_or_five_kw_not_configured_for_final_scenarios']}`.",
        f"- **Final unseen numerical results remain valid: {check['final_unseen_numerical_results_remain_valid']}.**", "",
        "## Nominal 3-kW eta(delta)", "| Lateral misalignment [mm] | eta [%] |", "| ---: | ---: |", values,
        "", "## 50-W prototype: qualitative experimental validation anchor",
        "- The matched sweep demonstrates that load-regulated operating points can retain approximately 80% or higher efficiency near the matched region and decline away from it.",
        "- Air-gap X is plotted separately from the matched operating-point sweep.",
        "- The prototype does **not** validate 3-kW absolute efficiency, is not directly scaled to 3 kW, and is not claimed to quantitatively match the analytical model.",
        "", "## Limitations", "- Detailed CCCV switching and control dynamics are not modeled.",
        "- Effective-load regulation is reduced to a near-matched operating assumption.",
        "- The prototype is 50 W whereas the DES pad is 3 kW.",
        "- The prototype is qualitative validation only.",
    ]
    (VALIDATION / "WPT_MODEL_VALIDATION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    result = final_provenance_check()
    if not result["final_unseen_numerical_results_remain_valid"]:
        raise SystemExit("Final provenance check failed; no simulation was run.")
    generate_figure()
    write_report(result)
    (VALIDATION / "final_unseen_nominal_3kw_regression.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("WPT_NOMINAL_3KW_VALIDATION_OK")
