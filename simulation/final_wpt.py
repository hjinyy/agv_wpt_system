from __future__ import annotations

from copy import deepcopy
from typing import Final

import numpy as np

import v2_runner
from simulation.physical_wpt import default_square_spiral_model


MISALIGNMENT_MM: Final = np.arange(0.0, 176.0, 25.0)
MODEL: Final = default_square_spiral_model()
CURVE: Final = MODEL.efficiency_curve(MISALIGNMENT_MM)


class FinalWptConfiguration(dict):
    pass


def physical_efficiency_values(_: dict) -> np.ndarray:
    return CURVE.efficiency


def load_final_wpt_configuration() -> FinalWptConfiguration:
    configuration = FinalWptConfiguration(deepcopy(v2_runner.load_cfg()))
    configuration["efficiency_states"] = {
        "labels": [f"lateral_{int(offset)}mm" for offset in CURVE.misalignment_mm],
        "misalignment_mm": CURVE.misalignment_mm.tolist(),
        "physical_efficiency": CURVE.efficiency.tolist(),
        "probabilities": [1.0 / len(CURVE.efficiency)] * len(CURVE.efficiency),
        "source_note": "Uniform discrete lateral misalignment sensitivity assumption over 0-175 mm.",
    }
    configuration["eta_input_source"] = "geometry_neumann_ss_fha"
    return configuration
