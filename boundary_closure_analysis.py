from __future__ import annotations

from parameter_refinement_analysis import (
    Aggregate,
    C4Parameters,
    C5Parameters,
    PairedStatistics,
    c4_parameters,
    is_safe,
)


def c4_lower_boundary_parameters() -> list[C4Parameters]:
    return [c4_parameters(0.55, w5) for w5 in (0.00, 0.05, 0.10, 0.15)]


def c5_lower_boundary_parameters() -> list[C5Parameters]:
    return [
        C5Parameters(2.0, 1.0, 1.5),
        C5Parameters(2.0, 1.25, 1.5),
        C5Parameters(2.0, 1.5, 1.5),
        C5Parameters(2.0, 1.5, 1.25),
        C5Parameters(2.0, 1.5, 1.0),
    ]


def _intervals_support_improvement(comparisons: list[PairedStatistics]) -> bool:
    by_metric = {comparison.metric: comparison for comparison in comparisons}
    return by_metric["mean_delay"].ci95_high < 0.0 and by_metric["urgent_on_time_rate"].ci95_low > 0.0


def choose_boundary_candidate(
    baseline: Aggregate,
    results: list[Aggregate],
    comparisons: dict[C4Parameters | C5Parameters, list[PairedStatistics]],
) -> Aggregate:
    supported = [
        candidate
        for candidate in results
        if candidate.parameters != baseline.parameters
        and is_safe(candidate)
        and candidate.mean_delay < baseline.mean_delay
        and candidate.urgent_on_time_rate > baseline.urgent_on_time_rate
        and _intervals_support_improvement(comparisons.get(candidate.parameters, []))
    ]
    return min(supported, key=lambda candidate: (candidate.mean_delay, -candidate.urgent_on_time_rate)) if supported else baseline
