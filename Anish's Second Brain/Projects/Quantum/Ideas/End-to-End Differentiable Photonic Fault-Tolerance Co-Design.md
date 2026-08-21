# End-to-End Differentiable Photonic Fault-Tolerance Co-Design

[[Ideas]]

## Central question

Can the physical photonic system and the quantum-error-correction stack be optimized jointly for **logical error rate**, rather than optimizing component-level fidelity first and decoding afterward?

## Core idea

Build a pipeline

$$
\theta_{\mathrm{photonic}}
\rightarrow
P(\text{loss, fusion failure, Pauli error, distinguishability})
\rightarrow
\text{QEC circuit}
\rightarrow
P_L,
$$

and optimize

$$
\min_{\theta}
\left[
P_L(\theta)
+ \lambda_1 N_{\mathrm{photons}}
+ \lambda_2 D
+ \lambda_3 C
\right].
$$

The optimizer is judged by downstream logical performance, not only by a physical-layer proxy such as average fidelity.

The first concrete benchmark is a **six-ring fusion-based photonic fault-tolerant/RHG logical-memory experiment**. The physical design variables describe realistic resource-state generation, routing and delay, fusion measurements, interference, and detection. Analytical models or targeted Strawberry Fields simulations translate those component parameters into location-dependent effective error channels; Stim and PyMatching then evaluate the full fault-tolerant memory at scale. The complete architecture is not simulated directly in Fock space.

This proceeds in two stages: Phase 2A tests selective quality allocation with controlled heterogeneous effective channels, while Phase 2B derives those heterogeneous channels from realistic component models. Both stages compare designs at fixed total cost and prioritize the reduction in decoded logical error per unit cost.

## Why it could be novel

A parameter that barely changes average component fidelity could strongly affect a specific logical failure mechanism. Conversely, improving an obvious physical metric may have little effect on $P_L$.

Potential design rules include:

- some loss channels matter disproportionately;
- some fusion locations deserve more protection;
- a slightly worse physical circuit may yield a lower logical failure rate because its errors are easier to decode;
- the best hardware design depends on the code and decoder.

## Toolchain

- **Strawberry Fields:** component- and small-subsystem-level photonic loss, fusion, interference, and detector statistics used to derive effective channels.
- **PennyLane:** differentiable physical parameters or surrogate models.
- **Stim:** logical-circuit and syndrome simulation at scale.
- **PyMatching:** syndrome decoding and logical-failure estimation.
- **Qiskit:** optional logical-algorithm validation.

## Phase notes

- [[Anish's Second Brain/Projects/Quantum/Phase 1 Notes - Surface-Code Memory and Simulation Fundamentals|Phase 1 Notes - Surface-Code Memory and Simulation Fundamentals]]
- [[Anish's Second Brain/Projects/Quantum/Phase 2 Notes - Decoder-Aware Photonic Hardware Allocation|Phase 2 Notes - Decoder-Aware Photonic Hardware Allocation]]
- [[Anish's Second Brain/Projects/Quantum/Phase 3 Notes - Hybrid Erasure-MWPM Decoder for Photonic Circuits|Phase 3 Notes - Hybrid Erasure-MWPM Decoder for Photonic Circuits]]
- [[Anish's Second Brain/Projects/Quantum/Phase 4 Notes - Learned Decoder Integration and Evaluation|Phase 4 - Learned Decoder Integration and Evaluation]]
- [[Anish's Second Brain/Projects/Quantum/Phase 5 Notes - Differentiable Logical-Error Surrogate and Allocation Optimization|Phase 5 - Differentiable Logical-Error Surrogate and Allocation Optimization]]

## Project phase roadmap and deferred validation record

### Phase 1 - scalable logical-memory baseline

Establish and verify the homogeneous rotated-memory Stim/PyMatching baseline, both logical bases, $T=d$, reproducible seeds, per-shot logical grading, and uncertainty reporting. **Status: complete.**

### Phase 2A - controlled selective allocation

Test uniform, random, heuristic, sensitivity-based, and optimized allocations with controlled heterogeneous effective channels at equal normalized cost. Record the distance-$7$ uncertainty without spending the final validation budget before the physical model is ready. **Status: complete as a proof of principle; not a final physical claim.**

### Phase 2B - component-derived effective channels

Derive location-dependent erasure, Pauli, measurement, and fusion-failure channels from source, routing, fusion, interference, detector, and measured BSM parameters. The implemented bridge uses published linear-optical and $(2,2)$-Shor erasure equations, tested limiting cases, measured standard/boosted BSM profiles, an explicit ancillary-photon resource cost, held-out equal-cost allocation, and separate published-abstraction and MDF-stress interpretations. The primary model sources, results, and assumption boundary are recorded in [[Anish's Second Brain/Projects/Quantum/Phase 2 Notes - Decoder-Aware Photonic Hardware Allocation#Current Phase 2B evidence|Current Phase 2B evidence]] and [[Anish's Second Brain/Projects/Quantum/Phase 2 Notes - Decoder-Aware Photonic Hardware Allocation#Phase 2B sources|Phase 2B sources]]. **Status: complete as a literature-grounded effective-channel study; not a native-circuit or hardware claim.**

### Phase 3 - photonic-aware decoding

Compare standard MWPM, erasure-aware MWPM, and peeling + MWPM on identical mixed-noise fault samples. Preserve heralded loss and fusion-failure locations as decoder side information, measure logical error and decoding cost, and test whether decoder choice changes the Phase 2 logical-sensitivity map. The implemented effective-channel benchmark has passed a $100{,}000$-shot-per-point perfect-flag comparison across distances 3, 5, and 7 in both bases at one mixed-noise point, plus a $1{,}000$-shot imperfect-flag integration test. Both photonic-aware decoders improved the paired logical outcomes at every primary point, and the screening sensitivity ranking changed with decoder choice. Multi-regime, multi-seed, one-imperfection-at-a-time, equal-cost reallocation, and native-circuit validation remain deferred. MCMC-CRW remains out of scope unless those studies expose a limitation that justifies adapting it. See [[Anish's Second Brain/Projects/Quantum/Phase 3 Notes - Hybrid Erasure-MWPM Decoder for Photonic Circuits#Current Phase 3 evidence|Current Phase 3 evidence]]. **Status: implementation complete for the scoped effective-channel benchmark; scientific validation remains preliminary rather than a native-circuit or hardware claim.**

### Phase 4 - learned decoder integration

Keep Peeling + MWPM as the fixed reference and test whether a learned logical-residual correction adds value on identical held-out trials. The first linear NumPy implementation completed a $1.8$-million-shot study across three distances, both bases, and three outer seeds. It did not beat Peeling + MWPM, and photonic inputs did not beat the syndrome-only learned control. This study used a fixed rotated-memory circuit with effective six-ring roles and uniform location-quality scales; it did not use the Phase 2 optimized allocation, and it did not perform location-by-location physical-error reconstruction. Later analytical or Strawberry Fields component modeling may create more realistic heterogeneous, correlated, or analog channels, but that creates an opportunity rather than a guarantee of ML improvement. Further decoder hyperoptimization is therefore deferred until the physical channel model and architecture-specific mapping are stable enough to define a durable decoder target. See [[Anish's Second Brain/Projects/Quantum/Phase 4 Notes - Learned Decoder Integration and Evaluation|Phase 4 Notes]]. **Status: complete as a scoped learned-decoder feasibility study with a null result; no ML advantage claimed or required.**

### Phase 5 - differentiable logical-error surrogate

Learn a small differentiable approximation $\widehat P_L(\mathbf q)$ from nonuniform allocation vectors evaluated by the existing Stim and Peeling + MWPM pipeline. Use held-out metrics, extract $\nabla_{\mathbf q}\widehat P_L$, and apply projected gradients under $0\le q_i\le1$ and $\sum_iq_i=C$. Every optimum must be frozen and returned to the real simulator with fresh seeds before it is evidence. MCMC-CRW remains out of scope. The first full distance-3 study completed 2.96 million decoded shots but obtained strongly negative held-out $R^2$ in both bases; the frozen proposal's numerical X improvement was unresolved and reversed direction in Z. See [[Anish's Second Brain/Projects/Quantum/Phase 5 Notes - Differentiable Logical-Error Surrogate and Allocation Optimization#Current Phase 5 evidence|Current Phase 5 evidence]]. **Status: end-to-end implementation operational; first full surrogate/allocation study is a scoped negative/inconclusive result, with no optimized-allocation advantage demonstrated.**

### Post-Phase-2 architecture-specific circuit validation

Validate the six-ring resource-state and fusion construction, its mapping into the RHG/logical-memory detector circuit, herald and detector semantics, temporal structure, and any graphlike decomposition used by PyMatching. Compare the scalable effective-channel model against tractable component or subsystem calculations and document where correlations require custom preprocessing or a correlation-aware decoder.

### Post-Phase-2 optimizer integration

Choose the final optimizer only after the physical variables and cost constraint are established. For discrete component assignments, compare adaptive coordinate exchange or racing, discrete simultaneous-perturbation stochastic approximation, and reduced-dimensional Bayesian or surrogate-guided search. For continuous photonic parameters, test a differentiable relaxation

$$
0 \le q_i \le 1,
\qquad
\sum_i q_i = C_{\max},
$$

and optimize a validated surrogate $\widehat{P}_L(\mathbf q)$ with projected gradients or another constrained method. PennyLane is appropriate when the Phase 2B photonic model or surrogate is genuinely differentiable; it does not automatically differentiate through Stim sampling, PyMatching decisions, or discrete logical-failure counts. Freeze every candidate design before held-out logical evaluation.

### Final statistical validation and generalization gate

Assign this work a phase number only after the intervening project phases are designed. Perform the expensive statistical work only after the component-derived channels, architecture-specific circuit mapping, calibrated cost model, and optimizer are validated:

1. Re-estimate the distance-$7$ importance map with at least $250{,}000$-$500{,}000$ search shots per perturbation, or adaptively sample to a predeclared failure-count or uncertainty target.
2. Use $1$-$2$ million held-out shots per final strategy and repeat across independent search and evaluation seeds.
3. Learn each allocation on one seed and physical-noise realization, freeze it, and test it across held-out seeds, both logical bases, component drift, and correlated-noise settings.
4. Compare optimization methods under the same total simulation-shot budget and hardware-cost constraint, including the cost of surrogate training data.
5. Run distance $9$ only after the distance-$7$ ranking is stable under the validated physical model.
6. Predeclare the success criterion: the optimized allocation must reproduce across seeds and bases, remain useful under held-out physical variation, and improve decoded logical error with reported uncertainty at fixed calibrated cost.

This deferred validation record should be carried into the appropriate future phase-specific note so the unresolved Phase 2A statistics are not forgotten or prematurely treated as a physical conclusion.

### Method references

- [PennyLane gradients and training](https://docs.pennylane.ai/en/stable/introduction/interfaces.html)
- [Optimization with discrete simultaneous perturbation stochastic approximation](https://arxiv.org/abs/1311.0042)
- [Optimal adaptation of surface-code decoders to local noise](https://arxiv.org/abs/2403.08706)
- [Correcting non-independent and non-identically distributed errors with surface codes](https://quantum-journal.org/papers/q-2023-09-26-1123/)

## Technical challenge

Stim and PyMatching are not naturally differentiable. Possible ways to connect their discrete logical-error estimates to optimization include:

- differentiable surrogate models for $P_L$;
- stochastic-gradient estimators;
- finite-difference gradients;
- Bayesian optimization;
- differentiable approximations to decoding;
- alternating hardware and decoder optimization.

This methodological problem could itself become part of the contribution. The project roadmap defers the final optimizer comparison and high-shot validation until the physical channels, architecture-specific circuit mapping, and calibrated cost model have been established.

## Metrics

$P_L$, photon/resource count, code distance, fusion success probability, loss rate, correlated-error rate, circuit depth, optimization convergence, and robustness to fabrication or noise drift.

## Connections

- [[Anish's Second Brain/Projects/Quantum/Phase 2 Notes - Decoder-Aware Photonic Hardware Allocation|Phase 2 Notes - Decoder-Aware Photonic Hardware Allocation]] is a constrained special case.
- [[Differentiable Discovery of Asymmetric Photonic QEC Architectures]] generalizes the design variables to redundancy and topology.
- [[Analog-Information Decoding Across CV-DV Photonic QEC]] provides a richer physical-to-decoder information interface.
- [[Correlated Photon-Loss Burst QEC]] supplies a realistic non-IID noise model.

#quantum-photonics #qec #differentiable-computing #fault-tolerance
