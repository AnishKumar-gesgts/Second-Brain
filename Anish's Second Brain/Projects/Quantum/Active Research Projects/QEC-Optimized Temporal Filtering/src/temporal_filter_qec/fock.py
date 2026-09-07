"""Finite-Fock-space validation using Strawberry Fields."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FockValidation:
    cutoff: int
    p_20: float
    p_11: float
    p_02: float
    probability_sum: float


def balanced_beamsplitter_validation(cutoff: int) -> FockValidation:
    """Propagate |1,1> through a 50:50 beamsplitter with a Fock backend."""
    if cutoff < 3:
        raise ValueError("cutoff must be >= 3 to represent two photons in one mode")
    import strawberryfields as sf
    from strawberryfields import ops

    program = sf.Program(2)
    with program.context as q:
        ops.Fock(1) | q[0]
        ops.Fock(1) | q[1]
        ops.BSgate(np.pi / 4.0, 0.0) | (q[0], q[1])
    state = sf.Engine("fock", backend_options={"cutoff_dim": cutoff}).run(program).state
    probs = state.all_fock_probs()
    return FockValidation(
        cutoff=cutoff,
        p_20=float(probs[2, 0]),
        p_11=float(probs[1, 1]),
        p_02=float(probs[0, 2]),
        probability_sum=float(np.sum(probs)),
    )
