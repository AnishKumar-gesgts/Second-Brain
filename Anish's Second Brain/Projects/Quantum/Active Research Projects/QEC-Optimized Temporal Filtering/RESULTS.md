# Idea 2 Results

## Current verdict

**Stop this gate-optimization branch.** The first implementation supports the model-scoped hypothesis that a finite temporal gate can outperform both no filtering and an overly narrow, optical-fidelity-oriented gate in a rotated-surface-code proxy. Two architecture-aware studies do not reproduce that advantage, including the decisive protocol-specific study with the published type-II distinguishability mapping. The earlier result remains valid for its original abstraction, but it is not evidence of an architecture-scale six-ring benefit. Preserving a positive claim would now require materially narrowing the project to that abstraction or to a tuned operating corner, which fails the stated impact criterion.

## Decisive protocol-specific result

The final predeclared study removed the largest unresolved sensitivity assumption. In the published rotated type-II convention, partial distinguishability flips the `ZZ` fusion outcome with probability `(1-V)/2`; it does not randomly split the error between `XX` and `ZZ`. In each periodic six-ring syndrome graph, cubic-axis edges carry `XX` outcomes and face-diagonal edges carry `ZZ` outcomes. The implementation now applies the temporal error only to the `ZZ` diagonals while temporal rejection and photon loss erase both edge classes. [Chan et al.](https://doi.org/10.1103/PRXQuantum.6.020304), [Bartolucci et al.](https://doi.org/10.1038/s41467-023-36493-1)

The frozen grid covered detunings of 0.6, 0.9, 1.2, and 1.5 GHz and detector jitter of 0, 15, 30, and 60 ps. Seven finite gate widths plus no filtering were evaluated with 5,000 pilot shots at distance 5. The pilot-selected candidate and no-filter baseline then received independent 30,000-shot evaluations at distances 3, 5, and 7.

- **0 of 16** conditions passed the pilot confidence guard.
- **0 of 16** candidates significantly improved the held-out distance-5 result.
- Apparent relative changes ranged only from **1.82% better to 1.66% worse**, with overlapping 95% Wilson intervals throughout.
- The best numerical change, 1.82% at 1.2 GHz and zero jitter, occurred in a saturated regime: 0.49590 versus 0.50510.
- At 0.6 GHz and 15 ps jitter, the selected 450 ps gate was effectively no filter and produced 0.11750 versus 0.11743 at distance 5. Both worsened with distance (0.09420 to 0.13693 without filtering).
- At 0.9 GHz and 15 ps jitter, the selected 220 ps gate produced 0.44233 versus 0.44563 at distance 5, but both approached 0.5 by distance 7.
- At the original 1.2 GHz, 15 ps condition, the selected 140 ps gate produced 0.49973 versus 0.50007 at distance 5; both were random-limited.

This confirms the stopping condition. The protocol correction makes the model more favorable than the earlier all-edge sensitivity proxy, yet it still reveals no broad, statistically supported, distance-improving advantage. A denser gate search, a hand-picked mismatch range, or a claim limited to the earlier surface-code proxy would narrow the hypothesis without producing the exceptional architecture-level advantage sought here.

## Architecture-aware fusion-bulk upgrade

The new compiler represents one Bell fusion as a mutually exclusive event: correct, wrong `XX`, wrong `ZZ`, correlated wrong `XX/ZZ`, `XX`-only erasure, `ZZ`-only erasure, full temporal-rejection erasure, or loss. The QEC layer uses a periodic 12-valent cubic-with-diagonals syndrome graph and decodes a noncontractible logical winding with correlated PyMatching. This reproduces the published local six-ring facts that each fusion supplies one `XX` and one `ZZ` result and that each primal or dual bulk graph is 12-valent. It is still a proxy because it does not construct the exact stabilizer complex, half-cell crossing map, or planar logical boundaries. [Fusion-Based Quantum Computation](https://doi.org/10.1038/s41467-023-36493-1)

The frozen calibration used 20,000 shots per point and behaved at the scale reported for the six-ring hardware-agnostic model:

| Independent error per outcome | Distance 3 | Distance 5 | Distance 7 | Scaling |
|---:|---:|---:|---:|---|
| 0.5% | 0.02045 | 0.00745 | 0.00240 | Suppresses |
| 1.0% | 0.07435 | 0.07130 | 0.07385 | Approximately flat |
| 1.5% | 0.14745 | 0.20235 | 0.27270 | Grows |

This crossing near 1% is consistent with, but does not re-estimate, the published 1.07% marginal Pauli threshold. Periodic boundaries, a three-point calibration, and the proxy topology prevent treating it as a new threshold measurement.

The guarded study then tested detunings of 0.4, 0.6, and 1.2 GHz under wrong-`XX/ZZ` correlation fractions of 0, 0.5, and 1. Each condition used 5,000 pilot shots per candidate gate and independent 20,000-shot held-out evaluations at distances 3, 5, and 7.

- **0 of 9** conditions selected a finite gate through the pilot confidence guard.
- **0 of 9** pilot candidates produced a significant held-out distance-5 improvement.
- Candidate changes ranged from **5.5% better to 1.4% worse**, but every candidate interval overlapped the no-filter interval.
- The confidence-guarded policy therefore retained no filtering in all nine conditions.

At the original 1.2 GHz, 15 ps reference point with a 50% correlated-wrong assumption, the pilot candidate was 220 ps. Its held-out distance-5 error was 0.49585 (95% Wilson interval 0.48892–0.50278), compared with 0.50255 (0.49562–0.50948) without filtering. Both remained near the random 0.5 limit at distances 3, 5, and 7. The 40 ps control reduced the marginal unheralded wrong-outcome probability to 0.00325 but raised full erasure to 0.65095, leaving the distance-5 logical rate at 0.49525. This confirms that accepted-event fidelity alone is not a useful objective when the gate destroys most fusion outcomes.

The reference no-filter marginal wrong-outcome probability was 0.06871, far above the approximately 1% calibration crossing. A 25% intrinsic fusion-failure control converted part of that error into partial erasure but still produced 0.49890 logical error at distance 5. Missed-herald controls from 0% to 100% were also uninformative at the reference candidate because the logical rate was already saturated near 0.5.

### Earlier interim interpretation

This first architecture-aware proxy left the optical `XX`/`ZZ` split unresolved and therefore motivated the decisive protocol-specific calculation above. That calculation has now been completed and did not recover the advantage.

## Earlier surface-code-proxy result

Within the earlier proxy, robustness testing made the hypothesis conditional:

> When distinguishability-induced unheralded error is large enough and detector jitter remains sufficiently below the photon wavepacket duration, a pilot-selected temporal gate with erasure-aware decoding can reduce logical error and sometimes recover distance suppression. At low mismatch or high jitter, the correct policy is no filtering.

The result also requires sufficiently reliable erasure heralds. For the tested 1.2 GHz, 15 ps regime, the advantage is confirmed with up to 20% of physical erasure flags missed, inconclusive at 25%, and reverses by 30%.

The strongest result is the frozen distance-recovery extension at 1.2 GHz detuning. A 100,000-shot pilot selected a 140 ps half-width. An independent one-million-shot-per-point evaluation then measured:

| Setting | Distance 3 | Distance 5 | Distance 7 |
|---|---:|---:|---:|
| 140 ps QEC-selected gate | 0.105063 | 0.092045 | 0.081247 |
| No temporal filter | 0.111637 | 0.112645 | 0.111009 |
| Overly narrow 40 ps gate | 0.395270 | 0.435253 | 0.459925 |

At distance 5, the selected gate reduced logical error by 18.3% relative to no filtering (rate ratio 0.817; equivalently no filtering was 1.224 times worse). Its 95% Wilson interval was 0.091480–0.092613, compared with 0.112027–0.113266 without filtering. The intervals do not overlap.

More importantly, the selected gate recovered statistically significant distance suppression: the distance-7 rate was 0.773 times the distance-3 rate. The no-filter ratio was 0.994, and its distance-3 and distance-7 intervals overlap.

## First baseline

The deliberately harder 1.5 GHz stress case also selected a finite gate (110 ps) and reduced distance-5 logical error from 0.229372 to 0.166189. However, the selected-gate rate did not improve with distance. This supports the tradeoff hypothesis but is not a useful operating regime for scalable error suppression.

## Detuning and jitter robustness map

A second study tested 16 combinations of mean detuning (0.6, 0.9, 1.2, and 1.5 GHz) and detector jitter (0, 15, 30, and 60 ps). Each condition used 30,000 pilot shots per candidate gate and independent 200,000-shot held-out evaluations at distances 3, 5, and 7. A confidence guard retained no filtering unless the pilot gate's 95% interval was already below the no-filter interval.

- Filtering produced a statistically significant held-out distance-5 improvement in **6 of 16** regimes.
- All six were at detuning at least 1.2 GHz and jitter at most 30 ps.
- The relative improvements ranged from **10.4% to 31.1%**.
- Filtering recovered significant distance suppression in **4 of 16** regimes.
- No finite gate passed the pilot guard at 0.6 or 0.9 GHz, or at 60 ps jitter.
- The confidence-guarded policy caused **no significant held-out harm**.

This is more useful than the original single-point result: the project now predicts a boundary between regimes where filtering is beneficial and regimes where it should be disabled.

## Spectral-diffusion robustness

At the 1.2 GHz, 15 ps reference point, the benefit persisted after adding Gaussian shot-to-shot spectral diffusion:

| Spectral diffusion | Selected gate | Distance-5 improvement | Selected d7/d3 | No-filter d7/d3 |
|---:|---:|---:|---:|---:|
| 0.0 GHz | 140 ps | 17.7% | 0.779 | 0.994 |
| 0.2 GHz | 130 ps | 17.1% | 0.779 | 1.036 |
| 0.5 GHz | 130 ps | 15.6% | 0.842 | 1.083 |

The selected rule retained significant distance suppression at all three diffusion levels, whereas no filtering did not.

## Imperfect-herald robustness

A 500,000-shot-per-point follow-up converted a controlled fraction of physical erasures into unflagged maximally mixed faults while holding the 140 ps rule fixed:

| Missed erasure flags | Filtered distance-5 error | No-filter distance-5 error | Relative change | Filtered d7/d3 |
|---:|---:|---:|---:|---:|
| 0% | 0.092344 | 0.111396 | 17.1% better | 0.769 |
| 10% | 0.100138 | 0.112682 | 11.1% better | 0.824 |
| 20% | 0.107950 | 0.112660 | 4.18% better | 0.869 |
| 25% | 0.111112 | 0.112276 | 1.04% better, not significant | 0.892 |
| 30% | 0.115586 | 0.113098 | 2.20% worse | 0.912 |
| 50% | 0.129494 | 0.113966 | 13.6% worse | 1.006 |
| 100% | 0.158264 | 0.116428 | 35.9% worse | 1.167 |

At 20% missed flags, the filtered and no-filter 95% intervals remain separated. At 25% they overlap. At 30%, the filtered lower bound (0.114703) exceeds the no-filter upper bound (0.113979), so the harm is statistically resolved. The practical design rule for this fixed gate is therefore to require missed-herald probability below roughly 20–25%, or to re-optimize the gate jointly with herald reliability.

## Why the result occurs

For the 1.2 GHz extension, the selected 140 ps gate compiled to:

- heralded erasure probability: 0.118337;
- accepted, unheralded error probability: 0.053685;
- total acceptance probability: 0.881663.

Without filtering, heralded erasure fell to 0.009975 but unheralded error rose to 0.091613. The decoder benefits from moving some uncertainty into observable erasure locations. Hiding the erasure flags at the selected gate increased distance-5 logical error from 0.092045 to 0.158104, confirming that the improvement depends on usable side information rather than rejection alone.

The ideal-interference controls behaved correctly: at zero detuning, no filtering produced zero failures in one million distance-5 shots (95% upper bound 3.84e-6), while unnecessary filtering introduced erasure-driven failures. This rules out a generic benefit from filtering when distinguishability is absent.

## Validation completed

- All event tables conserve probability.
- The unfiltered temporal integral matches its closed form to 2.22e-16.
- A separate 500,000-sample physical Monte Carlo agrees with the integrated 60 ps event table within sampling uncertainty.
- Strawberry Fields gives the ideal Hong-Ou-Mandel output `P(2,0)=P(0,2)=0.5` and `P(1,1)=0` at both Fock cutoffs 3 and 4.
- The 2,001-point and 20,001-point temporal grids agree within the convergence tolerance.
- Twenty-two automated tests pass, including fusion-schema conservation, the protocol-specific `ZZ` map, 12-valent graph structure, `XX`/`ZZ` edge classification, exact circuit construction, useful herald information, and the fully missed-herald limit.
- Pilot selection and held-out evaluation use different frozen random seeds.
- The robustness selector uses a confidence guard to avoid choosing a finite gate from pilot-shot winner's-curse noise.
- Missed heralds are modeled as unflagged maximally mixed faults, with total erasure and accepted-error probabilities preserved exactly.

## Claim boundary

This is a complete first study of a Gaussian two-photon temporal primitive connected to a code-capacity rotated-surface-code benchmark. It is **not** a native fusion-based six-ring/RHG simulation, a circuit-level threshold estimate, or hardware validation. The single physical event table is applied once per data qubit; repeated syndrome rounds are otherwise ideal. PyMatching uses a graphlike decomposition and two-pass correlated matching for the heralded-erasure correlations, so its decoder model is still an approximation to a more general correlated photonic channel.

The 1.2 GHz point was chosen after a broad exploratory scan, but its gate width and final comparisons were selected only from the pilot and then tested with independent held-out samples. It should be reproduced across a predeclared mismatch/jitter grid before making a general design recommendation.

That grid has now been run, but it is still a grid within one Gaussian model. The numerical boundary should not yet be presented as a hardware specification.

## Stopping decision

Do not continue optimizing this hypothesis. The protocol-specific channel and local six-ring syndrome geometry have now been tested across the broad predeclared physical grid without a supported gain. A future project could study calibrated soft time information or a different fusion protocol as a genuinely new hypothesis, but that would be a new research direction—not a narrower rescue of this one.
