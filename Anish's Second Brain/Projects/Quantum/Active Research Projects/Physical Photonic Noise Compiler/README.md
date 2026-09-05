# Physical Photonic Noise Compiler

Idea 3 is reusable infrastructure from small physical photonic models to scalable, decoder-honest QEC simulation.

## Contract

$$
\text{physical parameters}
\rightarrow
\text{observable outcome distribution}
\rightarrow
\text{effective QEC faults + herald record}
\rightarrow
\text{Stim/PyMatching logical evaluation}.
$$

Adapters must preserve conditional event probabilities and never provide hidden temporal-mode or Fock-state information to the decoder. Outputs include fault semantics, correlation treatment, provenance, and validation status—not only aggregate error rates.

## Validation program

Use Idea 2 as the first adapter, then Idea 1 as the multiphoton-plus-loss stress test. Validate optical behavior, compiled event distributions, and tractable QEC behavior separately before claiming that the interface is reusable.

This workspace is planning-only until implementation is requested.
