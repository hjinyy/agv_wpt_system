from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import numpy as np
from numpy.typing import NDArray


MU_0: Final = 4.0e-7 * np.pi
MOHAN_SQUARE_C1: Final = 1.27
MOHAN_SQUARE_C2: Final = 2.07
MOHAN_SQUARE_C3: Final = 0.18
MOHAN_SQUARE_C4: Final = 0.13


@dataclass(frozen=True, slots=True)
class SquareSpiralSpec:
    outer_side_m: float = 0.300
    inner_side_m: float = 0.100
    turns: int = 15
    air_gap_m: float = 0.040
    frequency_hz: float = 85_000.0
    coil_resistance_ohm: float = 0.15
    load_resistance_ohm: float = 0.623
    rated_power_kw: float = 3.0
    segments_per_side: int = 16


@dataclass(frozen=True, slots=True)
class EfficiencyCurve:
    misalignment_mm: NDArray[np.float64]
    mutual_inductance_h: NDArray[np.float64]
    coupling: NDArray[np.float64]
    efficiency: NDArray[np.float64]


def _square_segments(side_m: float, samples_per_side: int) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    half_side = side_m / 2.0
    corners = np.array(
        [
            [-half_side, -half_side, 0.0],
            [half_side, -half_side, 0.0],
            [half_side, half_side, 0.0],
            [-half_side, half_side, 0.0],
        ],
        dtype=float,
    )
    fractions = (np.arange(samples_per_side, dtype=float) + 0.5) / samples_per_side
    midpoints: list[NDArray[np.float64]] = []
    differentials: list[NDArray[np.float64]] = []
    for index in range(4):
        start = corners[index]
        end = corners[(index + 1) % 4]
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
        fill_ratio = (self.spec.outer_side_m - self.spec.inner_side_m) / (
            self.spec.outer_side_m + self.spec.inner_side_m
        )
        average_diameter = (self.spec.outer_side_m + self.spec.inner_side_m) / 2.0
        logarithmic_term = np.log(MOHAN_SQUARE_C2 / fill_ratio)
        polynomial_term = MOHAN_SQUARE_C3 * fill_ratio + MOHAN_SQUARE_C4 * fill_ratio**2
        return (
            MU_0
            * self.spec.turns**2
            * average_diameter
            * MOHAN_SQUARE_C1
            * (logarithmic_term + polynomial_term)
            / 2.0
        )

    @property
    def resonance_capacitance_f(self) -> float:
        angular_frequency = 2.0 * np.pi * self.spec.frequency_hz
        return 1.0 / (angular_frequency**2 * self.self_inductance_h)

    @property
    def quality_factor(self) -> float:
        angular_frequency = 2.0 * np.pi * self.spec.frequency_hz
        return angular_frequency * self.self_inductance_h / self.spec.coil_resistance_ohm

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
        dot_product = self._differentials @ self._differentials.T
        return float(MU_0 / (4.0 * np.pi) * np.sum(dot_product / distance))

    def efficiency_curve(self, misalignment_mm: NDArray[np.float64]) -> EfficiencyCurve:
        mutual_inductance = np.array([self.mutual_inductance_h(float(offset)) for offset in misalignment_mm])
        self_inductance = self.self_inductance_h
        coupling = mutual_inductance / self_inductance
        angular_frequency = 2.0 * np.pi * self.spec.frequency_hz
        mutual_reactance = angular_frequency * mutual_inductance
        secondary_total_resistance = self.spec.coil_resistance_ohm + self.spec.load_resistance_ohm
        numerator = mutual_reactance**2 * self.spec.load_resistance_ohm
        denominator = (
            self.spec.coil_resistance_ohm * secondary_total_resistance**2
            + mutual_reactance**2 * secondary_total_resistance
        )
        return EfficiencyCurve(misalignment_mm, mutual_inductance, coupling, numerator / denominator)


def default_square_spiral_model() -> SquareSpiralWptModel:
    return SquareSpiralWptModel(SquareSpiralSpec())
