# Project Prompt: Observable Calibration Certification Under Decoder Mismatch

## Project status

New candidate from Iteration 24. Status: **PROMISING; recommended primary candidate**.

This project is not the active physical-noise compiler itself. Treat compiler and model-reduction code as shared infrastructure only. Do not claim that a generic Strawberry Fields-to-Stim interface is the contribution.

## Core research question

Can a finite set of experimentally measurable optical and detector observables certify, with a stated confidence bound, which of two decoder or architecture choices has lower logical error when the true microscopic photonic noise is only partially known?

## Scientific premise

Loss, (g^{(2)}), mode distinguishability, timing covariance, photon-number-dependent afterpulsing, and source memory constrain—but do not necessarily uniquely determine—the conditional detector record. Physically distinct source/detector models may match ordinary calibration metrics while producing different syndrome correlations and different decoder rankings.

The project must test whether calibration can support an actionable engineering decision, not whether a set of observables is globally or minimally sufficient.

## Required framework roles

- **Strawberry Fields:** Generate physically constrained optical/source ensembles and conditional records for one named fusion primitive.
- **Detector-history layer:** Convert optical records into time-tagged, finite-resolution observations, including any chosen history dependence.
- **Stim:** Run large stabilizer-circuit trials for each reduced physical-noise hypothesis.
- **PyMatching:** Compare static MWPM, graphlike decompositions, and supported correlation/history-aware alternatives.
- **Small-code audit:** Use direct sampling or maximum-likelihood decoding to check the reduction and decoder claims.

PennyLane and Qiskit are not required unless a later, explicit need is demonstrated.

## Minimum viable experiment

1. Choose one dual-rail fusion primitive, one repetition-code or distance-3 surface-code schedule, and two decoder or architecture choices.
2. Construct several source/detector models matched on loss, click rate, (g^{(2)}), and HOM-like visibility, but differing in conditional timing or afterpulse correlations.
3. Define a finite calibration budget and separate calibration shots, training models, held-out models, and held-out logical shots.
4. Estimate a confidence interval for the decoder-risk difference.
5. Test the proposed certificate on held-out syndrome shots and at least one held-out physical model.

The decision loss must be explicit—for example, selecting decoder (D_1) when (D_2) has lower held-out (P_L). Predeclare a tolerance (epsilon), confidence level, and maximum acceptable false-safe rate.

## Required comparisons

Compare certificates based on:

1. ordinary optical metrics;
2. syndrome-only data;
3. joint optical-plus-detector metrics; and
4. the physically generated conditional record as an audit reference.

Report logical error, confidence coverage, false-safe rate, false-alarm rate, decoder ranking, calibration shots, model size, and runtime. A certificate that predicts (P_L) but selects the wrong decoder fails.

## Full paper path

Extend to distances 3, 5, and 7; repeated rounds; a temporal-fusion schedule; sourced afterpulse kernels; model misspecification; calibration-budget scaling; a second optical primitive; and a transfer test. Include a negative regime in which ordinary observables are sufficient and the certificate correctly permits a decision.

## Main risks

- The project becomes generic statistics rather than photonic QEC.
- Priors or model-ensemble choices dominate the result.
- The decoder choices are too similar to distinguish.
- The certificate works only for an artificial model family.
- Required detector parameters are unavailable.
- Existing literature already supplies the same photonic risk certificate.

## Kill criteria

Kill or pivot if the decoder ranking is invariant across all physically plausible matched models, if coverage fails under held-out misspecification, if results change materially with arbitrary priors, or if a literature search finds the same photonic decision certificate.

## Deliverable requirements

Produce a reproducible implementation, a literature matrix, predeclared evaluation criteria, held-out results with uncertainty intervals, and a conclusion that distinguishes calibration certification from generic model reduction. Report negative results honestly.

## Source boundary

Derived from the “Candidate A — Observable calibration certification under decoder mismatch” section at the bottom of `Photonic QEC Research Ideation — Model Handoff Protocol (Unedited).md`. Do not revive the historical temporal-filtering, allocation, analog-decoding, or generic correlated-loss projects under this prompt.
