# Validation Roadmap

## Stage 1 — Contract and first adapter — complete

- Define mutually exclusive branches, faults, erasures, heralds, provenance, and hidden validation labels.
- Guarantee that decoder-facing exports cannot contain hidden optical labels or fault truth.
- Import the frozen Idea 2 type-II temporal channels.
- Quantify the joint information lost by matched independent scalarization.

Gate: probability conservation, serialization, decoder-view privacy, analytic marginal agreement, and automated tests must pass.

## Stage 2 — QEC equivalence and divergence harness — complete

- Compile full and simplified channels into the same Stim circuit family.
- Verify equality on deliberately independent controls.
- Search a predeclared physical grid for statistically resolved logical divergence.
- Attribute divergence to a specific removed correlation or herald record.

Gate: use frozen pilot/held-out seeds, Wilson intervals, and distance scaling. Do not optimize the architecture separately for each noise representation.

Result: after correcting a model-specific decoder confound, 0 of 18 held-out comparisons showed a significant difference. The first adapter's joint-erasure correlation changed event distributions but did not change tested logical conclusions under a shared marginal decoder.

## Stage 3 — Idea 1 adapter — fusion-level reference complete

- Model the `two photons emitted → one lost → one detected` mechanism in a tractable higher-Fock-space primitive.
- Separate apparently valid detector records from correctly heralded loss.
- Validate small optical cases before architecture-scale sampling.

Gate: no hidden photon-number label may reach the decoder. Agreement must hold across more than one loss and multiphoton probability.

Completed source-layer items:

- exact conditional photon-number distribution for a heralded biphoton source;
- common-schema support for hidden physical erasure and non-computational leakage;
- frozen 80-condition grid and a passed $10^{-12}$ truncation-tolerance gate.

Remaining items:

- implement one explicit fusion/interference circuit in higher Fock space;
- classify its output histories without inventing a generic Pauli replacement;
- compare the full event table with a detector-record-matched reduction before
  making an architecture-scale logical claim.

Update: the standard unboosted four-mode Bell-measurement reference is complete.
It produced hidden full-record errors up to 1.7528%, but its intrinsic 50%
partial-failure probability prevents a meaningful unencoded six-ring logical
comparison. Continuing requires a new boosted, encoded, or repeat-until-success
architecture model rather than additional shots on the current primitive.

## Stage 4 — Generality and publication assessment

- Add a third physically distinct adapter only after a literature and tractability review.
- Compare full versus reduced channels across common architecture and decoder baselines.
- Evaluate whether the compiler changes thresholds, scaling, or hardware rankings broadly enough to support a top-journal claim.

Consultation gate: pause before narrowing the primary hypothesis, restricting it to one favorable mechanism, or replacing decision-level consequences with event-table differences alone.

Status: **paused after publication assessment**. The two-adapter evidence does not
currently support a top-journal claim. See `PUBLICATION_ASSESSMENT.md` for the
resume criteria.
