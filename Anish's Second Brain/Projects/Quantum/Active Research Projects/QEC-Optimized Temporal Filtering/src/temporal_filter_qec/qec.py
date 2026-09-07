"""Compilation into a decoder-honest Stim/PyMatching benchmark."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt

import numpy as np
import pymatching
import stim

from .physics import EventTable


@dataclass(frozen=True)
class LogicalEstimate:
    distance: int
    rounds: int
    shots: int
    failures: int
    logical_error_rate: float
    ci_low: float
    ci_high: float
    p_erasure: float
    p_accepted_error: float
    heralded_decoder: bool
    missed_erasure_fraction: float
    seed: int

    def to_dict(self) -> dict[str, float | int | bool]:
        return asdict(self)


def wilson_interval(failures: int, shots: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if shots <= 0 or not 0 <= failures <= shots:
        raise ValueError("invalid binomial counts")
    p = failures / shots
    denominator = 1.0 + z * z / shots
    center = (p + z * z / (2.0 * shots)) / denominator
    radius = z * sqrt((p * (1.0 - p) + z * z / (4.0 * shots)) / shots) / denominator
    return max(0.0, center - radius), min(1.0, center + radius)


def _data_qubits(circuit: stim.Circuit) -> list[int]:
    data: list[int] = []
    for instruction in circuit.flattened():
        if instruction.name == "M":
            data = [int(t.value) for t in instruction.targets_copy() if t.is_qubit_target]
    if not data:
        raise RuntimeError("could not identify final data-qubit measurement")
    return data


def build_surface_code_memory(
    distance: int,
    rounds: int,
    p_erasure: float,
    p_accepted_error: float,
    *,
    heralded_decoder: bool = True,
    missed_erasure_fraction: float = 0.0,
) -> stim.Circuit:
    """Build a code-capacity memory with one categorical fault opportunity.

    The heralded erasure branch is maximally mixed. Conditional on no erasure,
    X_ERROR has probability p_accepted_error/(1-p_erasure). Applying the X
    channel after a maximally mixed erasure does not change that branch, so the
    marginal channel exactly matches the event table.
    """
    if distance < 3 or distance % 2 == 0:
        raise ValueError("distance must be an odd integer >= 3")
    if rounds < 1:
        raise ValueError("rounds must be positive")
    if p_erasure < 0 or p_accepted_error < 0 or p_erasure + p_accepted_error > 1 + 1e-12:
        raise ValueError("invalid categorical channel probabilities")
    if not 0 <= missed_erasure_fraction <= 1:
        raise ValueError("missed_erasure_fraction must lie in [0, 1]")

    base = stim.Circuit.generated("surface_code:rotated_memory_z", distance=distance, rounds=rounds)
    data = _data_qubits(base)
    result = stim.Circuit()
    inserted = False
    for instruction in base:
        result.append(instruction)
        if not inserted and instruction.name == "TICK":
            flagged_erasure = p_erasure * (1.0 - missed_erasure_fraction)
            if flagged_erasure > 0:
                result.append("HERALDED_ERASE", data, flagged_erasure)
                if heralded_decoder:
                    n = len(data)
                    for index in range(n):
                        result.append("DETECTOR", [stim.target_rec(-(n - index))])
            # A missed erasure is an unflagged maximally mixed qubit. Given no
            # flagged erasure, its conditional probability is adjusted so the
            # total physical erasure probability remains exactly p_erasure.
            missed_erasure = p_erasure * missed_erasure_fraction
            conditional_missed = (
                missed_erasure / (1.0 - flagged_erasure)
                if flagged_erasure < 1.0
                else 0.0
            )
            if conditional_missed > 0:
                # DEPOLARIZE1(3q/4) equals (1-q)I + q(I+X+Y+Z)/4.
                result.append("DEPOLARIZE1", data, 0.75 * conditional_missed)
            conditional_error = p_accepted_error / (1.0 - p_erasure) if p_erasure < 1.0 else 0.0
            if conditional_error > 0:
                result.append("X_ERROR", data, conditional_error)
            inserted = True
    if not inserted:
        raise RuntimeError("failed to locate insertion tick")
    return result


def simulate_logical_error(
    table: EventTable,
    distance: int,
    rounds: int,
    shots: int,
    seed: int,
    *,
    heralded_decoder: bool = True,
    missed_erasure_fraction: float = 0.0,
) -> LogicalEstimate:
    if shots <= 0:
        raise ValueError("shots must be positive")
    circuit = build_surface_code_memory(
        distance,
        rounds,
        table.erasure,
        table.accepted_wrong,
        heralded_decoder=heralded_decoder,
        missed_erasure_fraction=missed_erasure_fraction,
    )
    dem = circuit.detector_error_model(decompose_errors=True, approximate_disjoint_errors=True)
    # The herald detector and its possible Pauli consequences form a
    # decomposable correlated error. Two-pass correlated matching is required
    # for PyMatching to condition its edge weights on the observed flag.
    matching = pymatching.Matching.from_detector_error_model(
        dem, enable_correlations=heralded_decoder
    )
    detectors, observables = circuit.compile_detector_sampler(seed=seed).sample(
        shots, separate_observables=True
    )
    predictions = matching.decode_batch(
        detectors, enable_correlations=heralded_decoder
    )
    failures = int(np.count_nonzero(np.any(predictions != observables, axis=1)))
    low, high = wilson_interval(failures, shots)
    return LogicalEstimate(
        distance=distance,
        rounds=rounds,
        shots=shots,
        failures=failures,
        logical_error_rate=failures / shots,
        ci_low=low,
        ci_high=high,
        p_erasure=table.erasure,
        p_accepted_error=table.accepted_wrong,
        heralded_decoder=heralded_decoder,
        missed_erasure_fraction=missed_erasure_fraction,
        seed=seed,
    )
