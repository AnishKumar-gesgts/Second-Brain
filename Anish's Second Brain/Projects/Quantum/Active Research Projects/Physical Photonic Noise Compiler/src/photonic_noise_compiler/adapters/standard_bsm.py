"""Exact small-Fock-space model of a standard dual-rail Bell measurement."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from itertools import product
from math import comb, factorial, sqrt

import numpy as np

from ..schema import CompiledChannel, OutcomeBranch
from .heralded_source import (
    HeraldedSourceParameters,
    conditional_signal_probability,
)


_BELL_VECTORS = {
    "phi_plus": np.array([1, 0, 0, 1], dtype=complex) / sqrt(2),
    "phi_minus": np.array([1, 0, 0, -1], dtype=complex) / sqrt(2),
    "psi_plus": np.array([0, 1, 1, 0], dtype=complex) / sqrt(2),
    "psi_minus": np.array([0, 1, -1, 0], dtype=complex) / sqrt(2),
}
_BELL_EIGENVALUES = {
    "phi_plus": (1, 1),
    "phi_minus": (-1, 1),
    "psi_plus": (1, -1),
    "psi_minus": (-1, -1),
}


@dataclass(frozen=True)
class BSMResult:
    channel: CompiledChannel
    probability_full_success: float
    probability_partial_failure: float
    probability_count_rejection: float
    full_success_hidden_error_probability: float
    accepted_error_given_full_success: float
    partial_retained_parity_error_probability: float
    max_full_bell_coherence: float


def _two_mode_bs_amplitudes(n_a: int, n_b: int) -> dict[tuple[int, int], complex]:
    """Balanced BS amplitudes for |n_a,n_b> -> |k,n_a+n_b-k>."""
    total = n_a + n_b
    amplitudes: dict[tuple[int, int], complex] = {}
    for k in range(total + 1):
        polynomial = 0
        for p in range(max(0, k - n_b), min(n_a, k) + 1):
            q = k - p
            polynomial += comb(n_a, p) * comb(n_b, q) * (-1) ** (n_b - q)
        amplitude = (
            polynomial
            * sqrt(factorial(k) * factorial(total - k) / (factorial(n_a) * factorial(n_b)))
            / (2 ** (total / 2))
        )
        if abs(amplitude) > 1e-15:
            amplitudes[(k, total - k)] = complex(amplitude)
    return amplitudes


def _four_mode_output_amplitudes(
    occupation: tuple[int, int, int, int]
) -> dict[tuple[int, int, int, int], complex]:
    """Apply identical spatial beam splitters to H and V polarization modes."""
    a_h, a_v, b_h, b_v = occupation
    h_outputs = _two_mode_bs_amplitudes(a_h, b_h)
    v_outputs = _two_mode_bs_amplitudes(a_v, b_v)
    result: dict[tuple[int, int, int, int], complex] = {}
    for (c_h, d_h), h_amplitude in h_outputs.items():
        for (c_v, d_v), v_amplitude in v_outputs.items():
            result[(c_h, c_v, d_h, d_v)] = h_amplitude * v_amplitude
    return result


def _detection_amplitude(
    output: tuple[int, ...],
    record: tuple[int, ...],
    efficiency: float,
) -> float:
    if any(observed > present for observed, present in zip(record, output, strict=True)):
        return 0.0
    probability = 1.0
    for present, observed in zip(output, record, strict=True):
        probability *= (
            comb(present, observed)
            * efficiency**observed
            * (1.0 - efficiency) ** (present - observed)
        )
    return sqrt(probability)


def remote_density_for_record(
    photons_a: int,
    photons_b: int,
    detector_efficiency: float,
    record: tuple[int, int, int, int],
) -> np.ndarray:
    """Unnormalized remote-qubit state for one source-number pair and click record.

    Each measured photon is one half of (|0,H> + |1,V>)/sqrt(2). Lost
    output photons are traced by summing incoherently over their number pattern.
    """
    environment_vectors: dict[tuple[int, ...], np.ndarray] = defaultdict(
        lambda: np.zeros(4, dtype=complex)
    )
    for remote_a, remote_b in product((0, 1), repeat=2):
        occupation = (
            photons_a if remote_a == 0 else 0,
            photons_a if remote_a == 1 else 0,
            photons_b if remote_b == 0 else 0,
            photons_b if remote_b == 1 else 0,
        )
        for output, optical_amplitude in _four_mode_output_amplitudes(occupation).items():
            detection_amplitude = _detection_amplitude(
                output, record, detector_efficiency
            )
            if detection_amplitude == 0.0:
                continue
            lost = tuple(
                present - observed
                for present, observed in zip(output, record, strict=True)
            )
            environment_vectors[lost][2 * remote_a + remote_b] += (
                0.5 * optical_amplitude * detection_amplitude
            )
    return sum(
        (np.outer(vector, vector.conj()) for vector in environment_vectors.values()),
        start=np.zeros((4, 4), dtype=complex),
    )


def _two_photon_records() -> tuple[tuple[int, int, int, int], ...]:
    records = []
    for a in range(3):
        for b in range(3 - a):
            for c in range(3 - a - b):
                d = 2 - a - b - c
                records.append((a, b, c, d))
    return tuple(records)


def _bell_populations(density: np.ndarray) -> dict[str, float]:
    return {
        label: float(np.real(vector.conj() @ density @ vector))
        for label, vector in _BELL_VECTORS.items()
    }


def _max_bell_coherence(density: np.ndarray) -> float:
    matrix = np.array(
        [
            [left.conj() @ density @ right for right in _BELL_VECTORS.values()]
            for left in _BELL_VECTORS.values()
        ]
    )
    matrix -= np.diag(np.diag(matrix))
    return float(np.max(np.abs(matrix)))


def compile_standard_bsm(
    source: HeraldedSourceParameters,
    *,
    detector_efficiency: float,
    name: str,
    photon_cutoff: int = 10,
) -> BSMResult:
    """Compile an unboosted dual-rail BSM into XX/ZZ outcomes."""
    if not 0.0 <= detector_efficiency <= 1.0:
        raise ValueError("detector_efficiency must lie in [0, 1]")
    source_probabilities = [
        conditional_signal_probability(n, source)
        for n in range(photon_cutoff + 1)
    ]
    source_probabilities[-1] += max(0.0, 1.0 - sum(source_probabilities))

    records = _two_photon_records()
    ideal_states: dict[tuple[int, ...], np.ndarray] = {}
    for record in records:
        ideal = remote_density_for_record(1, 1, 1.0, record)
        if np.trace(ideal).real > 1e-14:
            ideal_states[record] = ideal

    aggregated: dict[tuple[int, ...], np.ndarray] = {
        record: np.zeros((4, 4), dtype=complex) for record in records
    }
    for n_a, probability_a in enumerate(source_probabilities):
        for n_b, probability_b in enumerate(source_probabilities):
            weight = probability_a * probability_b
            if weight == 0.0:
                continue
            for record in records:
                aggregated[record] += weight * remote_density_for_record(
                    n_a, n_b, detector_efficiency, record
                )

    branch_probabilities: dict[
        tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], str], float
    ] = defaultdict(float)
    probability_full = 0.0
    probability_partial = 0.0
    full_hidden_error = 0.0
    partial_parity_error = 0.0
    max_full_coherence = 0.0

    for record, density in aggregated.items():
        record_probability = float(np.trace(density).real)
        if record_probability <= 1e-15:
            continue
        populations = _bell_populations(density)
        h_count = record[0] + record[2]
        v_count = record[1] + record[3]
        if record in ideal_states and h_count == 1 and v_count == 1:
            probability_full += record_probability
            max_full_coherence = max(
                max_full_coherence, _max_bell_coherence(density)
            )
            ideal_populations = _bell_populations(ideal_states[record])
            reported = max(ideal_populations, key=ideal_populations.get)
            reported_xx, reported_zz = _BELL_EIGENVALUES[reported]
            for actual, probability in populations.items():
                actual_xx, actual_zz = _BELL_EIGENVALUES[actual]
                flips = tuple(
                    target
                    for target, differs in (
                        ("XX", actual_xx != reported_xx),
                        ("ZZ", actual_zz != reported_zz),
                    )
                    if differs
                )
                if flips:
                    full_hidden_error += probability
                branch_probabilities[
                    (flips, (), ("bsm_two_count_full",), "full_bsm_record")
                ] += probability
        elif record in ideal_states:
            probability_partial += record_probability
            # Same-polarization two-count records reveal ZZ=+1 but not XX.
            for actual, probability in populations.items():
                _, actual_zz = _BELL_EIGENVALUES[actual]
                flips = ("ZZ",) if actual_zz != 1 else ()
                if flips:
                    partial_parity_error += probability
                branch_probabilities[
                    (
                        flips,
                        ("XX",),
                        ("bsm_two_count_partial", "erasure:XX"),
                        "partial_bsm_record",
                    )
                ] += probability

    probability_two_count = probability_full + probability_partial
    probability_rejection = max(0.0, 1.0 - probability_two_count)
    branch_probabilities[
        (
            (),
            ("XX", "ZZ"),
            ("bsm_count_rejection", "erasure:XX", "erasure:ZZ"),
            "detected_total_not_two",
        )
    ] += probability_rejection

    branches = tuple(
        OutcomeBranch(
            probability=probability,
            flips=flips,
            erasures=erasures,
            heralds=heralds,
            physical_event=event,
            latent_tags=("hidden_source_number_history",) if flips else (),
        )
        for (flips, erasures, heralds, event), probability in branch_probabilities.items()
        if probability > 1e-15
    )
    channel = CompiledChannel(
        name=name,
        adapter="standard_dual_rail_bsm",
        adapter_version="0.1",
        primitive="balanced spatial beamsplitter plus four-mode PNR detection",
        branches=branches,
        parameters=tuple(
            sorted(
                {
                    "pair_probability": source.pair_probability,
                    "signal_efficiency": source.signal_efficiency,
                    "idler_efficiency": source.idler_efficiency,
                    "fusion_detector_efficiency": detector_efficiency,
                    "photon_cutoff": photon_cutoff,
                }.items()
            )
        ),
        assumptions=(
            "each fusion photon is half of an ideal remote-photon Bell pair",
            "multiphoton contamination occupies the encoded rail coherently",
            "identical independent source-number distributions",
            "balanced polarization-preserving beamsplitter",
            "photon-number-resolving detectors with independent loss and no dark counts",
        ),
        correlations=(
            "full BSM outcome-bit errors may be correlated",
            "wrong total photon count jointly erases XX and ZZ",
            "same-polarization two-count failure erases XX while retaining ZZ",
        ),
        source_provenance=(
            "Randles, Munoz-Arias, and Sarovar, arXiv:2608.01549v1, Eqs. 12-14",
            "Hauser et al., npj Quantum Information 11, 41 (2025), standard BSM Eqs. 1-2",
        ),
    )
    conditional_error = (
        full_hidden_error / probability_full if probability_full else 0.0
    )
    return BSMResult(
        channel=channel,
        probability_full_success=probability_full,
        probability_partial_failure=probability_partial,
        probability_count_rejection=probability_rejection,
        full_success_hidden_error_probability=full_hidden_error,
        accepted_error_given_full_success=conditional_error,
        partial_retained_parity_error_probability=partial_parity_error,
        max_full_bell_coherence=max_full_coherence,
    )
