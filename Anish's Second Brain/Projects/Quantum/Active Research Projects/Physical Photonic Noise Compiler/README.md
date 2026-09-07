# Physical Photonic Noise Compiler

Physical photonic simulations and QEC simulations describe different objects. An optical model tracks modes, photons, interference, loss, and detector records; a decoder consumes syndromes and legitimately available herald information. This project builds and tests the missing contract between those layers.

## Central hypothesis

> A decoder-honest compiler that preserves observable herald structure and physically induced correlations can produce materially different—and more reliable—logical-QEC conclusions than matched scalar error/erasure models across multiple photonic noise mechanisms.

The hypothesis remains deliberately broad. It is not restricted to temporal filtering, one fusion protocol, or a predetermined positive outcome. Idea 2 is the first falsification case: its simplified surface-code mapping predicted a temporal-filter advantage that disappeared under the protocol-specific six-ring mapping. Idea 3 asks whether that failure is part of a general, measurable abstraction problem.

The hypothesis should not be narrowed to one favorable device regime, error channel, or architecture without consultation and a separate publication-potential assessment.

## Compiler contract

$$
\text{physical parameters}
\rightarrow
\text{physical event branches}
\rightarrow
\text{effective faults + observable herald record}
\rightarrow
\text{QEC sampler and decoder}.
$$

Each compiled channel contains mutually exclusive branches, fault actions, erasures, decoder-visible heralds, physical provenance, and an explicit correlation statement. Hidden optical labels may be retained for validation, but the decoder-facing export removes them.

## Publication gates

The project continues only while evidence supports a general contribution. A strong result must eventually show at least one of the following across multiple physically distinct adapters:

1. retaining physical correlations changes a logical threshold, scaling trend, or hardware ranking;
2. a commonly used scalar reduction gives a statistically resolved wrong design decision;
3. one compiler contract accurately predicts both tractable optical reference cases and scalable QEC behavior;
4. the framework reveals a previously hidden logical-error mechanism with an experimentally testable mitigation.

A schema, software package, or single-adapter agreement is useful infrastructure but is not by itself a top-journal result.

## Current implementation

- A canonical, normalized branch schema with separate simulator and decoder views.
- Provenance and correlation metadata.
- Marginal diagnostics and a matched independent-target approximation.
- Total-variation and mutual-information measures for information lost during scalarization.
- A protocol-specific type-II temporal adapter imported from Idea 2.
- A reproducible first-adapter study over Idea 2's frozen 128-channel grid.
- A paired periodic QEC harness that compares full and marginal-matched channels using one frozen decoder model.
- A completed 48-condition pilot and 18-point held-out Stage 2 study.
- A heralded-biphoton-source adapter that distinguishes hidden vacuum,
  correct single-photon, and multiphoton-leakage histories behind one valid herald.
- A completed 80-condition Stage 3 source grid with verified truncation error
  below $10^{-12}$.
- An exact 135-condition four-mode Bell-measurement propagation study.
- A publication-potential assessment and explicit criteria for resuming the
  top-journal version.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe scripts\run_idea2_adapter_study.py
.\.venv\Scripts\python.exe scripts\run_stage2.py
.\.venv\Scripts\python.exe scripts\run_stage3.py
.\.venv\Scripts\python.exe scripts\run_stage3_fusion.py
```

## Layout

- `src/photonic_noise_compiler/schema.py`: canonical channel and branch contract.
- `src/photonic_noise_compiler/adapters/temporal_type_ii.py`: first physical adapter.
- `src/photonic_noise_compiler/diagnostics.py`: correlation-loss and scalarization diagnostics.
- `scripts/run_idea2_adapter_study.py`: frozen Idea 2 import study.
- `src/photonic_noise_compiler/qec.py`: paired periodic bulk QEC harness.
- `src/photonic_noise_compiler/adapters/heralded_source.py`: second physical adapter.
- `src/photonic_noise_compiler/stage3_study.py`: hidden-source-history grid.
- `src/photonic_noise_compiler/stage2_study.py`: frozen correlation-reduction comparison.
- `config/stage2.json`: predeclared pilot grid, held-out profiles, shots, and seeds.
- `HYPOTHESIS.md`: claims, falsifiers, and scope boundary.
- `ROADMAP.md`: staged validation plan and consultation gates.
- `LITERATURE.md`: primary-source motivation and novelty boundary.
- `RESULTS.md`: verified results and current interpretation.
- `STAGE3_MODEL.md`: source model, visibility semantics, and claim boundary.
- `PUBLICATION_ASSESSMENT.md`: evidence-based go/no-go judgment and resume gates.
- `results/idea2_adapter/`: generated first-adapter evidence.

## Claim boundary

The first adapter's corrected held-out QEC comparison found no significant
logical consequence. The second adapter produced hidden errors in apparently
valid full Bell records, reaching 1.7528% in the worst frozen condition, but the
unboosted primitive is not a viable unencoded six-ring operating point. These
results do not establish a general compiler advantage, threshold shift, hardware
ranking reversal, or experimental accuracy. Active expansion is paused under the
project's top-journal criterion.
