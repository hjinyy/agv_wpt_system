import numpy as np


def test_square_spiral_model_reduces_coupling_and_efficiency_with_lateral_offset():
    from simulation.physical_wpt import default_square_spiral_model

    model = default_square_spiral_model()
    curve = model.efficiency_curve(np.array([0.0, 50.0, 100.0]))
    assert model.self_inductance_h > 0.0
    assert model.quality_factor > 0.0
    assert curve.mutual_inductance_h[0] > curve.mutual_inductance_h[-1] > 0.0
    assert 0.0 < curve.efficiency[2] < curve.efficiency[1] < curve.efficiency[0] < 1.0


def test_square_spiral_mutual_inductance_is_symmetric_about_coaxial_alignment():
    from simulation.physical_wpt import default_square_spiral_model

    model = default_square_spiral_model()
    curve = model.efficiency_curve(np.array([-60.0, 60.0]))
    assert np.isclose(curve.mutual_inductance_h[0], curve.mutual_inductance_h[1], rtol=1e-8)


def test_des_physical_efficiency_states_stop_at_the_normal_charging_limit():
    from run_physical_wpt_experiments import MISALIGNMENT_MM

    assert np.array_equal(MISALIGNMENT_MM, np.arange(0.0, 176.0, 25.0))
