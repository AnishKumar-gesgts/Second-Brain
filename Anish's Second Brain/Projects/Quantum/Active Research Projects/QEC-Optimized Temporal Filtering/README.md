# QEC-Optimized Temporal Filtering

This repository implements Idea 2: optimize a temporal acceptance rule by decoded logical error, rather than optical visibility alone.

## Scientific scope

The physical adapter is one deliberately small primitive: two Gaussian single-photon wavepackets with a frequency mismatch, a balanced interferometer, detector timing jitter, detector efficiency, and a hard gate on the measured arrival-time difference. The joint temporal calculation is analytic/numerical; Strawberry Fields independently validates the finite-Fock-space `|1,1>` balanced-beamsplitter limit at cutoffs 3 and 4.

Each physical point first produces a normalized, portable scalar event table:

- `accepted_correct`
- `accepted_wrong` (an unheralded parity/Pauli fault)
- `rejected` (a heralded erasure)
- `loss` (a heralded erasure)

The original compiler maps that table to a code-capacity rotated surface-code memory. Stim samples the circuit and PyMatching sees syndrome and herald detectors only; it never sees the hidden temporal variable or event-class label.

The architecture-aware extension adds a fusion-level schema with mutually exclusive correct, wrong-`XX`, wrong-`ZZ`, correlated-wrong, `XX`-only erasure, `ZZ`-only erasure, full temporal-rejection erasure, and loss branches. It then samples Bell-fusion outcomes on a periodic 12-valent cubic-with-face-diagonals syndrome graph. [Bartolucci et al.](https://doi.org/10.1038/s41467-023-36493-1) identify the cubic-axis edges with `XX` outcomes and the face-diagonal edges with `ZZ` outcomes. The protocol-specific compiler follows [Chan et al.](https://doi.org/10.1103/PRXQuantum.6.020304): detuning-induced partial distinguishability flips the reported `ZZ` outcome with probability `(1-V)/2`, while temporal rejection and photon loss erase both outcomes.

This extension is an **architecture-aware periodic bulk model**, not a full six-ring/RHG logical block. It reproduces the published local graph degree, edge-observable assignment, and type-II distinguishability channel, but it does not construct planar logical boundaries or simulate a complete source/device. The decisive predeclared study found no statistically supported temporal-filter improvement in any of 16 detuning/jitter conditions, so optimization work is stopped rather than narrowing the original hypothesis to a tuned corner.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe scripts\run_study.py --config config\baseline.json
.\.venv\Scripts\python.exe scripts\run_robustness.py
.\.venv\Scripts\python.exe scripts\run_herald_robustness.py
.\.venv\Scripts\python.exe scripts\run_architecture_study.py
.\.venv\Scripts\python.exe scripts\run_protocol_study.py
```

The study writes CSV tables, JSON metadata, a Markdown interpretation, and NumPy/Matplotlib figures to `results/`.

## Validation gates

1. Probability conservation and ideal/unfiltered analytic limits.
2. Strawberry Fields Fock-cutoff agreement and temporal-grid convergence.
3. Decoder-visible event classification and exact categorical channel mapping.
4. Monte Carlo agreement with the compiled physical event distribution.
5. Frozen, independent-seed held-out QEC evaluation with Wilson intervals.
6. A 12-valent bulk calibration spanning 0.5%, 1.0%, and 1.5% independent error per fusion outcome.
7. Guarded pilot/held-out fusion-bulk comparisons across detuning and `XX`/`ZZ` correlation assumptions.
8. A protocol-specific 16-condition type-II study with anisotropic `XX`-axis/`ZZ`-diagonal channels and 30,000 held-out shots per distance.

## Layout

- `src/temporal_filter_qec/physics.py`: temporal-mode model and event tables.
- `src/temporal_filter_qec/fock.py`: Strawberry Fields beamsplitter validation.
- `src/temporal_filter_qec/qec.py`: Stim/PyMatching compilation and decoding.
- `src/temporal_filter_qec/fusion_events.py`: observable fusion-event schema and scalar-to-`XX`/`ZZ` compiler.
- `src/temporal_filter_qec/fusion_network.py`: periodic 12-valent bulk graph, exact event sampling, and logical-winding decoding.
- `src/temporal_filter_qec/architecture_study.py`: calibration, guarded selection, held-out controls, and figures.
- `src/temporal_filter_qec/protocol_study.py`: decisive protocol-specific grid, frozen pilot selection, and held-out evaluation.
- `src/temporal_filter_qec/study.py`: pilot selection, held-out evaluation, controls, and artifacts.
- `src/temporal_filter_qec/robustness.py`: guarded selection and held-out detuning/jitter/diffusion maps.
- `tests/`: unit, convergence, compiler, and integration tests.
- `config/baseline.json`: frozen baseline parameters and random seeds.
- `config/architecture.json`: frozen fusion-bulk parameters, sensitivity axes, shots, and random seeds.
- `config/protocol_exact.json`: frozen protocol-specific detuning/jitter grid and seeds.
- `RESULTS.md`: combined interpretation and revised hypothesis.
- `NOVELTY.md`: targeted literature comparison and defensible novelty boundary.
