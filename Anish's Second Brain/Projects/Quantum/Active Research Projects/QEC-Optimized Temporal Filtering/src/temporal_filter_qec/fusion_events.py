"""Compile the temporal primitive into observable Bell-fusion outcomes.

The optical model currently determines whether an accepted fusion has the
wrong parity, but it does not determine which of the two commuting Bell
observables (XX and ZZ) is affected.  This module keeps that unresolved map
explicit through either a named type-II protocol map or a normalized
sensitivity split.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .physics import EventTable


@dataclass(frozen=True)
class FusionEventTable:
    """Mutually exclusive physical outcomes for one two-qubit fusion."""

    gate_width_ps: float | None
    correct: float
    wrong_xx: float
    wrong_zz: float
    wrong_xx_zz: float
    erasure_xx: float
    erasure_zz: float
    erasure_full_rejected: float
    erasure_full_loss: float
    temporal_acceptance: float
    temporal_rejection: float
    intrinsic_failure_probability: float
    wrong_xx_fraction: float
    wrong_zz_fraction: float
    wrong_xx_zz_fraction: float

    @property
    def accepted_wrong(self) -> float:
        return self.wrong_xx + self.wrong_zz + self.wrong_xx_zz

    @property
    def full_erasure(self) -> float:
        return self.erasure_full_rejected + self.erasure_full_loss

    @property
    def any_erasure(self) -> float:
        return self.erasure_xx + self.erasure_zz + self.full_erasure

    @property
    def xx_wrong_marginal(self) -> float:
        return self.wrong_xx + self.wrong_xx_zz

    @property
    def zz_wrong_marginal(self) -> float:
        return self.wrong_zz + self.wrong_xx_zz

    @property
    def xx_erasure_marginal(self) -> float:
        return self.erasure_xx + self.full_erasure

    @property
    def zz_erasure_marginal(self) -> float:
        return self.erasure_zz + self.full_erasure

    @property
    def total(self) -> float:
        return self.correct + self.accepted_wrong + self.any_erasure

    def validate(self, atol: float = 2e-10) -> None:
        probabilities = (
            self.correct,
            self.wrong_xx,
            self.wrong_zz,
            self.wrong_xx_zz,
            self.erasure_xx,
            self.erasure_zz,
            self.erasure_full_rejected,
            self.erasure_full_loss,
        )
        if any(value < -atol or value > 1 + atol for value in probabilities):
            raise ValueError(f"invalid fusion-event probability: {probabilities}")
        if abs(self.total - 1.0) > atol:
            raise ValueError(f"fusion-event probabilities sum to {self.total}, not 1")
        if abs(
            self.wrong_xx_fraction
            + self.wrong_zz_fraction
            + self.wrong_xx_zz_fraction
            - 1.0
        ) > atol:
            raise ValueError("wrong-outcome fractions must sum to 1")

    def to_dict(self) -> dict[str, float | None]:
        result = asdict(self)
        result.update(
            accepted_wrong=self.accepted_wrong,
            full_erasure=self.full_erasure,
            any_erasure=self.any_erasure,
            xx_wrong_marginal=self.xx_wrong_marginal,
            zz_wrong_marginal=self.zz_wrong_marginal,
            xx_erasure_marginal=self.xx_erasure_marginal,
            zz_erasure_marginal=self.zz_erasure_marginal,
            probability_sum=self.total,
        )
        return result


def compile_fusion_events(
    table: EventTable,
    *,
    wrong_xx_fraction: float = 0.25,
    wrong_zz_fraction: float = 0.25,
    wrong_xx_zz_fraction: float = 0.5,
    intrinsic_failure_probability: float = 0.0,
) -> FusionEventTable:
    """Lift the scalar parity table into an XX/ZZ fusion-event schema.

    ``intrinsic_failure_probability`` acts only on temporally accepted,
    detected events.  Following the randomized failure-basis convention in
    Bartolucci et al. (2023), half of these failures erase XX and half erase
    ZZ while preserving the other Bell outcome.  Rejection and photon loss
    erase both outcomes.

    The wrong-outcome split is a sensitivity parameter.  It is not inferred
    from the current two-mode Hong-Ou-Mandel calculation.
    """
    fractions = (
        wrong_xx_fraction,
        wrong_zz_fraction,
        wrong_xx_zz_fraction,
    )
    if any(value < 0 or value > 1 for value in fractions):
        raise ValueError("wrong-outcome fractions must lie in [0, 1]")
    if abs(sum(fractions) - 1.0) > 1e-12:
        raise ValueError("wrong-outcome fractions must sum to 1")
    if not 0 <= intrinsic_failure_probability <= 1:
        raise ValueError("intrinsic_failure_probability must lie in [0, 1]")

    survives_fusion = 1.0 - intrinsic_failure_probability
    failed_accepted = table.acceptance * intrinsic_failure_probability
    result = FusionEventTable(
        gate_width_ps=table.gate_width_ps,
        correct=table.accepted_correct * survives_fusion,
        wrong_xx=table.accepted_wrong * survives_fusion * wrong_xx_fraction,
        wrong_zz=table.accepted_wrong * survives_fusion * wrong_zz_fraction,
        wrong_xx_zz=table.accepted_wrong * survives_fusion * wrong_xx_zz_fraction,
        erasure_xx=failed_accepted / 2.0,
        erasure_zz=failed_accepted / 2.0,
        erasure_full_rejected=table.rejected,
        erasure_full_loss=table.loss,
        temporal_acceptance=table.acceptance,
        temporal_rejection=table.rejected,
        intrinsic_failure_probability=intrinsic_failure_probability,
        wrong_xx_fraction=wrong_xx_fraction,
        wrong_zz_fraction=wrong_zz_fraction,
        wrong_xx_zz_fraction=wrong_xx_zz_fraction,
    )
    result.validate()
    return result


def compile_type_ii_detuning_events(
    table: EventTable,
    *,
    intrinsic_failure_probability: float = 0.0,
) -> FusionEventTable:
    """Compile detuning-induced distinguishability for type-II fusion.

    For the rotated type-II fusion convention used in the six-ring proposal,
    partial photon distinguishability flips the reported ``ZZ`` outcome with
    probability ``(1 - V) / 2`` while leaving ``XX`` unchanged.  The scalar
    temporal model's ``accepted_wrong`` branch is exactly this probability
    after integrating over accepted arrival-time differences.  Temporal
    rejection and photon loss erase both outcomes.

    The mapping follows Chan et al., PRX Quantum 6, 020304 (2025), Appendix F,
    rather than treating the XX/ZZ split as a free sensitivity parameter.
    """
    return compile_fusion_events(
        table,
        wrong_xx_fraction=0.0,
        wrong_zz_fraction=1.0,
        wrong_xx_zz_fraction=0.0,
        intrinsic_failure_probability=intrinsic_failure_probability,
    )
