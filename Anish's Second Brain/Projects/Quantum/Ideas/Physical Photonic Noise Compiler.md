# Physical Photonic Noise Compiler

[[Ideas]]

## Research question

Can a reusable interface translate physical photonic parameters and small optical-primitive models into decoder-honest effective QEC fault models accurate enough for scalable Stim/PyMatching simulation?

$$
\text{physical parameters}
\rightarrow
\text{observable event distribution}
\rightarrow
\text{effective faults + herald record}
\rightarrow
\text{Stim/PyMatching}.
$$

## Compiler contract

An optical adapter, such as Strawberry Fields or a validated analytic model, receives source, loss, overlap/visibility, detector, filtering, and routing parameters. It returns a normalized conditional distribution over observable measurement records. The compiler maps those records to erasures, fusion failures, Pauli/measurement faults, and any retained correlation structure.

Its output must include fault probabilities and semantics, the herald information legitimately available to the decoder, provenance for physical parameters and convergence settings, and an explicit statement of correlations retained or approximated. It must never leak hidden Fock-state or temporal-mode labels to the decoder.

## Validation

Validate separately at three levels:

1. optical: ideal limits, probability conservation, loss controls, cutoff convergence;
2. compiler: conditional event-class probabilities and herald records;
3. QEC: logical-error, syndrome, and decoder-behavior agreement on tractable reference cases.

Agreement must be reported by physical regime; one matching point does not validate a universal compiler.

## First and second adapters

[[QEC-Optimized Temporal Filtering|Idea 2]] is the first adapter because it exposes a clear tradeoff between observable erasure and accepted hidden error. Once that contract is validated, [[Hidden Logical Errors from Multiphoton Emission and Photon Loss|Idea 1]] provides a distinct, higher-Fock-state and loss-masking test case.

Project charter: [[Anish's Second Brain/Projects/Quantum/Active Research Projects/Physical Photonic Noise Compiler/README|Physical Photonic Noise Compiler]].

#quantum-photonics #noise-compiler #strawberry-fields #stim #pymatching
