# Differentiable Discovery of Asymmetric Photonic QEC Architectures

[[Ideas]]

## Central question

Under a fixed photon or hardware budget, how should redundancy be distributed across a photonic fault-tolerant architecture?

## Core idea

Let $r_i$ represent redundancy assigned to fusion/site/edge $i$. Optimize

$$
\min_{\{r_i\}} P_L
$$

subject to

$$
\sum_i r_i \le N_{\max}.
$$

Possible design variables include tree-encoding depth, redundant photons, fusion and measurement redundancy, graph connectivity, bridge-node protection, ancilla allocation, and temporal multiplexing.

## Main hypothesis

The best finite-resource architecture is not necessarily uniform. An optimizer may discover heavily protected bridge nodes, lightly protected bulk nodes, asymmetric tree encodings, unequal redundancy for different fusion types, or topology-dependent protection.

The result becomes stronger if optimization reveals a simple transferable rule, for example

$$
r_i^\star \sim f(\text{centrality}_i,\text{logical sensitivity}_i,\text{loss exposure}_i).
$$

## Toolchain

**PennyLane** for optimization when differentiable relaxation is possible; **Stim** for logical QEC simulation; **PyMatching** for decoding; and **Strawberry Fields** for physical photonic error modeling.

## Connections

- Generalizes [[Anish's Second Brain/Projects/Quantum/Phase 2 Notes - Decoder-Aware Photonic Hardware Allocation|Phase 2 - Decoder-Aware Photonic Hardware Allocation]] from component quality to topology and redundancy.
- Can be embedded inside [[End-to-End Differentiable Photonic Fault-Tolerance Co-Design]].
- [[Correlated Photon-Loss Burst QEC]] may strongly change the optimal redundancy map.

#quantum-photonics #qec #architecture-search #differentiable-computing
