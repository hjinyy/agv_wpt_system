from __future__ import annotations

"""Final-DES WPT efficiency callback: nominal 3-kW SS-FHA matched operation.

The logistics DES models a load-regulated receiver chain:
power supply -> inverter -> Tx -> Rx -> rectifier -> DC link -> CCCV buck -> battery.
CCCV duty regulation is represented only by a near-matched resonant-link assumption.
It does not model converter switching/control dynamics or guarantee constant efficiency.
"""

from copy import deepcopy
from functools import lru_cache
from typing import Final

import numpy as np

import v2_runner
from simulation.physical_wpt import default_square_spiral_model

MISALIGNMENT_MM: Final = np.arange(0.0, 176.0, 25.0)
NOMINAL_POWER_KW: Final = 3.0
MODEL: Final = default_square_spiral_model()


class FinalWptConfiguration(dict):
    pass


@lru_cache(maxsize=1)
def _nominal_eta_values() -> tuple[float, ...]:
    """Compute eta(delta) once at the configured 3-kW nominal matched condition."""
    if not np.isclose(MODEL.spec.rated_output_power_kw, NOMINAL_POWER_KW):
        raise ValueError("Final DES requires a 3-kW nominal WPT model")
    return tuple(MODEL.efficiency_curve(MISALIGNMENT_MM).efficiency.tolist())


def physical_efficiency_values(configuration: dict) -> np.ndarray:
    """Return final-DES eta(delta), rejecting non-nominal pad configurations."""
    power_kw = float(configuration.get("wpt_power_kw", NOMINAL_POWER_KW))
    if not np.isclose(power_kw, NOMINAL_POWER_KW):
        raise ValueError(f"Final DES only supports nominal {NOMINAL_POWER_KW:g}-kW WPT pads; got {power_kw:g} kW")
    return np.asarray(_nominal_eta_values(), dtype=float)


def load_final_wpt_configuration() -> FinalWptConfiguration:
    configuration = FinalWptConfiguration(deepcopy(v2_runner.load_cfg()))
    configuration["wpt_power_kw"] = NOMINAL_POWER_KW
    curve = MODEL.efficiency_curve(MISALIGNMENT_MM)
    configuration["efficiency_states"] = {
        "labels": [f"lateral_{int(offset)}mm" for offset in curve.misalignment_mm],
        "misalignment_mm": curve.misalignment_mm.tolist(),
        "physical_efficiency": curve.efficiency.tolist(),
        "probabilities": [1.0 / len(curve.efficiency)] * len(curve.efficiency),
        "source_note": "Uniform 0-175-mm lateral-misalignment sensitivity under nominal 3-kW matched SS-FHA operation.",
    }
    configuration["eta_input_source"] = "geometry_neumann_ss_fha_nominal_3kw_matched"
    configuration["dc_output_voltage_v"] = MODEL.spec.dc_output_voltage_v
    configuration["rectifier_fha_convention"] = MODEL.spec.rectifier_convention
    configuration["cccv_load_regulation_assumption"] = "Near-matched resonant-link operation over the DES charging range; detailed switching/control dynamics are outside scope."
    return configuration
