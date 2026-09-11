# Project Prompt: Reset Sufficiency at a Bosonic/Photonic-to-Qubit Interface

## Project status

New candidate from Iteration 24. Status: **NEEDS LITERATURE VALIDATION**; scientifically important but high risk.

The project must define a real out-of-code-space state and a physical reset map. Do not label ordinary loss or an immediately measured failed fusion as leakage without demonstrating persistence across rounds.

## Core research question

For one photonic-to-qubit interface, when does an out-of-code-space event require an explicit reset before the next syndrome round rather than an immediate erasure abstraction?

## Physical mechanism

Vacuum, multiphoton population, failed emission, or imperfect transduction may leave the intended dual-rail or qubit subspace. A later interaction or measurement can convert that latent state into a wrong outcome, while an actual reset can remove the memory. The project must distinguish persistent non-code-space population from a measurement-time erasure.

## Required framework roles

- **Strawberry Fields or validated Fock/mode simulator:** Track the selected optical interface and relevant number sectors.
- **Instrument layer:** Define the measurement, latent state, feed-forward, reset map, and time ordering operationally.
- **Stim:** Compare immediate erasure, reset-after-detection, no-reset persistence, and leakage-to-measurement-flip abstractions.
- **PyMatching:** Evaluate decoder consequences.
- **Direct small-code sampling:** Check whether the latent-state reduction is faithful.

Qiskit is optional only if an explicit qubit-interface circuit is needed.

## Minimum viable experiment

1. Choose one named dual-rail primitive and its detector/reset operation.
2. Define an operational truth table for vacuum, one-photon, and two-photon sectors.
3. Propagate those sectors through two syndrome rounds.
4. Compare the four reductions while holding detected marginal loss fixed.
5. Test whether the no-reset model produces a measurable logical difference.

## Full paper path

Add detector number resolution, source (g^{(2)}), transduction loss, reset latency, multiple schedules, distance scaling, and comparison with a known leakage-reduction protocol. Keep the interface and schedule fixed until the persistence claim is validated.

## Required novelty boundary

Review photonic/emitter interface papers and general leakage-QEC work. The only defensible novelty is a device-specific reset-sufficiency boundary for one named interface and schedule. Do not claim generally that photonic leakage is important.

## Main risks

- The chosen optical measurement resets or erases every out-of-space event immediately.
- “Leakage” is only bookkeeping rather than a persistent physical state.
- The interface is unavailable in the chosen simulator.
- The result duplicates general leakage literature.
- Different encodings or schedules change the answer entirely.

## Kill criteria

Kill if the primitive resets or erases every out-of-space event immediately, if all abstractions agree within uncertainty, or if the exact reset boundary is already reported for the same interface.

## Deliverable requirements

Provide the operational instrument definition, explicit state persistence evidence, reset map, abstraction comparison, held-out logical trials, and a conclusion limited to the selected interface and schedule.

## Source boundary

Derived from the “Candidate D — Reset sufficiency at a bosonic/photonic-to-qubit interface” section at the bottom of `Photonic QEC Research Ideation — Model Handoff Protocol (Unedited).md`. Do not merge this with the historical multiphoton-plus-loss idea unless the interface-specific reset question is the actual subject.
