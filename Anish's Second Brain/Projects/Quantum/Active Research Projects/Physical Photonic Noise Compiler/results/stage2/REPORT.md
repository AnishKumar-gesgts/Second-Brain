# Stage 2 QEC Reduction Result

## Verdict

The first adapter's within-fusion erasure correlation changes the physical event distribution but did not significantly change the tested logical-QEC results when both channels used the same frozen marginal decoder.

The pilot covered 48 predeclared detuning, detector-jitter, and gate conditions. Six profiles were fixed before reading pilot output and evaluated at distances 3, 5, and 7 with 20,000 held-out shots per model and distance.

- 0 of 18 comparisons significantly favored the full correlated channel.
- 0 of 18 significantly favored the matched independent channel.
- 0 of 6 non-saturated comparisons showed a significant difference.

## Method correction

An earlier run used a separately generated PyMatching model for each sampled channel and appeared to show five significant differences. That implementation also shifted single-component logical rates even though the physical channels had identical single-component marginals. The apparent effect was therefore decoder-model confounding, not clean evidence of physical correlation. It was discarded.

The corrected study decoded samples from both physical channels with the same frozen marginal decoder. Component-level differences then remained consistent with sampling variation, and the apparent held-out signal disappeared.

## Interpretation

Channel-level total variation reached 46.02% for aggressive temporal gates, yet the tested logical behavior was reproduced by matched target marginals within uncertainty. This demonstrates why the compiler must validate reductions at the logical layer rather than equating a large event-table difference with architectural importance.

The result is negative for this correlation mechanism, not for the complete Idea 3 hypothesis. The second adapter tests a different failure mode: multiphoton emission followed by loss can create an apparently valid detector record containing a hidden unheralded fault.

## Claim boundary

The architecture is a paired periodic 12-valent bulk proxy with the published local `XX`-axis and `ZZ`-diagonal semantics. The cross-component pairing is deterministic but does not reproduce the exact half-cell crossing geometry or planar logical-block boundaries. This is not a six-ring threshold estimate or hardware validation.
