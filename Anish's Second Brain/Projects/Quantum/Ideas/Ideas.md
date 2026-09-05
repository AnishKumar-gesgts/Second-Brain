# Photonic QEC Research Program

## Intended sequence

1. [[QEC-Optimized Temporal Filtering|Idea 2 — QEC-Optimized Temporal Filtering]]
   - Build one optical model, measure the distinguishability-versus-erasure tradeoff, and optimize for decoded \(P_L\).
2. [[Physical Photonic Noise Compiler|Idea 3 — Physical Photonic Noise Compiler]]
   - Generalize Idea 2's physical-to-QEC handoff into reusable validated infrastructure.
3. [[Hidden Logical Errors from Multiphoton Emission and Photon Loss|Idea 1 — Hidden Logical Errors from Multiphoton Emission and Photon Loss]]
   - Test the compiler on higher-Fock-state effects and loss-masked, unheralded faults.

## Shared interface

$$
\text{physical photonic parameters}
\rightarrow
\text{Strawberry Fields / analytical primitive}
\rightarrow
\text{conditional observable-event compiler}
\rightarrow
\text{Stim + PyMatching}
\rightarrow
P_L.
$$

The decoder receives only detector and herald information; hidden mode or Fock-state labels are not available to it.

## Project workspaces

- [[Anish's Second Brain/Projects/Quantum/Active Research Projects/QEC-Optimized Temporal Filtering/README|Idea 2 project workspace]]
- [[Anish's Second Brain/Projects/Quantum/Active Research Projects/Physical Photonic Noise Compiler/README|Idea 3 project workspace]]

## Immediate next step

For Idea 2, specify the minimum two-photon primitive, the detector and filter model, the decoder-visible event table, and the fixed first Stim/PyMatching baseline. Do not make a one-off simulator: the event table is the reusable Idea 3 interface.

#quantum-photonics #quantum-error-correction #strawberry-fields #stim #pymatching
