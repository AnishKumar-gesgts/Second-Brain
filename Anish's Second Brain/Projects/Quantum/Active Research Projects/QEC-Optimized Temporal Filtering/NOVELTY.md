# Novelty Assessment

Reviewed 2026-09-05 using targeted searches of arXiv, APS, Nature-family journals, and the references surfaced by those searches.

## What is already established

The broad ingredients are not individually novel:

1. **Time-resolved detection can recover interference and fusion fidelity from frequency-distinguishable photons.** The 2024 PRL experiment reported improved interference when effective timing resolution was changed from 200 ps to 20 ps and applied time-resolved detection to a type-II fusion operation. [On-Chip Quantum Information Processing with Distinguishable Photons](https://doi.org/10.1103/PhysRevLett.132.150602)
2. **Temporal quantum erasure for fusion gates has a direct theoretical treatment.** Aqua and Dayan describe heralding the exchange-symmetric component of distinguishable-photon states. [Temporal Quantum Eraser](https://arxiv.org/abs/2404.01516)
3. **Soft information can improve surface-code decoding, and a physical setting that minimizes physical error need not minimize logical error.** This was demonstrated for general soft measurement outcomes, not specifically photonic fusion time tags. [Improved Quantum Error Correction Using Soft Information](https://arxiv.org/abs/2107.13589)
4. **FBQC already distinguishes erasure and Pauli-type failure and evaluates them at the logical level.** [Fusion-Based Quantum Computation](https://doi.org/10.1038/s41467-023-36493-1)
5. **Photon distinguishability is already included in architecture-level fault-tolerance studies.** A 2025 PRX Quantum study reports separate photon-loss and distinguishability thresholds for emitter-tailored FBQC. [Tailoring Fusion-Based Photonic Quantum Computing Schemes to Quantum Emitters](https://doi.org/10.1103/PRXQuantum.6.020304)
6. **Very recent work studies how fusion protocols transform partial distinguishability.** The September 2026 preprint compares the distinguishability left by different successful fusion events, which makes protocol-specific modeling more important. [Photonic Fusion Operations Transform Partial Distinguishability](https://arxiv.org/abs/2609.01019)

## Defensible novelty

The project should **not** claim that temporal filtering, soft decoding, or logical-level hardware optimization is new in isolation.

The potentially novel contribution is their specific closed loop:

$$
\text{time-resolved distinguishable-photon model}
\rightarrow
\text{observable error/erasure event table}
\rightarrow
\text{erasure-aware logical decoding}
\rightarrow
\text{QEC-selected temporal policy}.
$$

The robustness result adds a concrete design claim: the optimum is conditional, with a measurable detuning/jitter region where filtering helps and a region where it should be disabled. The targeted search did not find a paper that reports this exact logical-error-optimized temporal-filter phase diagram for photonic fusion.

The architecture-aware follow-up sharpens this boundary. A periodic 12-valent bulk sensitivity proxy found no confidence-qualified temporal-filter advantage in nine detuning/correlation conditions. The decisive protocol-specific study then assigned detuning errors only to the published `ZZ` face-diagonal edges and again found no significant improvement in any of 16 predeclared detuning/jitter conditions. This negative result identifies an abstraction-sensitive failure: a filter that looks favorable when one scalar event is applied per surface-code data qubit does not retain that advantage when compiled into the local six-ring syndrome geometry.

That finding is still not a complete six-ring logical-block or hardware result. The model matches the local degree and edge-observable semantics in [Fusion-Based Quantum Computation](https://doi.org/10.1038/s41467-023-36493-1) and the type-II distinguishability outcome map in [Tailoring Fusion-Based Photonic Quantum Computing Schemes to Quantum Emitters](https://doi.org/10.1103/PRXQuantum.6.020304), but it does not reproduce planar logical boundaries, full resource-state preparation, or a calibrated source/device. Novelty confidence is therefore **moderate for the closed-loop method**, **low for a positive architecture-level claim**, and insufficient to justify narrowing the hypothesis for a top-journal submission.

## Possible future projects, not continuations

1. Calibrate the temporal adapter against experimental time-tag histograms or a protocol-specific fusion model.
2. Replace the periodic 12-valent proxy with a six-ring stabilizer-complex generator, exact primal/dual fusion pairing, and published logical-block boundaries.
3. Compare hard gating with a decoder that consumes calibrated per-event time likelihoods.
4. Evaluate non-Gaussian wavepackets, missing/false heralds, and correlations between successive photons.
5. Compare against the fusion-protocol-dependent distinguishability transformations identified in the 2026 preprint.

The protocol-specific validation did not preserve the earlier improvement. Under the project's stopping rule, the honest conclusion is to stop this gate-optimization branch rather than tune a saturated abstraction or redefine success around a small corner. The items above would constitute new hypotheses and would need independent motivation before work resumes.
