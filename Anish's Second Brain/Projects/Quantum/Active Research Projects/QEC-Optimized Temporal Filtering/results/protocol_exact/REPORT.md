# Protocol-specific six-ring bulk result

## Decision evidence

The predeclared study tested 16 detuning/jitter conditions. 0 passed the pilot confidence guard, and 0 showed a nonoverlapping-95%-interval improvement in the independent held-out comparison at distance 5.

The compiler now uses the published type-II mapping: detuning-induced partial distinguishability flips only the `ZZ` measurement outcome, while each six-ring syndrome graph assigns `XX` outcomes to cubic-axis edges and `ZZ` outcomes to face diagonals. Temporal rejection and loss erase both kinds of edge.

This is the decisive test for the current project hypothesis. A continuation is justified only if the benefit is broad across the predeclared physical grid and remains favorable as distance increases. A benefit confined to a small tuned corner is recorded but does not justify narrowing the original top-journal-scale claim.

The observed relative changes ranged from 1.82% better to 1.66% worse, with overlapping 95% Wilson intervals in every condition. The largest apparent improvement occurred in a saturated regime near 0.5 logical error. At 0.6 GHz the best finite gate was effectively no filtering and logical error worsened with distance; at 0.9 GHz and above, the distance-7 results approached the random 0.5 limit.

## Stopping decision

Stop this gate-optimization branch. The more favorable protocol-specific mapping still provides no broad, statistically supported, distance-improving advantage. Continuing would require a denser search, a hand-picked operating corner, or retreat to the earlier surface-code abstraction. Those changes would materially narrow the original hypothesis without meeting the intended impact standard.

## Claim boundary

This is a periodic bulk syndrome-graph calculation, not a planar logical block, a full six-ring resource-state circuit, a multimode Fock-space device simulation, an experiment, or hardware validation.
