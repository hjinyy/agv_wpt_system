from __future__ import annotations

"""SS-compensated square-spiral WPT model under the fundamental-harmonic approximation.

The nominal DC side is a paper-model design assumption, not an empirical AGV specification.
The generic evaluator can compute an FHA curve for a requested output power using
``R_L,FHA = (8/pi^2) R_dc = (8/pi^2) V_dc^2 / P_out``.  Such arbitrary-power sweeps
are retained only as historical/model-development diagnostics.

The final DES callback is instead fixed to the nominal 3-kW matched condition and uses
``eta(delta)``. It represents CCCV load regulation through a near-matched resonant-link
assumption, not through a direct fixed-load ``R_L ∝ 1/P_out`` trajectory.

This model returns efficiency only. It does not model source/inverter/current/apparent-power
limits or detailed CCCV switching/control dynamics and must not be interpreted as a
deliverable-power-limit model.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np
import yaml
from numpy.typing import NDArray


MU_0: Final = 4.0e-7 * np.pi
MOHAN_SQUARE_C1: Final = 1.27
MOHAN_SQUARE_C2: Final = 2.07
MOHAN_SQUARE_C3: Final = 0.18
MOHAN_SQUARE_C4: Final = 0.13
CONFIG_PATH: Final = Path(__file__).resolve().parents[1] / "config" / "wpt_model.yaml"


@dataclass(frozen=True, slots=True)
class SquareSpiralSpec:
    outer_side_m: float
    inner_side_m: float
    turns: int
    air_gap_m: float
    frequency_hz: float
    coil_resistance_ohm: float
    dc_output_voltage_v: float
    rated_output_power_kw: float
    rectifier_fha_factor: float
    rectifier_convention: str
    segments_per_side: int


@dataclass(frozen=True, slots=True)
class EfficiencyCurve:
    misalignment_mm: NDArray[np.float64]
    output_power_kw: float
    load_resistance_ohm: float
    mutual_inductance_h: NDArray[np.float64]
    coupling: NDArray[np.float64]
    efficiency: NDArray[np.float64]


def load_square_spiral_spec(path: Path = CONFIG_PATH) -> SquareSpiralSpec:
    """Load the one source-of-truth WPT geometry/network/DC-side assumption."""
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    coil = data["coil_geometry"]
    resonant = data["resonant_network"]
    dc = data["dc_side"]
    return SquareSpiralSpec(
        outer_side_m=float(coil["outer_side_m"]),
        inner_side_m=float(coil["inner_side_m"]),
        turns=int(coil["turns"]),
        air_gap_m=float(coil["air_gap_m"]),
        frequency_hz=float(resonant["frequency_hz"]),
        coil_resistance_ohm=float(resonant["coil_resistance_ohm"]),
        dc_output_voltage_v=float(dc["dc_output_voltage_v"]),
        rated_output_power_kw=float(dc["rated_output_power_kw"]),
        rectifier_fha_factor=float(dc["rectifier_fha_factor"]),
        rectifier_convention=str(dc["rectifier_convention"]),
        segments_per_side=int(coil["segments_per_side"]),
    )


def _square_segments(side_m: float, samples_per_side: int) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    half_side = side_m / 2.0
    corners = np.array(
        [[-half_side, -half_side, 0.0], [half_side, -half_side, 0.0],
         [half_side, half_side, 0.0], [-half_side, half_side, 0.0]], dtype=float,
    )
    fractions = (np.arange(samples_per_side, dtype=float) + 0.5) / samples_per_side
    midpoints: list[NDArray[np.float64]] = []
    differentials: list[NDArray[np.float64]] = []
    for index in range(4):
        start, end = corners[index], corners[(index + 1) % 4]
        edge = end - start
        midpoints.append(start + fractions[:, None] * edge)
        differentials.append(np.repeat((edge / samples_per_side)[None, :], samples_per_side, axis=0))
    return np.concatenate(midpoints), np.concatenate(differentials)


class SquareSpiralWptModel:
    def __init__(self, spec: SquareSpiralSpec) -> None:
        self.spec = spec
        self._midpoints, self._differentials = self._coil_segments()

    @property
    def self_inductance_h(self) -> float:
        fill_ratio = (self.spec.outer_side_m - self.spec.inner_side_m) / (self.spec.outer_side_m + self.spec.inner_side_m)
        average_diameter = (self.spec.outer_side_m + self.spec.inner_side_m) / 2.0
        return MU_0 * self.spec.turns**2 * average_diameter * MOHAN_SQUARE_C1 * (
            np.log(MOHAN_SQUARE_C2 / fill_ratio) + MOHAN_SQUARE_C3 * fill_ratio + MOHAN_SQUARE_C4 * fill_ratio**2
        ) / 2.0

    @property
    def angular_frequency_rad_s(self) -> float:
        return 2.0 * np.pi * self.spec.frequency_hz

    @property
    def resonance_capacitance_f(self) -> float:
        return 1.0 / (self.angular_frequency_rad_s**2 * self.self_inductance_h)

    @property
    def quality_factor(self) -> float:
        return self.angular_frequency_rad_s * self.self_inductance_h / self.spec.coil_resistance_ohm

    def fha_load_resistance_ohm(self, output_power_kw: float) -> float:
        """Return R_L,FHA for the configured DC bus and rectifier convention."""
        output_power_w = float(output_power_kw) * 1_000.0
        if output_power_w <= 0.0:
            raise ValueError("output_power_kw must be positive")
        return self.spec.rectifier_fha_factor * self.spec.dc_output_voltage_v**2 / output_power_w

    def _coil_segments(self) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        sides = np.linspace(self.spec.outer_side_m, self.spec.inner_side_m, self.spec.turns)
        segments = [_square_segments(float(side), self.spec.segments_per_side) for side in sides]
        return np.concatenate([segment[0] for segment in segments]), np.concatenate([segment[1] for segment in segments])

    def mutual_inductance_h(self, misalignment_mm: float) -> float:
        receiver_midpoints = self._midpoints.copy()
        receiver_midpoints[:, 0] += misalignment_mm / 1_000.0
        receiver_midpoints[:, 2] += self.spec.air_gap_m
        displacement = receiver_midpoints[None, :, :] - self._midpoints[:, None, :]
        distance = np.linalg.norm(displacement, axis=2)
        return float(MU_0 / (4.0 * np.pi) * np.sum((self._differentials @ self._differentials.T) / distance))

    def efficiency_curve(self, misalignment_mm: NDArray[np.float64], output_power_kw: float | None = None) -> EfficiencyCurve:
        power_kw = self.spec.rated_output_power_kw if output_power_kw is None else float(output_power_kw)
        load_resistance = self.fha_load_resistance_ohm(power_kw)
        mutual_inductance = np.array([self.mutual_inductance_h(float(offset)) for offset in misalignment_mm])
        coupling = mutual_inductance / self.self_inductance_h
        mutual_reactance = self.angular_frequency_rad_s * mutual_inductance
        secondary_total_resistance = self.spec.coil_resistance_ohm + load_resistance
        numerator = mutual_reactance**2 * load_resistance
        denominator = self.spec.coil_resistance_ohm * secondary_total_resistance**2 + mutual_reactance**2 * secondary_total_resistance
        return EfficiencyCurve(np.asarray(misalignment_mm, dtype=float), power_kw, load_resistance, mutual_inductance, coupling, numerator / denominator)


def default_square_spiral_model() -> SquareSpiralWptModel:
    return SquareSpiralWptModel(load_square_spiral_spec())
