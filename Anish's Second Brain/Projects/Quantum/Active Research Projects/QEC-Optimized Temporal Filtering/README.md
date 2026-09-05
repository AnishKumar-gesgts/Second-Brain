# QEC-Optimized Temporal Filtering

Idea 2 optimizes a temporal gate/filter by decoded logical error rather than a raw optical metric.

## First study

Model one two-photon interference or fusion primitive in Strawberry Fields with temporal mismatch and gate width \(\tau\). For each point, calculate accepted-correct, accepted-wrong, rejected, and loss probabilities; compile them into a fixed Stim/PyMatching experiment; and report acceptance, heralded erasure, unheralded accepted error, \(P_L\), and uncertainty.

The interface must return a portable decoder-visible event table, not write directly into a one-off circuit. That contract becomes the first adapter for Idea 3.

## Required gates

1. Probability conservation and ideal-limit tests.
2. Fock-cutoff and temporal-discretization convergence.
3. Decoder-visible event classification.
4. Optical-to-compiled event-distribution agreement.
5. Frozen held-out QEC evaluation with uncertainty.

This workspace is planning-only until implementation is requested.
