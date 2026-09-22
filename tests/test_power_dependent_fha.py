import math

import numpy as np

from simulation.final_wpt import physical_efficiency_values
from simulation.physical_wpt import default_square_spiral_model


def test_fha_equivalent_load_is_derived_from_explicit_48v_dc_assumption():
    model = default_square_spiral_model()

    assert model.spec.dc_output_voltage_v == 48.0
    assert math.isclose(model.fha_load_resistance_ohm(1.0), (8 / math.pi**2) * 48**2 / 1_000, rel_tol=1e-12)
    assert math.isclose(model.fha_load_resistance_ohm(3.0), (8 / math.pi**2) * 48**2 / 3_000, rel_tol=1e-12)
    assert math.isclose(model.fha_load_resistance_ohm(5.0), (8 / math.pi**2) * 48**2 / 5_000, rel_tol=1e-12)


def test_efficiency_curve_recomputes_load_for_requested_power():
    model = default_square_spiral_model()
    offsets = np.array([0.0, 75.0, 175.0])
    one_kw = model.efficiency_curve(offsets, output_power_kw=1.0)
    three_kw = model.efficiency_curve(offsets, output_power_kw=3.0)
    five_kw = model.efficiency_curve(offsets, output_power_kw=5.0)

    assert one_kw.load_resistance_ohm > three_kw.load_resistance_ohm > five_kw.load_resistance_ohm
    assert np.all(one_kw.efficiency > 0)
    assert np.all(three_kw.efficiency > 0)
    assert np.all(five_kw.efficiency > 0)
    assert not np.allclose(one_kw.efficiency, five_kw.efficiency)


def test_final_wpt_efficiency_callback_is_fixed_to_nominal_3kw():
    eta = physical_efficiency_values({"wpt_power_kw": 3.0})
    assert eta.shape == (8,)
    import pytest
    with pytest.raises(ValueError, match="3-kW"):
        physical_efficiency_values({"wpt_power_kw": 1.0})
    with pytest.raises(ValueError, match="3-kW"):
        physical_efficiency_values({"wpt_power_kw": 5.0})
