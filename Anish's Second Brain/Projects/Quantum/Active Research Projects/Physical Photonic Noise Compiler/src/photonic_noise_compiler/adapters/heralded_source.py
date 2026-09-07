"""Heralded biphoton-source adapter with hidden vacuum and multiphoton events."""

from __future__ import annotations

from dataclasses import dataclass
from math import comb, fsum
from typing import Any

from ..schema import CompiledChannel, OutcomeBranch


@dataclass(frozen=True)
class HeraldedSourceParameters:
    """Parameters for a TMSV source conditioned on one idler PNR count.

    ``pair_probability`` is |lambda|^2. ``idler_efficiency`` combines idler
    transmission and detector efficiency, matching eta_id in Randles et al.
    """

    pair_probability: float
    signal_efficiency: float
    idler_efficiency: float

    def __post_init__(self) -> None:
        if not 0.0 < self.pair_probability < 1.0:
            raise ValueError("pair_probability must lie strictly between 0 and 1")
        for name in ("signal_efficiency", "idler_efficiency"):
            if not 0.0 <= getattr(self, name) <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")
        if self.idler_efficiency == 0.0:
            raise ValueError("a one-count herald is impossible at zero idler efficiency")


def one_count_herald_probability(parameters: HeraldedSourceParameters) -> float:
    """Published exact probability of registering one idler photon."""
    mu = parameters.pair_probability
    eta_id = parameters.idler_efficiency
    xi = mu * (1.0 - eta_id)
    return eta_id * (1.0 - mu) * mu / (1.0 - xi) ** 2


def conditional_signal_probability(
    n: int, parameters: HeraldedSourceParameters
) -> float:
    """Published exact P(signal has n photons | one idler PNR count)."""
    if n < 0:
        raise ValueError("n must be nonnegative")
    mu = parameters.pair_probability
    eta_s = parameters.signal_efficiency
    gamma_s = 1.0 - eta_s
    xi = mu * (1.0 - parameters.idler_efficiency)
    if xi == 0.0:
        # Perfect idler detection makes the one-count event select exactly one pair.
        return gamma_s if n == 0 else eta_s if n == 1 else 0.0
    numerator = (1.0 - xi) ** 2 * (n + gamma_s * xi) * (eta_s * xi) ** n
    denominator = xi * (1.0 - gamma_s * xi) ** (n + 2)
    return numerator / denominator


def conditional_pair_signal_probability(
    generated_pairs: int,
    surviving_signal_photons: int,
    parameters: HeraldedSourceParameters,
) -> float:
    """P(pair number k, surviving signal n | one idler PNR count)."""
    k = generated_pairs
    n = surviving_signal_photons
    if k < 1 or n < 0 or n > k:
        return 0.0
    mu = parameters.pair_probability
    eta_s = parameters.signal_efficiency
    eta_id = parameters.idler_efficiency
    pair_probability = (1.0 - mu) * mu**k
    idler_one = k * eta_id * (1.0 - eta_id) ** (k - 1)
    signal_n = comb(k, n) * eta_s**n * (1.0 - eta_s) ** (k - n)
    return pair_probability * idler_one * signal_n / one_count_herald_probability(
        parameters
    )


def compile_heralded_source(
    parameters: HeraldedSourceParameters,
    *,
    name: str,
    photon_cutoff: int = 8,
    extra_parameters: dict[str, Any] | None = None,
) -> CompiledChannel:
    """Compile the conditional signal state after a valid one-count herald.

    Vacuum is an unheralded physical erasure; n>=2 is non-computational
    photon-number leakage. Every branch has the same detector-visible source
    herald, so the decoder cannot distinguish these histories.
    """
    if photon_cutoff < 2:
        raise ValueError("photon_cutoff must be at least 2")
    probabilities = [
        conditional_signal_probability(n, parameters)
        for n in range(photon_cutoff + 1)
    ]
    tail = max(0.0, 1.0 - fsum(probabilities))
    branches: list[OutcomeBranch] = []
    for n, probability in enumerate(probabilities):
        if probability == 0.0:
            continue
        branches.append(
            OutcomeBranch(
                probability=probability,
                erasures=("source_signal",) if n == 0 else (),
                leakages=("source_signal",) if n >= 2 else (),
                heralds=("source_idler_one_count",),
                physical_event=f"signal_{n}_photons_given_one_idler_count",
                latent_tags=(f"hidden_signal_photon_number:{n}",),
            )
        )
    if tail > 0.0:
        branches.append(
            OutcomeBranch(
                probability=tail,
                leakages=("source_signal",),
                heralds=("source_idler_one_count",),
                physical_event=f"signal_more_than_{photon_cutoff}_photons",
                latent_tags=("hidden_signal_photon_number:cutoff_tail",),
            )
        )
    metadata = {
        "pair_probability": parameters.pair_probability,
        "signal_efficiency": parameters.signal_efficiency,
        "idler_efficiency": parameters.idler_efficiency,
        "photon_cutoff": photon_cutoff,
        "one_count_herald_probability": one_count_herald_probability(parameters),
        **(extra_parameters or {}),
    }
    return CompiledChannel(
        name=name,
        adapter="heralded_biphoton_source",
        adapter_version="0.1",
        primitive="TMSV biphoton source conditioned on one idler PNR count",
        branches=tuple(branches),
        parameters=tuple(sorted(metadata.items())),
        assumptions=(
            "two-mode squeezed-vacuum pair-number distribution",
            "independent signal and idler amplitude damping",
            "one-count photon-number-resolving idler detection",
            "negligible dark counts",
            "single spectral mode and no partial distinguishability",
        ),
        correlations=(
            "one visible source herald aliases correct, vacuum, and multiphoton signal histories",
        ),
        source_provenance=(
            "Randles, Munoz-Arias, and Sarovar, arXiv:2608.01549v1, Eqs. 12-14",
        ),
    )
