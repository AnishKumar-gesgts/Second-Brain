# Fusion-bulk proxy result

## Verdict

The architecture-aware upgrade **does not support** carrying the earlier surface-code-proxy improvement into the six-ring bulk model. None of the 9 predeclared detuning/correlation conditions passed the pilot confidence guard, and the independent held-out comparison found 0 significant candidate improvements and 0 significant harms.

The negative result has a direct mechanism. The six-ring bulk calibration changes from distance suppression near 0.5% independent error per fusion outcome to distance growth near 1.5%, with a crossing around 1%. At the original 1.2 GHz reference condition, the compiled wrong-outcome probability is several times larger than that scale even after filtering. Narrow gates reduce wrong outcomes but replace them with full XX/ZZ erasures quickly enough to saturate the logical winding measurement.

## What this establishes

- The new compiler preserves mutually exclusive correct, wrong-XX, wrong-ZZ, correlated-wrong, partial-erasure, full-rejection, and loss branches.
- The scalable benchmark uses a periodic 12-valent cubic-with-diagonals syndrome graph and decodes a noncontractible logical winding with MWPM.
- Pilot selection and held-out evaluation use frozen independent seeds and Wilson intervals.
- The unknown optical split between XX-only, ZZ-only, and correlated wrong outcomes is exposed as a sensitivity axis rather than fixed implicitly.
- The 40 ps control and 25% intrinsic fusion-failure control both test whether apparent fidelity gains are only produced by erasing too many outcomes.

## What this does not establish

This is not yet a native six-ring/RHG logical block. The code does not construct the six-qubit resource stabilizers, the exact half-cell-shifted primal/dual crossing map, or published planar boundaries from the fusion complex. It also does not derive the XX/ZZ split from a multimode type-II fusion calculation. Therefore, the result is evidence that the earlier gain is fragile under a threshold-calibrated architecture-aware mapping, not a six-ring threshold or hardware-performance claim.

At the 1.2 GHz reference condition, the 40 ps control converts 65.1% of fusion events into full erasure and remains saturated near 0.5 logical error per syndrome graph. A 25% intrinsic fusion-failure control is also saturated. Missed-herald sensitivity is not identifiable at this reference point because every tested herald quality lies within the same already-random regime.
