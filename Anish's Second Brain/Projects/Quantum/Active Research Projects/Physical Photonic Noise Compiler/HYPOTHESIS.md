# Hypothesis and Falsification Plan

## Primary hypothesis

A reusable physical-to-QEC compiler that retains decoder-visible heralds, biased faults, and within-event correlations will predict logical behavior more reliably than models that replace each photonic primitive with independent scalar error and erasure rates.

“More reliably” must be demonstrated against an exact or independently validated reference at the optical, compiled-channel, and QEC layers. It cannot be inferred from additional model complexity alone.

## Broad predictions

1. At least two physically distinct photonic mechanisms will produce joint observable-event distributions that cannot be represented faithfully by independent per-outcome error and erasure probabilities.
2. For at least one realistic regime, retaining that structure will significantly change logical error, distance scaling, a threshold estimate, or the ranking of two hardware/control policies.
3. The same channel contract and decoder-visibility rules will support every adapter without mechanism-specific changes to the compiler core.
4. Simplifying a compiled channel will produce a measurable error budget that identifies which discarded correlation or herald record caused the logical discrepancy.

## Planned adapters

1. Type-II temporal distinguishability and temporal rejection from Idea 2.
2. Multiphoton emission plus photon loss from Idea 1.
3. A third independent mechanism selected from detector dark counts, mode-dependent loss, source-number impurity, or temporally correlated loss after a literature and tractability review.

## Falsifiers

The central hypothesis loses publication promise if, after at least two faithful adapters and held-out QEC comparisons:

- matched scalar models reproduce all logical results within uncertainty;
- correlation-aware compilation changes event tables but not decisions or scaling;
- the core schema requires mechanism-specific exceptions rather than a stable interface; or
- validation cannot distinguish compiler error from optical-model or architecture error.

If evidence points toward one narrow favorable mechanism or parameter corner, pause and consult before changing the primary hypothesis.

## Current evidence boundary

Idea 2 provides one strong motivating counterexample: a simplified scalar surface-code mapping supported temporal filtering, while a protocol-specific six-ring bulk mapping did not. This establishes that the mapping choice can reverse a conclusion in one case. It does not yet establish that the new compiler is generally accurate or that correlation-preserving compilation changes architecture-level results across multiple mechanisms.

## Assessment after two adapters

The first adapter produced no statistically resolved logical difference after a
shared-decoder correction. The second adapter produced decoder-hidden fusion-bit
errors up to 1.7528% among full Bell records, but the tested unboosted primitive
does not provide a viable unencoded six-ring operating point. Consequently, the
primary hypothesis is **not strictly falsified**, because the second adapter has
not been tested in a suitable encoded or boosted architecture. It is also **not
supported strongly enough** to justify expecting a top-journal paper.

The project is paused rather than narrowed. Resuming it requires independent
reason to believe that a realistic architecture-level comparison can change a
threshold, subthreshold overhead, or hardware ranking.
