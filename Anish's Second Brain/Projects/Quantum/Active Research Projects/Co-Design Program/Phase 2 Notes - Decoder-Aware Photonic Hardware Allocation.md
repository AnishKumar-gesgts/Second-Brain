# Phase 2 Notes - Decoder-Aware Photonic Hardware Allocation

[[Ideas/Ideas|Quantum Photonics Ideas]]
[[Anish's Second Brain/Projects/Quantum/Phase 1 Notes - Surface-Code Memory and Simulation Fundamentals|Phase 1 Notes - Surface-Code Memory and Simulation Fundamentals]]
[[Anish's Second Brain/Projects/Quantum/Phase 3 Notes - Hybrid Erasure-MWPM Decoder for Photonic Circuits|Phase 3 Notes - Hybrid Erasure-MWPM Decoder for Photonic Circuits]]

## Central question

Given a fixed photonic hardware budget, how should heterogeneous source, routing, fusion, and detector quality be allocated across a realistic fusion-based photonic architecture to minimize logical error rate?

The benchmark is a **six-ring fusion-based photonic fault-tolerant/RHG logical-memory experiment**. The logical-memory task remains the standard QEC test: prepare a logical state, perform repeated error-correction rounds, decode, and measure whether the logical observable survived. The six-ring resource-state construction and its fusions provide the photonic physical setting in which that memory is built and protected.

This is a proof-of-principle architecture benchmark rather than a claim that one circuit is universal across the photonics industry. It is useful because it connects a recognized fault-tolerant photonic construction to the same logical-memory metric used in [[Anish's Second Brain/Projects/Quantum/Phase 1 Notes - Surface-Code Memory and Simulation Fundamentals|Phase 1]].

## Physical environment

The environment being optimized is not an abstract list of interchangeable photons. It includes location-dependent properties of:

- six-ring photonic resource-state generation;
- source brightness, purity, efficiency, and indistinguishability;
- delay lines, switching, multiplexing, and routing loss;
- fusion measurements and their success or failure probabilities;
- interference visibility and mode mismatch;
- detector efficiency, dark counts, and measurement error; and
- any correlations or herald information produced by these components.

These physical components induce effective loss, erasure, fusion-failure, measurement-error, Pauli, and correlated-error channels at particular locations in the RHG/QEC model.

## Core idea

Assign each physical location a quality vector

$$
q_i = (\eta_i, V_i, p_{\mathrm{dark},i}, p_{\mathrm{fusion},i}, \ldots),
$$

where $\eta_i$ is transmission/detection efficiency, $V_i$ is indistinguishability or interference visibility, $p_{\mathrm{dark},i}$ is dark-count probability, and $p_{\mathrm{fusion},i}$ is fusion-failure probability.

Optimize subject to

$$
\sum_i C(q_i) \le C_{\max},
$$

with objective

$$
\min_{\{q_i\}} P_L.
$$

Here, $C(q_i)$ may represent photons, multiplexing overhead, fabrication quality, detector quality, switching resources, or another explicit engineering cost. The comparison must hold the total cost fixed.

## Main hypothesis

The optimal architecture may be deliberately **nonuniform**: some graph locations may deserve much higher physical quality because their errors disproportionately affect logical failure.

A strong result would show that

$$
\frac{\partial P_L}{\partial q_i}
$$

varies strongly with location $i$, and that logical-sensitivity-based allocation beats uniform allocation at equal total cost.

The decoder supplies a logical sensitivity or importance map. For a location or component parameter $q_i$, estimate how changing it affects decoded logical failure, for example through finite differences, perturbation experiments, or a fitted surrogate:

$$
S_i \approx -\frac{\Delta P_L}{\Delta q_i}.
$$

Allocation should depend not only on raw sensitivity but on **cost-normalized benefit**:

$$
B_i \approx -\frac{\Delta P_L}{\Delta C_i}.
$$

The highest-quality hardware should be assigned where the expected reduction in decoded logical error per unit cost is greatest. This makes the optimization decoder-aware: two physically similar improvements can have different value because of their location in the code, the syndrome information they create, and the decoder's response.

## Phase 2A - selective-allocation proof of principle

Phase 2A asks the controlled question first: if some comparable locations can be made better than others under a fixed budget, can selective allocation reduce $P_L$ relative to uniform allocation?

- Use the six-ring FBQC/RHG logical-memory benchmark.
- Introduce deliberately heterogeneous effective error rates at selected source, routing, fusion, or detector locations.
- Compare uniform, random, heuristic, sensitivity-based, and optimized allocations at equal total cost.
- Derive decoder-based logical-importance maps and test whether they generalize across logical basis, code distance, and noise regime.

This stage establishes the allocation effect without claiming that every effective error rate has already been derived from a complete device model.

## Phase 2B - component-derived heterogeneous errors

Phase 2B replaces the controlled effective parameters with errors derived from realistic photonic components and layouts.

For component parameters $\theta_i$, construct a physical-to-QEC interface

$$
\theta_i
\rightarrow
\mathcal{E}_i(\theta_i)
\rightarrow
\text{effective erasure, Pauli, measurement, and correlated channels}
\rightarrow
P_L.
$$

Analytical photonic models and targeted **Strawberry Fields** simulations should characterize resource-state generation, transmission, interference, fusion, and detection at the component or small-subsystem level. Their outputs are then reduced to effective channels that can be inserted into **Stim** and decoded with **PyMatching**.

The full six-ring/RHG fault-tolerant architecture should not be simulated directly in Fock space. That would be computationally intractable and is unnecessary for the research question. Strawberry Fields supplies physically motivated local channel parameters; Stim and PyMatching supply scalable circuit-level sampling, decoding, and logical-error estimation.

## Experiments

- Compare uniform and optimized source, routing, fusion, and detector quality.
- Allocate a fixed number of high-quality components among lower-quality components at equal cost.
- Compare raw-physical-quality heuristics with decoder-sensitivity and cost-normalized-benefit allocation.
- Test generalization across logical basis, code distance, decoder choice, and heterogeneous noise regime.
- Derive a logical-importance map over the six-ring/RHG photonic graph.
- In Phase 2B, compare effective channels derived analytically and from targeted Strawberry Fields simulations.

## Current Phase 2A evidence

The first full controlled sweep used distances $d=3,5,7$, both logical memory bases, and $100{,}000$ held-out shots per allocation strategy. All tested basis-strategy series showed decreasing logical error from $d=3$ to $d=5$ to $d=7$, so the underlying memory remained in a distance-suppressing regime.

At $d=3$, the optimized equal-cost allocation reduced the logical-error point estimate by about $31\%$ relative to uniform allocation in both bases, with separated Wilson $95\%$ confidence intervals. At $d=5$, the corresponding reductions were about $24\%$ in the $X$ memory and $23\%$ in the $Z$ memory, again with separated intervals.

The $d=7$ result is unresolved. Relative to uniform allocation, the optimized point estimate was $11.9\%$ worse in the $X$ memory and $9.1\%$ better in the $Z$ memory, but both confidence intervals overlapped. This is not evidence that selective allocation stops helping at larger distance.

The optimizer itself was under-resolved at $d=7$. Its $20{,}000$-shot all-low search baselines contained only $32$ logical failures for the $X$ memory and $47$ for the $Z$ memory. In the $X$-basis importance map, $40$ of $49$ one-location perturbations received a negative estimated benefit, which is a strong indication that Monte Carlo noise dominated the finite-difference ranking. The held-out run therefore evaluated a noisily learned allocation rather than establishing the performance of the true optimum.

## Phase 2A status and Phase 2B handoff

Phase 2A is complete as a controlled proof-of-principle implementation and initial equal-cost allocation experiment. It establishes the simulation, allocation, held-out evaluation, and logical-importance-map machinery and gives positive distance-$3$ and distance-$5$ evidence. It does not yet establish a final architecture-level or hardware-level advantage.

The unresolved distance-$7$ statistics are recorded as a limitation, but the expensive re-optimization and high-shot validation should not be performed inside Phase 2. Those tests depend on the physical component model, the architecture-specific circuit mapping, and the final optimization method. They are deferred to the project-wide validation phase recorded in [[End-to-End Differentiable Photonic Fault-Tolerance Co-Design]].

Phase 2B is complete as a literature-grounded effective-channel and equal-resource allocation study. The implementation separates source, routing, detector, and fusion parameters; supports six-ring role-specific overrides; implements the published linear-optical physical-fusion erasure $p_0=1-(1-p_{\mathrm{fail}}/2)\eta^N$ and $(2,2)$-Shor encoded-erasure reduction; records every intermediate probability; and checks limiting cases. It now accepts reported BSM success and measurement-discrimination data and compares standard and Bell-pair-boosted BSM profiles under an explicit photon-resource cost.

This completion is scoped deliberately. Phase 2B establishes the auditable physical-parameter-to-effective-channel-to-decoder workflow and its model sensitivity; it is not a calibrated end-to-end device prediction. Native six-ring fusion-circuit validation, device-specific source/routing calibration, correlated multiphoton or common-mode loss, alternative optimizers, and the final multi-seed high-statistics gate remain in the post-Phase-2 stages of [[End-to-End Differentiable Photonic Fault-Tolerance Co-Design]].

## Current Phase 2B evidence

Two full sweeps used distances $d=3,5,7$, both logical bases, $100{,}000$ held-out shots per reported design, separate search and evaluation seeds, and a one-third boosted-location budget. A standard BSM consumes one normalized two-photon unit and a Bell-pair-boosted BSM consumes two, so every uniform, random, heuristic, sensitivity, and optimized allocation within a distance/basis point has the same expected photon cost.

The source-faithful success/loss abstraction uses the reported $p_{c,\mathrm{total}}=0.4905$ standard and $0.693$ boosted BSM success probabilities, a common reported $0.45\%$ per-photon loss, and no MDF-derived Pauli term, matching the assumptions of the paper's photon-loss threshold comparison. In this abstraction, all-boosted logical error decreased from about $6.2\%$ at $d=3$ to about $4.2\%$ at $d=7$, while all-standard and the one-third-boost allocations were not distance-suppressing. Nevertheless, optimized placement beat the equal-cost uniform mixture in all six distance/basis comparisons: by about $9.0$-$9.2\%$ at $d=3$, $4.9$-$5.4\%$ at $d=5$, and $4.5$-$7.9\%$ at $d=7$, with separated Wilson $95\%$ intervals in every comparison. This establishes a component-derived within-size allocation effect, not fault tolerance at the one-third-boost budget.

The conservative measured-outcome stress reduction instead uses $p_{\mathrm{conclusive}}=p_c/F_{\mathrm{MDF}}$, maps inconclusive outcomes to fusion failure, and maps $1-F_{\mathrm{MDF}}$ to an independent conditional outcome flip. The reported boosted average $F_{\mathrm{MDF}}=0.890$ then produces an $11\%$ flip proxy. Under this stronger interpretation, all tested profiles worsened with distance and optimized placement did not beat uniform. This is evidence that the conclusion is sensitive to the physical-to-Pauli reduction; it is not evidence that the demonstrated boosted BSM physically causes independent $11\%$ errors throughout a native six-ring network.

## Phase 2B sources

- [Fusion-based quantum computation](https://doi.org/10.1038/s41467-023-36493-1) supports the six-ring fusion-network setting, the hardware-agnostic erasure/Pauli interface, the physical-fusion erasure model, and the $(2,2)$-Shor encoded-erasure reduction used by the analytical bridge.
- [Boosted Bell-state measurements for photonic quantum computation](https://doi.org/10.1038/s41534-025-00986-2) supports the standard and boosted Bell-state-measurement photon counts, their ideal $50\%$ and $75\%$ success structure, photon-loss erasure modeling, and the experimental interference and detector context.
- [Minimizing Resource Overhead in Fusion-Based Quantum Computation Using Hybrid Spin-Photon Devices](https://arxiv.org/abs/2412.08611) provides architecture and resource-generation context for a $(2,2)$-Shor-encoded six-ring resource state; it is contextual rather than the source of the implemented channel formulas.

The optional visibility-to-Pauli mapping, $(1-V)/2$, remains a documented phenomenological proxy rather than an exact formula taken from these papers. It is disabled in both primary standard/boosted comparison pairs: the published abstraction has no Pauli term, while the measured-outcome stress test uses the reported MDF directly. A native circuit or targeted subsystem model must determine the correct correlated measurement channel before either reduction is treated as physically predictive.

## Toolchain

**Stim** for scalable heterogeneous logical-error simulations; **PyMatching** for decoding and decoder-derived sensitivity; **PennyLane** or classical optimization for constrained allocation; and **Strawberry Fields** or analytical models for component-level photonic characterization and effective-channel extraction.

## Connections

- A special case of [[End-to-End Differentiable Photonic Fault-Tolerance Co-Design]].
- Phase 3 in [[Anish's Second Brain/Projects/Quantum/Phase 3 Notes - Hybrid Erasure-MWPM Decoder for Photonic Circuits|Phase 3 Notes - Hybrid Erasure-MWPM Decoder for Photonic Circuits]] tests whether standard MWPM, erasure-aware MWPM, or peeling + MWPM changes the logical-sensitivity map and therefore the best equal-cost hardware allocation.
- Closely related to [[Differentiable Discovery of Asymmetric Photonic QEC Architectures]], which optimizes redundancy rather than only component quality.
- [[Correlated Photon-Loss Burst QEC]] may make the optimal allocation highly nonuniform.

#quantum-photonics #resource-allocation #qec #decoder-aware
