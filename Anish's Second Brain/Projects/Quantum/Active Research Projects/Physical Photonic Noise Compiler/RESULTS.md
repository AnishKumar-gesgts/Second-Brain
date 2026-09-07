# Results

## Current status

Stages 1 and 2 are complete, and the source layer of Stage 3 is complete. The first adapter does **not** support a logical benefit from retaining its within-fusion `XX`/`ZZ` erasure correlation. The second adapter now demonstrates decoder-hidden vacuum and multiphoton histories behind a valid source herald, but its fusion-level and logical tests remain open.

## Stage 2 — held-out QEC reduction test

The Stage 2 harness represents two paired periodic 12-valent syndrome components. It preserves the published local assignment of `XX` outcomes to cubic-axis edges and `ZZ` outcomes to face-diagonal edges. Each physical fusion pairs one `XX` edge with one `ZZ` edge across the components, although the exact half-cell geometric crossing map and planar boundaries are not implemented.

The pilot covered 48 predeclared conditions: four detunings, three detector-jitter values, and four fixed gate regimes. Six profiles were fixed before pilot output and evaluated with 20,000 independent held-out shots at distances 3, 5, and 7.

An initial implementation appeared to produce five significant differences, but it decoded each physical channel with a separately generated PyMatching model. Because single-component rates also moved despite identical marginals, that result was diagnosed as decoder-model confounding and discarded. The corrected study sampled both channels while decoding both with the same frozen marginal model.

The corrected result was:

- **0 of 18** held-out profile-distance comparisons significantly favored the full correlated channel;
- **0 of 18** significantly favored the matched independent channel;
- **0 of 6** non-saturated comparisons showed a significant difference;
- component-level differences remained consistent with sampling variation;
- neither representation recovered distance suppression in the two non-saturated low-detuning profiles.

For the low-error no-filter profile, full versus independent any-component logical error was 0.17895 versus 0.18640 at distance 3, 0.21260 versus 0.22150 at distance 5, and 0.25865 versus 0.25860 at distance 7. All intervals overlapped. For the 220 ps low-error profile, the corresponding rates were 0.20985 versus 0.21550, 0.26720 versus 0.26670, and 0.34090 versus 0.32840; again, all intervals overlapped and both worsened with distance.

This result shows that a large event-distribution difference does not automatically become a logical-QEC difference. In this first adapter, the matched marginals capture the tested logical behavior within uncertainty under the shared decoder. That weakens any claim that within-fusion temporal-erasure correlation alone motivates the compiler, but it does not test the hidden, unheralded multiphoton-loss mechanism planned for the second adapter.

## Idea 2 adapter import

The first study compiled all 128 frozen type-II temporal channels from Idea 2: four detunings, four detector-jitter levels, seven finite gates, and no filtering. All 128 compiled channels conserved probability.

The physical channel contains joint `XX`/`ZZ` erasures: temporal rejection or photon loss removes both fusion outcomes in the same event. A matched independent-target model preserves the erasure marginal of each outcome but invents `XX`-only and `ZZ`-only erasure events that are absent from the physical channel.

| Gate | Joint-erasure range | Total-variation range from independent model |
|---|---:|---:|
| No filter | 1.00% | 1.98% |
| 450 ps | 1.00–1.02% | 1.98–2.02% |
| 220 ps | 1.94–7.61% | 3.81–14.06% |
| 140 ps | 10.79–25.09% | 19.25–37.59% |
| 40 ps | 64.11–74.15% | 38.34–46.02% |

At the most aggressive gates, the independent model assigns as much as 46.02% probability to synthetic partial-erasure combinations. This is a large difference between channel distributions, but it does not establish that a decoder's logical decision changes. Stage 2 must compare the full and reduced channels on one frozen QEC architecture.

## What this establishes

- The core schema can represent biased faults, joint erasures, observable heralds, provenance, assumptions, and hidden validation labels.
- Decoder-facing shot records omit physical-event labels, latent optical tags, and actual fault truth.
- The independent reduction preserves every per-target correct/flip/erasure marginal while deliberately removing cross-target correlation.
- The first adapter reproduces Idea 2's protocol-specific `ZZ`-only detuning faults and joint temporal-rejection/loss erasures.

## What this does not establish

The first-adapter result is not evidence that correlation preservation changes a threshold, distance scaling, hardware ranking, or logical error. It does not validate an experimental device.

## Next gate

The source portion of Stage 3 is now implemented. The next gate is an explicit
higher-Fock-space fusion circuit that propagates the compiled vacuum and
multiphoton inputs to detector outcomes and output faults. The project's
publication promise will be reassessed only after this second adapter receives
a fusion-level and held-out QEC comparison.

## Stage 3 source-layer result

The second adapter compiles a heralded biphoton source conditioned on one idler
photon-number-resolving count. It uses the exact conditional photon-number
distribution from Randles, Muñoz-Arias, and Sarovar,
[arXiv:2608.01549v1](https://arxiv.org/abs/2608.01549), rather than an assumed
two-photon mixture.

The frozen 80-condition grid found that a valid one-count herald concealed either
vacuum or a multiphoton signal state in **1.0194% to 18.5692%** of accepted events.
All correct and faulty histories produced the same decoder-visible record.

At the most adverse frozen condition
($\mu=0.20$, $\eta_s=0.85$, $\eta_{id}=0.85$):

- hidden vacuum probability: **14.2414%**;
- hidden multiphoton probability: **4.32785%**;
- total hidden-fault probability: **18.5692%**;
- fraction of valid heralds originating from two-pair generation with only one
  detected idler photon: **5.6454%**.

At the mildest condition
($\mu=0.01$, $\eta_s=0.99$, $\eta_{id}=0.99$), total hidden-fault probability
was still **1.0194%**, dominated by signal loss.

The initial eight-photon cutoff failed the frozen $10^{-12}$ convergence gate.
Increasing the cutoff to ten photons reduced the worst tail discrepancy to
$5.66\times10^{-15}$ without relaxing the tolerance.

This is a positive source/channel-level result, not yet a positive logical-QEC
result. The QEC harness intentionally refuses multiphoton leakage until a
specified fusion circuit provides a validated reduction.

## Stage 3 fusion-level result

The source distribution was propagated through a standard balanced four-mode
dual-rail Bell measurement with photon-number-resolving detection. The model
includes two remote qubits, applies detector loss at the Fock-state level, traces
lost photons, and reconstructs the remote state for every two-count record.

The ideal limit recovered 50% full Bell success, 50% one-parity fusion failure,
zero wrong-count rejection, and zero hidden error. Across the frozen 135-condition
grid, the full-success states were Bell-diagonal to a worst-case off-diagonal
magnitude of $1.32\times10^{-17}$. The resulting hidden fusion-bit errors
therefore did not require an additional Pauli-twirling assumption.

Hidden error conditioned on an apparently valid full Bell record ranged from
**0.000360001% to 1.752806%**. At the worst condition
($\mu=0.20$, $\eta_s=0.99$, $\eta_{id}=0.85$, $\eta_d=0.85$):

- full Bell-record probability: **32.5616%**;
- one-parity failure probability: **33.1765%**;
- wrong-count rejection probability: **34.2619%**;
- hidden `XX` error probability: **0.570741%** per attempted fusion;
- hidden retained-`ZZ` error during partial failure: **0.307466%** per attempt;
- hidden error among full Bell records: **1.752806%**.

This confirms the Idea 1 mechanism at the explicit fusion level: loss can reduce
a multiphoton history to a detector record that is also produced by the correct
two-photon sector. Photon-number resolution rejects many such histories but not
all of them.

## Final top-journal decision

The result is physically meaningful, but it is not yet a top-journal result.
The first adapter gave a held-out logical null result. The second adapter gives a
measurable hidden fusion error, but the unboosted Bell measurement's intrinsic
failure rate prevents a useful unencoded six-ring logical comparison. Existing
literature already establishes multiphoton-limited Bell discrimination and now
evaluates FBQC in the more demanding subthreshold-overhead regime.

A decisive continuation would require a validated boosted, encoded, or
repeat-until-success resource architecture and would constitute a substantially
larger project. Active work is therefore paused under the user's stated criterion.
The implementation remains valuable as infrastructure or as the basis of a
specialist paper or supervised collaboration. See `PUBLICATION_ASSESSMENT.md`.
