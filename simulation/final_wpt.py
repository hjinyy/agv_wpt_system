from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from typing import Final

import numpy as np

import v2_runner
from simulation.physical_wpt import default_square_spiral_model


MISALIGNMENT_MM: Final = np.arange(0.0, 176.0, 25.0)
MODEL: Final = default_square_spiral_model()


class FinalWptConfiguration(dict):
    pass


@lru_cache(maxsize=None)
def _cached_physical_efficiency_values(power_kw: float) -> tuple[float, ...]:
    return tuple(MODEL.efficiency_curve(MISALIGNMENT_MM, output_power_kw=power_kw).efficiency.tolist())


def physical_efficiency_values(configuration: dict) -> np.ndarray:
    """Return cached eta(delta, P_out) under the configured SS-FHA DC-side assumption."""
    power_kw = float(configuration.get("wpt_power_kw", MODEL.spec.rated_output_power_kw))
    return np.asarray(_cached_physical_efficiency_values(power_kw), dtype=float)


def load_final_wpt_configuration() -> FinalWptConfiguration:
    configuration = FinalWptConfiguration(deepcopy(v2_runner.load_cfg()))
    curve = MODEL.efficiency_curve(MISALIGNMENT_MM, output_power_kw=float(configuration["wpt_power_kw"]))
    configuration["efficiency_states"] = {
        "labels": [f"lateral_{int(offset)}mm" for offset in curve.misalignment_mm],
        "misalignment_mm": curve.misalignment_mm.tolist(),
        "physical_efficiency": curve.efficiency.tolist(),
        "probabilities": [1.0 / len(curve.efficiency)] * len(curve.efficiency),
        "source_note": "Uniform discrete lateral-misalignment sensitivity assumption over 0-175 mm; eta is recomputed when output power changes.",
    }
    configuration["eta_input_source"] = "geometry_neumann_ss_fha_power_dependent"
    configuration["dc_output_voltage_v"] = MODEL.spec.dc_output_voltage_v
    configuration["rectifier_fha_convention"] = MODEL.spec.rectifier_convention
    return configuration
