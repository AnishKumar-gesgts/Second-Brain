# Phase 5 Notes - Differentiable Logical-Error Surrogate and Allocation Optimization

[[Anish's Second Brain/Projects/Quantum/Ideas/End-to-End Differentiable Photonic Fault-Tolerance Co-Design|End-to-End Differentiable Photonic Fault-Tolerance Co-Design]]

## Purpose

Phase 5 replaces the expensive inner optimization loop around discrete Stim sampling and Peeling + MWPM decoding with a differentiable approximation of logical error. The real pipeline remains the scientific reference:

$$
\mathbf q \longrightarrow \text{nonuniform effective channels} \longrightarrow \text{Stim samples} \longrightarrow \text{Peeling + MWPM} \longrightarrow P_L.
$$

Here $\mathbf q=(q_1,\ldots,q_n)$ assigns continuous quality or resource fractions to effective six-ring locations. Stim and the decoder do not provide a stable analytic derivative $\partial P_L/\partial q_i$; changing one allocation normally requires another noisy Monte Carlo evaluation.

## Differentiable surrogate

Train a small regressor so that $\widehat P_L(\mathbf q;\phi)\approx P_L(\mathbf q)$, where $\phi$ denotes learned model parameters. PyTorch automatic differentiation then supplies

$$
\nabla_{\mathbf q}\widehat P_L=\left(\frac{\partial \widehat P_L}{\partial q_1},\ldots,\frac{\partial \widehat P_L}{\partial q_n}\right).
$$

These gradients describe the surrogate locally. They are optimization guidance, not measurements of the true Monte Carlo pipeline.

## First implementation

The initial repository uses a deliberately small PyTorch multilayer perceptron. It includes dataset generation/loading, a fixed disjoint training/validation split, MAE/RMSE/$R^2$, gradients for every allocation variable, and projected gradient descent under

$$
0\le q_i\le1,\qquad\sum_iq_i=C.
$$

An adapter calls the existing Phase 3 simulator and retains Peeling + MWPM as the ground-truth decoder. It records shot and failure counts, Wilson intervals, seeds, physical-noise controls, and complete allocations because $P_L$ labels are noisy binomial estimates rather than exact values.

## Validation rule

A surrogate optimum is only a proposal. Freeze the candidate and compare it with uniform and established Phase 2 allocations using fresh simulator seeds, identical physical settings, both logical bases, and sufficient shots to report uncertainty. Count simulator shots used to build the surrogate as part of the optimization budget.

A small smoke run establishes software integration only; it cannot establish a lower logical error rate or a distance-scaling advantage.

## Scientific boundaries

- Peeling + MWPM remains the fixed decoder target. MCMC-CRW stays out of the project for now.
- This is allocation-to-logical-error regression, not another learned residual decoder study. The [[Anish's Second Brain/Projects/Quantum/Phase 4 Notes - Learned Decoder Integration and Evaluation|Phase 4]] null result remains intact.
- The current six-ring roles are mapped onto rotated-memory data world lines, not a native fusion-based/RHG detector circuit.
- The effective-channel pipeline is not a full Fock-space simulation or hardware validation.
- A differentiable surrogate does not make Stim, PyMatching, or Peeling differentiable.
- Final claims remain deferred until the physical channel and architecture mapping define stable variables and costs.

## Next evidence gates

- Generate a space-filling fixed-budget dataset across multiple seeds and both logical bases.
- Test whether validation error is small relative to the logical-error differences being optimized.
- Compare the learned gradient with held-out finite-difference perturbations.
- Re-simulate the frozen proposal, uniform control, and Phase 2 baselines on independent shots.
- Test robustness to component drift and graphlike approximation/fallback behavior.

## Current Phase 5 evidence

The first full distance-3 study completed 2,960,000 decoded shots: 128 fixed-budget allocations with 10,000 Stim + Peeling/MWPM shots per allocation in each logical basis, followed by 100,000 fresh validation shots for uniform and the frozen proposal in each basis.

The surrogate did not learn reliable held-out allocation variation. Logical X validation was MAE $8.67\times10^{-4}$, RMSE $1.16\times10^{-3}$, and $R^2=-7.07$; logical Z was MAE $9.48\times10^{-4}$, RMSE $1.26\times10^{-3}$, and $R^2=-6.25$. These errors are comparable to the full observed $P_L$ range.

In the real-simulator check, logical X was $223/100{,}000=0.00223$ for uniform and $198/100{,}000=0.00198$ for the proposal. Logical Z was $196/100{,}000=0.00196$ for uniform and $205/100{,}000=0.00205$ for the proposal. The Wilson intervals overlap. Approximate unpaired two-proportion tests give $p=0.223$ for X and $p=0.653$ for Z, so neither difference is resolved and the direction does not reproduce across bases.

**Status:** the end-to-end implementation is operational, but the first full study is a scoped negative/inconclusive result. It does not validate the surrogate or demonstrate an improved allocation. Improve label precision or use binomial-aware modeling and paired comparisons before further optimizer tuning.

## Connections

- [[Anish's Second Brain/Projects/Quantum/Phase 2 Notes - Decoder-Aware Photonic Hardware Allocation|Phase 2]] supplies the fixed-cost allocation question.
- [[Anish's Second Brain/Projects/Quantum/Phase 3 Notes - Hybrid Erasure-MWPM Decoder for Photonic Circuits|Phase 3]] supplies the retained decoder and real evaluation interface.
- [[Anish's Second Brain/Projects/Quantum/Phase 4 Notes - Learned Decoder Integration and Evaluation|Phase 4]] supplies the no-regression lesson for learned additions.

#quantum-photonics #qec #differentiable-computing #surrogate-model #resource-allocation
