# Project Prompt: Photon-Number-Dependent Afterpulsing in Temporal-Fusion QEC

## Project status

New candidate from Iteration 24. Status: **PROMISING**; strongest experimentally anchored detector-noise candidate, subject to parameter-transfer validation.

This is not a revival of QEC-optimized temporal filtering. The variable under study is detector history and photon-number-dependent afterpulsing, not an acceptance-window optimization.

## Core research question

Does photon-number-dependent SNSPD afterpulsing create a logical-error penalty that cannot be predicted from average efficiency, dark-count rate, and fusion success alone in a temporal-fusion schedule?

## Physical mechanism

An earlier detection event can change the probability of a later click because the detector has memory. If afterpulse probability depends on photons per pulse and persists over the time separation used by a temporal-fusion schedule, it can create history-dependent false positives or missed detections even when average detector metrics are matched.

## Required framework roles

- **Strawberry Fields:** Produce source photon-number and interference statistics for one named temporal-fusion primitive.
- **Detector layer:** Apply an experimentally motivated afterpulse kernel, dead time, finite timing resolution, and any required conditional efficiency.
- **Stim:** Represent repeated syndrome extraction and sample large stabilizer workloads.
- **PyMatching:** Compare static average-efficiency weights with time-dependent or history-conditioned weights.
- **Small-code audit:** Check the physical-record-to-QEC bridge directly.

## Minimum viable experiment

1. Select a temporal-fusion schedule with an explicit time separation.
2. Reproduce the published qualitative photon-number dependence using a parameterized afterpulse kernel.
3. Bracket the kernel with conservative and aggressive fits rather than relying on one arbitrary value.
4. Match average efficiency and dark counts between memoryless and history-aware models.
5. Run a short repeated-syndrome schedule for at least two round counts and measure (P_L), decoder ranking, and uncertainty intervals.

## Full paper path

Fit multiple published detector models; include delay loss and emitter memory; vary schedule spacing; test distance scaling; and compare hardware mitigation against history-aware decoding. Add a second detector-history mechanism only if it tests transfer rather than simply expanding the model.

## Required novelty boundary

Verify primary evidence for the detector mechanism and distinguish it from the already known fact that detector history exists. The defensible contribution is the logical comparison at matched average detector metrics using sourced afterpulse parameters in a named photonic-QEC schedule.

## Main risks

- Published afterpulse behavior does not transfer to the target detector.
- The chosen architecture does not use a relevant time separation.
- Stim state expansion obscures the causal mechanism.
- Re-estimated conditional weights absorb the logical effect.
- The result duplicates existing detector-noise studies.

## Kill criteria

Kill if all sourced kernels agree with the memoryless model within confidence intervals, if the target architecture has no relevant time separation, or if the effect disappears after conditional calibration.

## Deliverable requirements

Document the detector kernel and its source, separate measured facts from fitted assumptions, match average metrics explicitly, run held-out logical trials, and report both positive and negative regimes. Do not claim universal SNSPD behavior from one parameterization.

## Source boundary

Derived from the “Candidate C — Photon-number-dependent afterpulsing in temporal-fusion QEC” section at the bottom of `Photonic QEC Research Ideation — Model Handoff Protocol (Unedited).md`. Do not reintroduce temporal filtering as the project objective.
