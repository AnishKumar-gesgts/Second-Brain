# QEC-Optimized Temporal Filtering

[[Ideas]]

## Research question

For one specified photonic interference or fusion primitive with imperfect temporal-mode overlap, which temporal filter setting minimizes decoded logical error \(P_L\), rather than simply maximizing optical visibility or coincidence rate?

Temporal distinguishability can cause accepted, **unheralded** faults. Narrowing a temporal gate suppresses those faults but rejects additional events, increasing decoder-visible erasures. The central tradeoff is therefore

$$
\text{filter width } \tau
\longrightarrow
\bigl(p_{\mathrm{accepted\ error}},\ p_{\mathrm{erasure}},\ P_L\bigr).
$$

## Minimum Strawberry Fields primitive

Start with a two-photon interference/fusion primitive: two wavepackets with controllable delay/overlap, a balanced interferometer, a temporal acceptance window, and an explicit detector efficiency/timing model. The output is a normalized table of decoder-visible event classes: accepted-correct, rejected/lost (heralded erasure or failed fusion), and accepted-but-corrupted (ordinary accepted record, with no hidden fault label).

Use a finite Fock cutoff and temporal discretization only after verifying ideal limits, probability conservation, and convergence. This is a primitive-level optical calculation, not full-architecture Fock-space simulation.

## Stim/PyMatching handoff

Compile each physical point \((\delta t,\tau,\eta_d,\ldots)\) into effective QEC fault probabilities plus an observable herald/erasure record. Stim and PyMatching receive only what a real decoder could observe—detector outcomes and heralds—not hidden temporal-mode information used to generate the distribution.

## First baseline experiment

Fix one mismatch regime and sweep \(\tau\). At each point compile the physical outcome table into the same fixed QEC circuit and decoder, then report acceptance, erasure rate, accepted-error rate, \(P_L\), and uncertainty. Include no filtering, near-ideal overlap, and independent-loss/ideal-interference controls. Freeze all final settings before held-out QEC evaluation.

## Role in the program

This is **Idea 2** and a complete model-scoped project on its own. Its event-table interface is intentionally the first adapter for [[Physical Photonic Noise Compiler|Idea 3]].

Project charter: [[Anish's Second Brain/Projects/Quantum/Active Research Projects/QEC-Optimized Temporal Filtering/README|QEC-Optimized Temporal Filtering]].

#quantum-photonics #temporal-filtering #strawberry-fields #stim #pymatching
