from __future__ import annotations

"""Create a pre-final parameter manifest after C4 and C5 tuning complete."""

import json
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "pre_final"
CONFIG = ROOT / "config" / "rho_redesign.yaml"


def main() -> None:
    data = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    c4 = json.loads((ROOT / "results" / "tuning" / "frozen_c4_parameters.json").read_text(encoding="utf-8"))
    c5 = json.loads((OUT / "frozen_c5_parameters.json").read_text(encoding="utf-8"))
    source_sha = subprocess.check_output(["git", "rev-parse", "a2a7a0b"], cwd=ROOT, text=True).strip()
    tuning = list(range(data["seeds"]["tuning_start"], data["seeds"]["tuning_end"] + 1))
    final = list(range(data["seeds"]["planned_final_start"], data["seeds"]["planned_final_end"] + 1))
    manifest = {
        "manifest_status": "pre-final parameters frozen; unseen final evaluation not executed",
        "source_git_sha": source_sha,
        "wpt_model_version": "config/wpt_model.yaml; SS-compensated FHA geometry model with power-dependent eta(delta,P)",
        "V_dc_V": 48.0,
        "rho_definition": "rho = task-demand power / (n_pads * P_wpt * mean_eta); demand uses DES round-trip task travel plus service auxiliary energy and excludes scheduling-dependent pad detours",
        "base_parameters": data["scenarios"]["base"],
        "primary_parameters": data["scenarios"]["primary"],
        "stress_scenarios": {key: value for key, value in data["scenarios"].items() if key.startswith("stress_")},
        "c4_general_formulation": data["c4_general_formulation"],
        "frozen_c4_active_weights": c4["weights"],
        "c5_frozen_scales": c5["scales"],
        "c5_structure": {"horizon_s": data["c5_revalidation"]["horizon_s"], "slot_s": data["c5_revalidation"]["slot_s"], "execution": "first-slot receding-horizon implementation"},
        "c5_terminology": "rolling-horizon MILP reference / optimization-based reference",
        "tuning_seeds": tuning,
        "planned_final_seeds": final,
        "seed_overlap": len(set(tuning) & set(final)),
        "final_evaluation_executed": False,
        "final_figures_generated": False,
    }
    assert manifest["seed_overlap"] == 0
    (OUT / "frozen_experiment_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
