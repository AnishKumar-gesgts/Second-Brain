# Baseline result

The frozen held-out study **supports** the model-scoped hypothesis that a finite temporal gate can reduce decoded logical error relative to no filtering.

- Selected pilot gate: **140 ps** at distance 5.
- Held-out selected-gate logical error: **0.092045** (95% Wilson CI 0.09148-0.0926132).
- Held-out no-filter logical error: **0.112645** (95% Wilson CI 0.112027-0.113266).
- Rate ratio (no filter / selected): **1.22x**.
- Same selected gate with herald flags hidden from the decoder: **0.158104**.
- Selected-gate distance-3 to distance-7 rate ratio: **0.773** (significant suppression: **True**).
- No-filter distance-3 to distance-7 rate ratio: **0.994** (significant suppression: **False**).

## Interpretation

The result is evidence for the tradeoff within the specified Gaussian detuning model and decoder mapping. It is not evidence for a device-independent optimum, a full six-ring/RHG architecture, or a photonic fault-tolerance threshold. The next useful extension is to replace the hard gate with a calibrated time-dependent soft/phase-aware decision rule and test it under non-Gaussian wavepackets and imperfect heralds.
