"""Two-photon temporal-mode model.

The relative true arrival time D is Gaussian. Detector jitter adds independent
Gaussian noise to produce the observed difference Y. A hard temporal gate keeps
events with |Y| <= tau. For a frequency mismatch dw, the unresolved relative
phase gives a conditional parity-error probability (1-cos(dw*D))/2.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import exp, pi, sqrt

import numpy as np
from scipy.special import ndtr


@dataclass(frozen=True)
class PhysicalParameters:
    wavepacket_sigma_ps: float
    detector_jitter_ps: float
    frequency_detuning_ghz: float
    detector_efficiency: float
    spectral_diffusion_ghz: float = 0.0

    def __post_init__(self) -> None:
        if self.wavepacket_sigma_ps <= 0:
            raise ValueError("wavepacket_sigma_ps must be positive")
        if self.detector_jitter_ps < 0:
            raise ValueError("detector_jitter_ps must be non-negative")
        if self.frequency_detuning_ghz < 0:
            raise ValueError("frequency_detuning_ghz must be non-negative")
        if not 0 <= self.detector_efficiency <= 1:
            raise ValueError("detector_efficiency must lie in [0, 1]")
        if self.spectral_diffusion_ghz < 0:
            raise ValueError("spectral_diffusion_ghz must be non-negative")

    @property
    def sigma_relative_s(self) -> float:
        return sqrt(2.0) * self.wavepacket_sigma_ps * 1e-12

    @property
    def jitter_relative_s(self) -> float:
        return sqrt(2.0) * self.detector_jitter_ps * 1e-12

    @property
    def angular_detuning(self) -> float:
        return 2.0 * pi * self.frequency_detuning_ghz * 1e9

    @property
    def angular_diffusion(self) -> float:
        return 2.0 * pi * self.spectral_diffusion_ghz * 1e9

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(frozen=True)
class EventTable:
    gate_width_ps: float | None
    accepted_correct: float
    accepted_wrong: float
    rejected: float
    loss: float
    conditional_accepted_error: float
    conditional_visibility: float
    grid_points: int

    @property
    def acceptance(self) -> float:
        return self.accepted_correct + self.accepted_wrong

    @property
    def erasure(self) -> float:
        return self.rejected + self.loss

    @property
    def total(self) -> float:
        return self.acceptance + self.erasure

    def validate(self, atol: float = 2e-10) -> None:
        values = (self.accepted_correct, self.accepted_wrong, self.rejected, self.loss)
        if any(x < -atol or x > 1 + atol for x in values):
            raise ValueError(f"invalid event probability: {values}")
        if abs(self.total - 1.0) > atol:
            raise ValueError(f"event probabilities sum to {self.total}, not 1")

    def to_dict(self) -> dict[str, float | int | None]:
        result = asdict(self)
        result["acceptance"] = self.acceptance
        result["erasure"] = self.erasure
        result["probability_sum"] = self.total
        return result


def _normal_pdf(x: np.ndarray, sigma: float) -> np.ndarray:
    return np.exp(-0.5 * (x / sigma) ** 2) / (sqrt(2.0 * pi) * sigma)


def event_table(
    params: PhysicalParameters,
    gate_width_ps: float | None,
    *,
    grid_points: int = 20_001,
    extent_sigma: float = 9.0,
) -> EventTable:
    """Integrate the mutually exclusive physical event probabilities."""
    if gate_width_ps is not None and gate_width_ps < 0:
        raise ValueError("gate_width_ps must be non-negative or None")
    if grid_points < 501 or grid_points % 2 == 0:
        raise ValueError("grid_points must be an odd integer >= 501")

    sigma_d = params.sigma_relative_s
    d = np.linspace(-extent_sigma * sigma_d, extent_sigma * sigma_d, grid_points)
    density = _normal_pdf(d, sigma_d)
    if gate_width_ps is None:
        gate_probability = np.ones_like(d)
    else:
        tau = gate_width_ps * 1e-12
        sigma_n = params.jitter_relative_s
        if sigma_n == 0:
            gate_probability = (np.abs(d) <= tau).astype(float)
        else:
            gate_probability = ndtr((tau - d) / sigma_n) - ndtr((-tau - d) / sigma_n)

    accepted_density = density * gate_probability
    accepted_if_detected = float(np.trapezoid(accepted_density, d))
    # Average over independent shot-to-shot Gaussian spectral diffusion. This
    # damps long relative-time events even when the mean detuning is calibrated.
    coherence = np.cos(params.angular_detuning * d) * np.exp(
        -0.5 * (params.angular_diffusion * d) ** 2
    )
    coherence_if_detected = float(np.trapezoid(accepted_density * coherence, d))
    eta2 = params.detector_efficiency**2
    accepted_correct = eta2 * (accepted_if_detected + coherence_if_detected) / 2.0
    accepted_wrong = eta2 * (accepted_if_detected - coherence_if_detected) / 2.0
    rejected = eta2 * (1.0 - accepted_if_detected)
    loss = 1.0 - eta2
    accepted = accepted_correct + accepted_wrong
    table = EventTable(
        gate_width_ps=gate_width_ps,
        accepted_correct=max(0.0, accepted_correct),
        accepted_wrong=max(0.0, accepted_wrong),
        rejected=max(0.0, rejected),
        loss=max(0.0, loss),
        conditional_accepted_error=accepted_wrong / accepted if accepted > 0 else 0.0,
        conditional_visibility=coherence_if_detected / accepted_if_detected if accepted_if_detected > 0 else 1.0,
        grid_points=grid_points,
    )
    table.validate()
    return table


def analytic_unfiltered(params: PhysicalParameters) -> EventTable:
    """Closed-form limit used to validate the numerical temporal integral."""
    diffusion_factor = 1.0 + (
        params.angular_diffusion * params.sigma_relative_s
    ) ** 2
    visibility = exp(
        -0.5
        * (params.angular_detuning * params.sigma_relative_s) ** 2
        / diffusion_factor
    ) / sqrt(diffusion_factor)
    eta2 = params.detector_efficiency**2
    table = EventTable(
        gate_width_ps=None,
        accepted_correct=eta2 * (1.0 + visibility) / 2.0,
        accepted_wrong=eta2 * (1.0 - visibility) / 2.0,
        rejected=0.0,
        loss=1.0 - eta2,
        conditional_accepted_error=(1.0 - visibility) / 2.0,
        conditional_visibility=visibility,
        grid_points=0,
    )
    table.validate()
    return table


def sample_event_frequencies(
    params: PhysicalParameters,
    gate_width_ps: float | None,
    shots: int,
    seed: int,
) -> dict[str, float]:
    """Independent Monte Carlo check of the integrated event table."""
    rng = np.random.default_rng(seed)
    detected = rng.random(shots) < params.detector_efficiency**2
    d = rng.normal(0.0, params.sigma_relative_s, size=shots)
    y = d + rng.normal(0.0, params.jitter_relative_s, size=shots)
    accepted = detected if gate_width_ps is None else detected & (np.abs(y) <= gate_width_ps * 1e-12)
    shot_detuning = rng.normal(
        params.angular_detuning, params.angular_diffusion, size=shots
    )
    wrong_probability = (1.0 - np.cos(shot_detuning * d)) / 2.0
    wrong = accepted & (rng.random(shots) < wrong_probability)
    correct = accepted & ~wrong
    rejected = detected & ~accepted
    loss = ~detected
    return {
        "accepted_correct": float(np.mean(correct)),
        "accepted_wrong": float(np.mean(wrong)),
        "rejected": float(np.mean(rejected)),
        "loss": float(np.mean(loss)),
    }
