# Phase 3 Notes - Hybrid Erasure-MWPM Decoder for Photonic Circuits

## Phase 3 question

Given the side information available in a photonic computer—especially heralded photon loss and fusion failure—are we decoding the resulting QEC data appropriately, and can a photonic-aware decoder reduce logical error relative to ordinary syndrome-only MWPM?

Phase 1 established the scalable Stim-to-PyMatching logical-memory baseline. [[Anish's Second Brain/Projects/Quantum/Phase 2 Notes - Decoder-Aware Photonic Hardware Allocation|Phase 2]] then asked where limited photonic hardware quality should be allocated at fixed cost. Phase 3 keeps the physical noise model and logical-memory benchmark explicit, but changes how the decoder uses the information produced by that hardware.

The primary comparison is

$$
\boxed{\text{standard MWPM}}
\quad\longrightarrow\quad
\boxed{\text{erasure-aware MWPM}}
\quad\longrightarrow\quad
\boxed{\text{peeling + MWPM}}.
$$

MCMC-CRW is **out of scope for now**. It should only be reconsidered if measured correlated or highly degenerate error structure exposes a limitation that erasure-aware matching and peeling cannot address without a more specialized decoder.

## 1. Why heralded photon loss becomes an erasure

For an ordinary unknown Pauli fault, the decoder must infer both where a fault occurred and what correction is consistent with the observed syndrome:

$$
\text{unknown Pauli fault}
\rightarrow
\text{unknown location + unknown error}.
$$

Heralded loss is different. A detector or fusion operation may report that the photon at a particular location was lost. The encoded quantum information at that location is no longer known, but the failed location is known:

$$
\text{erasure}
\rightarrow
\text{known location + unknown information}.
$$

Thus the photonic simulation should retain an erasure record

$$
\mathbf e=(e_1,e_2,\ldots,e_N),
\qquad
e_i=
\begin{cases}
1, & \text{location }i\text{ is known erased},\\
0, & \text{otherwise},
\end{cases}
$$

alongside the detector syndrome $\mathbf s$. A syndrome-only decoder receives $D_{\mathrm{MWPM}}(\mathbf s)$, whereas a photonic-aware decoder receives $D_{\mathrm{photonic}}(\mathbf s,\mathbf e)$. Throwing away $\mathbf e$ discards physically useful information.

## 2. How MWPM maps probabilities to weights

Stim produces detection events. In the matching graph, an edge represents a graphlike fault mechanism that could connect two detection events or connect one event to a boundary. MWPM searches for the lowest-cost set of edges whose boundary matches the observed detection events.

For an independent fault with probability $p_i$, a common log-likelihood-ratio weight is

$$
w_i
=
\log\left(\frac{1-p_i}{p_i}\right)
=
-\log\left(\frac{p_i}{1-p_i}\right).
$$

For $p_i<1/2$, a less likely fault has a larger positive cost and a more likely fault has a smaller cost. MWPM therefore searches for a low-cost, physically plausible explanation of the syndrome rather than merely the geometrically shortest path.

This already connects decoding to heterogeneous hardware. If two locations have different effective fault probabilities, $p_i\ne p_j$, they should not automatically receive identical matching weights. The weights must come from the documented physical-to-effective-channel model and be checked against sampled fault statistics.

## 3. How erasure information changes matching

Ordinary MWPM conditions on the syndrome alone:

$$
D_{\mathrm{MWPM}}(\mathbf s).
$$

Erasure-aware MWPM conditions on both the syndrome and the known loss pattern:

$$
D_{\mathrm{EA}}(\mathbf s,\mathbf e).
$$

If one candidate explanation passes through a heralded lost location while another requires unrelated faults at locations that were reported intact, the first explanation can be much more likely after conditioning on $\mathbf e$. Erasure awareness therefore changes the relevant edge likelihoods, graph structure, or preprocessing for that shot.

The implementation must not blindly assign one universal weight to every erased edge. The correct conditional model depends on what a reported loss means in the circuit, when the loss was localized, which checks or fusions it affects, and whether the effective detector-error mechanism remains graphlike. Perfect flags, missed flags, false-positive flags, and uncertain timing should be introduced as separate controlled cases.

This stage does not replace matching. It tests whether matching improves when it receives the photonic information that the hardware actually provides.

## 4. Peeling and why peeling + MWPM is the main hybrid

Peeling exploits the known support of an erasure pattern. Within an erased cluster, stabilizer constraints form a binary system over $\mathrm{GF}(2)$. For example,

$$
e_1\oplus e_2=s_1,
\qquad
e_2=s_2.
$$

The second constraint determines $e_2$, after which the first determines $e_1$. A peeling decoder repeatedly removes variables or checks that can be resolved in this way, progressively reducing the erased region. A spanning-forest or erased-cluster construction is typically used so redundant cycles do not create avoidable ambiguity.

Peeling alone is not sufficient for the intended mixed photonic noise model. Realistic shots can contain

$$
\text{heralded loss}
+
\text{unknown Pauli faults}
+
\text{measurement faults}
+
\text{fusion failures}.
$$

Peeling is designed to exploit the known erasure support; MWPM remains useful for sparse residual faults whose locations are unknown. The Phase 3 hybrid is therefore

$$
\boxed{
\text{heralded erasures}
\rightarrow
\text{peeling / erased-cluster preprocessing}
\rightarrow
\text{residual syndrome}
\rightarrow
\text{MWPM}
\rightarrow
\text{combined correction}
}.
$$

If peeling reaches an ambiguous cluster or stopping set, the decoder must record the condition and use a declared fallback rather than silently treating the partial result as a complete correction.

## Decoder ladder and experiment

Every decoder should be evaluated on the same recorded or fixed-seed fault samples:

1. **Standard MWPM:** the control condition; decode the detector syndrome without using the erasure record.
2. **Erasure-aware MWPM:** condition graph weights, structure, or preprocessing on known loss locations while retaining MWPM as the decoding engine.
3. **Peeling + MWPM:** resolve the inferable part of known erased clusters first, then send the residual syndrome to MWPM and combine both corrections.

Start with perfect erasure flags and independent mixed erasure/Pauli noise. Then add missed flags, false-positive flags, timing uncertainty, fusion-failure semantics, and controlled correlations one at a time. Stim remains the scalable circuit-level simulator; PyMatching supplies the graphlike MWPM baseline. Analytical models or targeted Strawberry Fields component/subsystem simulations may supply physically motivated local event probabilities, but the full six-ring/RHG architecture should not be simulated directly in Fock space.

For every sampled shot, score the decoder's predicted observable correction against the shot's known logical observable. Report

- logical error probability $P_L$ with uncertainty intervals;
- decoding runtime and memory;
- explicit peeling stopping/fallback rates;
- sensitivity to false and missed erasure flags;
- performance across loss/Pauli mixtures, code distance, logical basis, and controlled correlations; and
- the exact graphlike decomposition or approximation used for higher-order photonic faults.

## Current Phase 3 evidence

### Implementation status

The Phase 3 effective-channel benchmark is implemented in `Co-Design-Phase-3`. It preserves the Phase 1 conventions of a Stim rotated logical-memory experiment, both logical bases, $T=d$, per-shot scoring against the known observable, deterministic seeds, and Wilson 95% confidence intervals. It retains the Phase 2 six-ring component roles on data-qubit world lines, but it remains an effective-channel abstraction rather than a native six-ring FBQC detector circuit.

The implemented decoder ladder is:

1. **Standard MWPM:** discard the herald record and decode the ordinary detector syndrome.
2. **Erasure-aware MWPM:** use the active herald record to contract a deterministic spanning forest of graphlike erasure support, then apply MWPM to the residual syndrome. Redundant cycle edges are dropped as an explicit approximation.
3. **Peeling + MWPM:** peel only acyclic active erasure support. Cyclic or parallel support is recorded as a stopping set and the shot falls back to ordinary MWPM without applying a partial peeling correction.

The Stim detector error model uses `decompose_errors=True` and `approximate_disjoint_errors=True`. The current primary and smoke runs reported zero unsupported erasure segments. This is a tested graphlike reduction, not a claim that arbitrary higher-order photonic correlations have been decoded exactly.

**Implementation status: complete for the scoped six-ring/RHG effective-channel decoder benchmark. Scientific validation status: promising initial evidence, not yet a final multi-regime or native-architecture claim.**

### Primary perfect-flag validation

The primary Phase 3 run used

$$
p_{\mathrm{erase}}=0.03,
\qquad
p_{\mathrm{Pauli}}=0.001,
\qquad
T=d,
$$

with perfect erasure flags, no added fusion-failure channel, distances $d\in\{3,5,7\}$, both logical bases, and $100{,}000$ identical fault samples per decoder comparison at each point. The saved results are in `Co-Design-Phase-3/results/phase3-primary.csv` and its companion summary JSON.

| Distance | Basis | Standard MWPM $P_L$ | Erasure-aware MWPM $P_L$ | Peeling + MWPM $P_L$ |
|---:|:---:|---:|---:|---:|
| 3 | X | 0.01983 | 0.00557 | 0.00649 |
| 3 | Z | 0.02037 | 0.00720 | 0.00838 |
| 5 | X | 0.01489 | 0.00325 | 0.00456 |
| 5 | Z | 0.01401 | 0.00277 | 0.00391 |
| 7 | X | 0.00921 | 0.00094 | 0.00216 |
| 7 | Z | 0.00784 | 0.00073 | 0.00161 |

At this one mixed-noise point, both photonic-aware decoders lowered the logical-error estimate in both bases at every tested distance. All three decoder sequences also decreased from $d=3$ to $d=5$ to $d=7$. Because the decoders saw identical shots, paired comparisons are more informative than treating the estimates as independent: erasure-aware MWPM produced substantially more corrected baseline failures than newly introduced failures at all six points, and the same was true for peeling + MWPM.

The benefit has a clear computational cost. At $d=7$, standard MWPM required about $5.5\,\mu\mathrm{s}$ per shot, while the two Python-level photonic-aware preprocessors required roughly $0.44$-$0.47\,\mathrm{ms}$ per shot. Strict peeling's fallback rate also increased from about $0.9\%$ at $d=3$ to about $6.8\%$ at $d=7$, showing that larger active erased clusters create more stopping sets even though the hybrid still improved logical performance at this point.

This primary run is strong evidence that the retained herald record is useful in the implemented model. It is not yet a threshold study: it covers one erasure/Pauli mixture, one outer seed, perfect flags, and the effective rotated-memory mapping rather than a native FBQC circuit.

### Imperfect-flag smoke test

The August 14, 2026 smoke test exercised the complete nonideal-report path at $d=3$ with $1{,}000$ identical shots per decoder and basis:

$$
p_{\mathrm{erase}}=0.03,
\quad
p_{\mathrm{Pauli}}=0.001,
\quad
p_{\mathrm{fusion\ failure}}=0.01,
$$

$$
p_{\mathrm{missed\ flag}}=0.02,
\quad
p_{\mathrm{false\ positive}}=0.005,
\quad
p_{\mathrm{timing\ uncertainty}}=0.01.
$$

The saved outputs are `Co-Design-Phase-3/results/smoke.csv` and `Co-Design-Phase-3/results/smoke.summary.json`.

| Basis | Decoder | Failures / 1,000 | $P_L$ | Wilson 95% interval |
|:---:|:---|---:|---:|:---|
| X | Standard MWPM | 19 | 0.019 | $[0.0122,\ 0.0295]$ |
| X | Erasure-aware MWPM | 6 | 0.006 | $[0.00275,\ 0.0130]$ |
| X | Peeling + MWPM | 6 | 0.006 | $[0.00275,\ 0.0130]$ |
| Z | Standard MWPM | 33 | 0.033 | $[0.0236,\ 0.0460]$ |
| Z | Erasure-aware MWPM | 19 | 0.019 | $[0.0122,\ 0.0295]$ |
| Z | Peeling + MWPM | 22 | 0.022 | $[0.0146,\ 0.0331]$ |

On the paired samples, erasure-aware MWPM had 16 wins and 3 losses relative to standard MWPM in the X basis, and 19 wins and 5 losses in the Z basis. The exact two-sided McNemar values were $0.00443$ and $0.00661$, respectively. Peeling + MWPM had 16 wins and 3 losses in X and 16 wins and 5 losses in Z, with paired values $0.00443$ and $0.0266$. These paired counts support a decoder benefit on this fixed sample, even though the marginal Wilson intervals overlap in places.

Strict peeling encountered 18 stopping/fallback shots in each basis, a rate of $1.8\%$, and resolved about $1.71$ X-basis and $1.66$ Z-basis erasure edges per shot on average. The photonic-aware paths required about $52$-$55\,\mu\mathrm{s}$ per shot and roughly $88$-$93\,\mathrm{kB}$ of traced peak memory, compared with less than $1\,\mu\mathrm{s}$ and about $43$-$47\,\mathrm{kB}$ for standard MWPM.

The smoke test therefore establishes that the end-to-end decoder ladder remains operational and beneficial in this fixed-seed sample when fusion failures and imperfect reports are present. It does **not** isolate robustness to any one imperfection because missed flags, false positives, timing uncertainty, and fusion failures were enabled simultaneously. With only $1{,}000$ shots and one distance, it also cannot establish distance scaling, a general operating region, or a calibrated photonic-device advantage.

### Interpretation across Phases 1-3

- **Phase 1:** established the scalable circuit-level logical-memory pipeline and its $100{,}000$-shot distance-scaling criterion. Phase 3 reuses that simulation and per-shot grading discipline, so the decoder comparison is attached to a validated computational backbone. Numerical rates should not be compared across phases without matching every noise and herald setting.
- **Phase 2:** established that fixed-cost hardware allocation must be judged by decoded logical performance and that the physical layer should enter the scalable QEC simulation through explicit effective channels. Phase 3 supplies the previously missing decoder-side use of the herald information produced by those channels.
- **Phase 3:** demonstrates, within the current abstraction, that decoder choice is not a neutral downstream detail. A $20{,}000$-shot one-location-at-a-time screen changed the ranking from standard MWPM's leading order $[0,2,4,7,\ldots]$ to $[7,0,1,2,\ldots]$ for erasure-aware MWPM and $[7,1,0,2,\ldots]$ for peeling + MWPM. This supports the hypothesis that Phase 2 hardware sensitivity is decoder-dependent, but the ranking is a one-seed screening result rather than a finalized allocation.

The next project-level experiment is therefore not to combine the Phase 2 and Phase 3 point estimates informally. It is to rerun the equal-cost Phase 2 allocation comparison with the Phase 3 decoder fixed in advance, learn the allocation on separate samples, and grade the frozen hardware-decoder pair on held-out logical-memory trials.

### Remaining validation before a stronger claim

1. Sweep erasure/Pauli mixtures, both bases, and multiple distances with independent outer seeds.
2. Vary missed flags, false positives, timing uncertainty, and fusion failures one at a time before testing their interactions.
3. Add controlled correlation sweeps and record where the graphlike reduction becomes inadequate.
4. Rerun uniform, random, heuristic, sensitivity-based, and optimized Phase 2 allocations at equal cost under each fixed decoder.
5. Validate the effective six-ring mapping against a native architecture-specific detector circuit or tractable subsystem calculations.
6. Optimize the current Python preprocessing before treating its measured runtime as representative of a production decoder.

MCMC-CRW remains deferred. The present results do not yet expose a failure that requires expanding Phase 3 beyond erasure-aware matching and peeling.

## Connection to Phase 2: decoder-dependent hardware sensitivity

Phase 2 estimates the value of improving physical location $i$ through quantities such as

$$
S_i\approx-\frac{\Delta P_L}{\Delta q_i}
\qquad\text{and}\qquad
B_i\approx-\frac{\Delta P_L}{\Delta C_i}.
$$

These are not properties of the hardware alone. More completely,

$$
\boxed{
\frac{\partial P_L}{\partial q_i}
=
f(\text{hardware},\text{code},\text{decoder},\text{noise model})
}.
$$

A location that appears highly important under standard MWPM may become less important if erasure-aware matching or peeling handles its dominant loss mechanism well. Another location may then become the bottleneck. Rerunning the Phase 2 allocation study after Phase 3 could therefore change the logical-sensitivity map and the preferred equal-cost allocation.

The size of that change is an experimental question. If the improved decoder benefits all locations approximately uniformly, the Phase 2 ranking may change little. If it protects particular geometries or fault types disproportionately, the allocation may change substantially. A favorable result is the project hypothesis, not a conclusion to assume in advance.

## The end-to-end co-design loop

The complete loop is

$$
\boxed{\text{physical photonic parameters and resource allocation}}
\rightarrow
\boxed{\text{loss / fusion / Pauli effective channels}}
\rightarrow
\boxed{\text{QEC circuit and syndrome}}
\rightarrow
\boxed{\text{peeling + MWPM}}
\rightarrow
\boxed{P_L}
\rightarrow
\boxed{\text{updated hardware allocation}}
\circlearrowleft.
$$

The eventual comparison should hold the hardware/resource budget fixed and compare a baseline such as uniform hardware with standard MWPM against decoder-aware hardware allocation with a photonic-aware decoder. Only held-out logical-error results can establish whether joint optimization outperforms the baseline.

Phase 3 is therefore not isolated decoder tuning. It closes the information path from photonic failure reports to logical performance, after which [[Anish's Second Brain/Projects/Quantum/Phase 2 Notes - Decoder-Aware Photonic Hardware Allocation|Phase 2]] can be rerun with the decoder included in the sensitivity calculation. Repeating that alternating update—and finally optimizing both sides within [[Ideas/End-to-End Differentiable Photonic Fault-Tolerance Co-Design|the end-to-end co-design framework]]—is the larger project direction.

## Technical boundaries

- “Use erasure information in MWPM” is not by itself a novelty claim. The contribution must be tied to the six-ring fusion-based/RHG setting, explicit herald and fusion semantics, calibrated mixed noise, or a measured regime where the hybrid provides a reproducible benefit.
- PyMatching is most natural for graphlike detector-error models in which one elementary mechanism produces at most two detection events. Higher-order fusion or resource-state correlations require documented decomposition, custom preprocessing, or later comparison with a correlation-aware method.
- MCMC-CRW remains outside the Phase 3 implementation and benchmark plan unless the measured error structure justifies revisiting it.

## Connections

- [[Anish's Second Brain/Projects/Quantum/Phase 1 Notes - Surface-Code Memory and Simulation Fundamentals|Phase 1 Notes - Surface-Code Memory and Simulation Fundamentals]]
- [[Anish's Second Brain/Projects/Quantum/Phase 2 Notes - Decoder-Aware Photonic Hardware Allocation|Phase 2 Notes - Decoder-Aware Photonic Hardware Allocation]]
- [[Ideas/End-to-End Differentiable Photonic Fault-Tolerance Co-Design|End-to-End Differentiable Photonic Fault-Tolerance Co-Design]]
- [[Anish's Second Brain/Projects/Quantum/Phase 4 Notes - Learned Decoder Integration and Evaluation|Phase 4 - Learned Decoder Integration and Evaluation]]

#quantum-photonics #qec #decoder #erasure #mwpm #peeling
