# Baseline result

The frozen held-out study **supports** the model-scoped hypothesis that a finite temporal gate can reduce decoded logical error relative to no filtering.

- Selected pilot gate: **110 ps** at distance 5.
- Held-out selected-gate logical error: **0.166189** (95% Wilson CI 0.165461-0.16692).
- Held-out no-filter logical error: **0.229372** (95% Wilson CI 0.228549-0.230197).
- Rate ratio (no filter / selected): **1.38x**.
- Same selected gate with herald flags hidden from the decoder: **0.289759**.
- Selected-gate distance-3 to distance-7 rate ratio: **1.01** (significant suppression: **False**).
- No-filter distance-3 to distance-7 rate ratio: **1.3** (significant suppression: **False**).

## Interpretation

The result is evidence for the tradeoff within the specified Gaussian detuning model and decoder mapping. It is not evidence for a device-independent optimum, a full six-ring/RHG architecture, or a photonic fault-tolerance threshold. The next useful extension is to replace the hard gate with a calibrated time-dependent soft/phase-aware decision rule and test it under non-Gaussian wavepackets and imperfect heralds.
