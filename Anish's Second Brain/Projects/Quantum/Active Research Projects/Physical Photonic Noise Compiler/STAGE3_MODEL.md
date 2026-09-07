# Stage 3 Model: Hidden Source Histories Behind a Valid Herald

## Selected primitive

The second adapter uses a two-mode squeezed-vacuum biphoton source conditioned on exactly one photon-number-resolving count in the idler arm. This is the smallest literature-grounded primitive that directly contains the intended mechanism:

$$
\text{multiple pairs generated}
\rightarrow
\text{idler photons lost}
\rightarrow
\text{one idler count recorded}
\rightarrow
\text{apparently valid source herald}.
$$

The retained signal mode can nevertheless contain zero, one, or multiple photons. The zero-photon and multiphoton branches are physically distinct hidden faults even though the detector and decoder receive the same source-herald record.

This primitive follows the source and detector model in Randles, Muñoz-Arias, and Sarovar, [arXiv:2608.01549v1](https://arxiv.org/abs/2608.01549), especially Eqs. 12-14. That work explicitly models heralded sources with vacuum and multiphoton contributions and identifies false-positive heralds as a source of output-state fidelity loss.

## Parameters and exact distribution

Let $\mu=|\lambda|^2$ be the pair-generation parameter, $\eta_s$ be signal transmission, $\eta_{id}$ combine idler transmission and detector efficiency, and $\xi=\mu(1-\eta_{id})$.

The adapter evaluates the exact probability of a one-count idler herald and the exact conditional signal photon-number distribution from the cited source model. It retains photon numbers through $n=10$ and assigns the remaining analytic tail to a leakage branch rather than discarding or renormalizing it.

## Compiler semantics

| Hidden signal state | Simulator truth | Decoder-visible record |
|---|---|---|
| $n=0$ | unheralded physical erasure | valid one-count source herald |
| $n=1$ | correct single-photon state | valid one-count source herald |
| $n\geq2$ | non-computational photon-number leakage | valid one-count source herald |

This required a principled schema clarification: a physical erasure is decoder-visible only when a matching `erasure:<target>` herald exists. Leakage remains simulator truth and is never exported automatically. The existing temporal adapter already emits explicit erasure heralds, so its behavior is unchanged.

## Frozen source-level study

The grid in `config/stage3.json` contains 80 combinations of $\mu\in\{0.01,0.03,0.05,0.10,0.20\}$ and $\eta_s,\eta_{id}\in\{0.85,0.90,0.95,0.99\}$.

An initial $n=8$ cutoff failed the predeclared $10^{-12}$ tail-probability tolerance with a worst case of $5.27\times10^{-12}$. The cutoff was increased to $n=10$ without relaxing the tolerance. The successful run's worst tail was $5.66\times10^{-15}$.

## Current claim boundary

This study validates a second physical adapter, the hidden-history/visible-record separation, and the exact source-level probability calculation. It does **not** yet establish how multiphoton leakage propagates through a type-II fusion, how it should be reduced to Pauli or erasure faults, or whether it changes logical-QEC behavior. The QEC harness deliberately rejects leakage channels until that mapping is independently justified.

The next scientific step is a small higher-Fock-space simulation of one explicit fusion/interference circuit with output detection, followed by a tested event-classification table. A generic random-Pauli substitution would not be adequate.
