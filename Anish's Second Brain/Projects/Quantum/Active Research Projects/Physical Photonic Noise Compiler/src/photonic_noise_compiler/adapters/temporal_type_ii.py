"""Idea 2 temporal-event adapter for rotated type-II fusion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..schema import CompiledChannel, OutcomeBranch


@dataclass(frozen=True)
class ScalarTemporalTable:
    accepted_correct: float
    accepted_wrong: float
    rejected: float
    loss: float

    def __post_init__(self) -> None:
        values = (
            self.accepted_correct,
            self.accepted_wrong,
            self.rejected,
            self.loss,
        )
        if any(value < 0.0 or value > 1.0 for value in values):
            raise ValueError("temporal event probabilities must lie in [0, 1]")
        if abs(sum(values) - 1.0) > 1e-10:
            raise ValueError("temporal event probabilities must sum to 1")

    @classmethod
    def from_idea2_row(cls, row: dict[str, Any]) -> "ScalarTemporalTable":
        return cls(
            accepted_correct=float(row["correct"]),
            accepted_wrong=float(row["accepted_wrong"]),
            rejected=float(row["erasure_full_rejected"]),
            loss=float(row["erasure_full_loss"]),
        )


def compile_temporal_type_ii(
    table: ScalarTemporalTable,
    *,
    name: str,
    parameters: dict[str, Any],
    source_provenance: tuple[str, ...],
) -> CompiledChannel:
    """Compile time-filtered distinguishability into type-II outcomes."""
    branches = (
        OutcomeBranch(
            probability=table.accepted_correct,
            physical_event="accepted_correct",
        ),
        OutcomeBranch(
            probability=table.accepted_wrong,
            flips=("ZZ",),
            physical_event="accepted_wrong_detuning",
            latent_tags=("relative_temporal_phase",),
        ),
        OutcomeBranch(
            probability=table.rejected,
            erasures=("XX", "ZZ"),
            heralds=("erasure:XX", "erasure:ZZ", "temporal_rejection"),
            physical_event="temporal_rejection",
            latent_tags=("arrival_time_outside_gate",),
        ),
        OutcomeBranch(
            probability=table.loss,
            erasures=("XX", "ZZ"),
            heralds=("erasure:XX", "erasure:ZZ", "photon_loss"),
            physical_event="photon_loss",
            latent_tags=("lost_input_photon",),
        ),
    )
    return CompiledChannel(
        name=name,
        adapter="temporal_type_ii",
        adapter_version="0.1",
        primitive="rotated type-II fusion measuring XX and ZZ",
        branches=branches,
        parameters=tuple(sorted(parameters.items())),
        assumptions=(
            "hard symmetric gate on measured relative arrival time",
            "rejection and input-photon loss erase both fusion outcomes",
            "wrong accepted detuning event flips ZZ only",
        ),
        correlations=(
            "XX and ZZ erasures are perfectly correlated within rejection and loss events",
            "accepted detuning faults are ZZ-biased",
        ),
        source_provenance=source_provenance,
    )
