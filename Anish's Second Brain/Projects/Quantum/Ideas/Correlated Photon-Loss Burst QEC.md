# Correlated Photon-Loss Burst QEC

[[Ideas]]

## Central question

How should photonic fault-tolerant architectures and decoders be redesigned when photon loss occurs in correlated bursts rather than as independent erasures?

## Motivation

A simplified model assumes

$$
P(E_1,\ldots,E_n)=\prod_i P(E_i).
$$

Shared source drift, switching failures, coupling fluctuations, detector dead periods, multiplexing failures, fabrication-dependent mode groups, and common optical paths can violate this assumption:

$$
P(E_1,\ldots,E_n)\ne\prod_i P(E_i).
$$

Simply showing that correlated loss makes QEC worse is not enough. The project needs a corrective principle: a decoder, graph construction, interleaver, syndrome schedule, or architecture change that exploits the correlation structure.

## Candidate directions

1. **Correlation-aware decoding:** represent likely multi-loss events explicitly in decoder weights or graph structure.
2. **Interleaving:** route photons so a physical burst maps to separated code locations rather than one contiguous logical region.
3. **Syndrome scheduling:** change check timing so common-mode failures do not erase a dangerous set of measurements simultaneously.
4. **Architecture design:** choose graph structures whose logical distance degrades slowly under burst loss.

## Noise model

Use a mixture

$$
P(\mathbf{E})=(1-\beta)P_{\mathrm{IID}}(\mathbf{E})+\beta P_{\mathrm{burst}}(\mathbf{E}),
$$

where $\beta$ controls the fraction of correlated events and a burst has spatial or temporal correlation length $\xi$. Map

$$
(p_{\mathrm{loss}},\beta,\xi,d)
$$

to logical error rate $P_L$.

## Strong result targets

- a decoder modification that recovers much of the IID threshold;
- an interleaving rule that converts burst loss into approximately independent erasures;
- an architecture whose effective distance remains large under finite correlation length;
- an analytical relation between correlation length and effective code distance.

For example, characterize $d_{\mathrm{eff}}(\xi)$ and identify when mitigation prevents rapid collapse.

## Toolchain

**Stim** for Monte Carlo QEC simulations; **PyMatching** for baseline and modified decoding; optionally **Strawberry Fields** for physical derivation of correlated loss and **PennyLane** for layout or mitigation optimization.

## Connections

- Provides a realistic noise model for [[End-to-End Differentiable Photonic Fault-Tolerance Co-Design]].
- May create strong nonuniformity in [[Anish's Second Brain/Projects/Quantum/Phase 2 Notes - Decoder-Aware Photonic Hardware Allocation|Phase 2 - Decoder-Aware Photonic Hardware Allocation]].
- May alter the optimal redundancy pattern in [[Differentiable Discovery of Asymmetric Photonic QEC Architectures]].
- Could combine with [[Analog-Information Decoding Across CV-DV Photonic QEC]] when analog confidence contains common-mode information.

#quantum-photonics #qec #correlated-noise #photon-loss
