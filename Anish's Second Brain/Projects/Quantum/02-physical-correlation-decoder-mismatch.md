# Project Prompt: Physically Generated Correlation Versus Decoder Mismatch

## Project status

New candidate from Iteration 24. Status: **PROMISING BACKUP**.

This is not a generic correlated-decoder project and not the claim that PyMatching cannot represent correlations. The central comparison must use the same physically generated source and distinguish exact multi-detector mechanisms from graphlike approximations.

## Core research question

When a fusion network is driven by physically generated multi-detector correlations, which decoder mismatch—independent erasure, graphlike detector-error-model decomposition, or correlation-aware inference—first changes the observed code-distance trend?

## Physical mechanism

A single source, loss, multiphoton, mode-overlap, or detector-history event can affect multiple detectors and/or an observable. Two noise models can therefore share all single-detector marginals while differing in hyperedge structure and decoder likelihoods.

## Required framework roles

- **Strawberry Fields:** Simulate the local optical fusion or resource primitive that generates the physical event correlations.
- **Record bridge:** Emit exact multi-detector mechanisms, coordinates, and observables from the conditional physical record.
- **Stim:** Store and sample reduced detector-error models, including multi-target mechanisms.
- **PyMatching:** Provide fast graphlike decoding and the decomposition baseline.
- **Small-code likelihood decoder:** Audit the approximation on a tractable instance.

The key result is logical behavior under identical physically generated correlations, not a software feature comparison.

## Minimum viable experiment

1. Choose one small fusion network and a distance-3/5 repeated stabilizer schedule.
2. Construct independent and correlated models matched on all single-detector marginals.
3. Compare exact multi-detector sampling, `decompose_errors=True`, graphlike decoding, and a small-code likelihood decoder.
4. Measure logical error, decoder ranking, hyperedge frequency, and decomposition bias.

Do not treat a graphlike decomposition as the physical reference. The operational measurement, encoding, feed-forward, reset, time ordering, and logical observable must be fixed before comparison.

## Full paper path

Add source (g^{(2)}), loss placement, mode mismatch, detector-history kernels, distances 3/5/7, multiple schedules, supported correlated matching, and a runtime/accuracy phase diagram. Include a regime where decomposition is demonstrably safe.

## Required novelty boundary

Check literature on photonic correlated noise, detector-error models, designed fault-tolerant circuits, correlated decoding, and learned logical-circuit decoders before claiming novelty. The defensible boundary is a photonic-mechanism-resolved comparison in which the same physical source is decoded under competing abstractions and the first distance or round at which decomposition changes a decoder or scaling conclusion is measured.

## Main risks

- Hyperedges are too rare to affect logical results.
- A custom likelihood decoder is too expensive.
- Correlations are architecture-specific.
- A current correlated decoder closes the gap.
- The required correlation strengths are physically unrealistic.

## Kill criteria

Kill if matched-marginal physical models never change decoder ranking beyond uncertainty, if a supported correlated decoder closes the gap without a photonic-specific finding, or if the effect requires unphysical correlation strengths.

## Deliverable requirements

Provide the physical event model, exact multi-target record representation, decomposition definition, decoder baselines, held-out logical trials, uncertainty estimates, and a clear statement of the regime in which graphlike decoding is or is not trustworthy.

## Source boundary

Derived from the “Candidate B — Physically generated correlation versus decoder mismatch” section at the bottom of `Photonic QEC Research Ideation — Model Handoff Protocol (Unedited).md`. Do not turn this into the historical generic correlated photon-loss project.
