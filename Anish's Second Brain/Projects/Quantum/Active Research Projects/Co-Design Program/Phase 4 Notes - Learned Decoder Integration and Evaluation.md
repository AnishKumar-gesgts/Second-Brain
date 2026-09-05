# Phase 4 Notes - Learned Decoder Integration and Evaluation

## Goal

Phase 4 asks whether a decoder that learns the structure of the photonic noise can reduce logical error beyond the fixed [[Anish's Second Brain/Projects/Quantum/Phase 3 Notes - Hybrid Erasure-MWPM Decoder for Photonic Circuits|Phase 3 Peeling + MWPM baseline]]. The experiment keeps the physical faults and held-out trials fixed while changing only how the decoder interprets the available information.

The Phase 3 pipeline is

$$
\text{photonic parameters}
\rightarrow
\text{effective physical errors}
\rightarrow
\text{QEC simulation}
\rightarrow
\text{Peeling + MWPM}
\rightarrow
P_L.
$$

Phase 4 adds a learned residual decision without removing the reference decoder:

$$
\text{Peeling + MWPM prediction}
\oplus
f_\phi(S,\mathbf q)
\rightarrow
\text{logical prediction}.
$$

Here, $S$ is the syndrome and $\mathbf q$ contains photonic side information. The learned model predicts whether the baseline logical decision should be flipped. This first implementation is deliberately a small, auditable model rather than a claim that a particular neural architecture is optimal.

## Scientific question

> Given the same simulated physical faults, does information about the photonic hardware's actual noise distribution improve the logical decision beyond Peeling + MWPM?

This is stronger than asking whether a generic machine-learning model can beat MWPM. The relevant evidence is whether physical-layer information adds decoding value under controlled held-out evaluation.

## Preserve Peeling + MWPM as the baseline

Peeling + MWPM remains the reference decoder for every physical configuration:

$$
P_L^{\mathrm{Peeling/MWPM}}.
$$

The learned decoder is evaluated on the same held-out faults and logical labels. Keeping the baseline fixed prevents a decoder change from being confused with a hardware-allocation change and preserves the Phase 1-3 comparison ladder.

## Decoder inputs and target

For each simulated shot, retain

$$
(S,\mathbf h,\mathbf q,y),
$$

where:

- $S$ is the ordinary QEC detector syndrome;
- $\mathbf h$ is the heralded loss and fusion-failure record;
- $\mathbf q$ describes the physical configuration, including erasure, Pauli, fusion-failure, and flag-quality parameters; and
- $y$ is the known logical observable from simulation.

The initial learned target is the baseline residual logical class

$$
r = y \oplus \hat y_{\mathrm{Peeling/MWPM}}.
$$

Predicting $r$ keeps the fixed decoder in the loop and makes the learned model responsible only for a logical-class correction. The scientific metric is held-out logical error rate $P_L$, not training accuracy or reconstruction of every physical error bit.

## Required control experiment

Evaluate all three paths on identical held-out shots:

$$
\begin{aligned}
A &: \text{Peeling + MWPM},\\
B &: \text{learned residual decoder using syndrome only},\\
C &: \text{learned residual decoder using syndrome + photonic information}.
\end{aligned}
$$

The key co-design comparison is $C$ versus $B$. If $C$ improves reproducibly, the physical-layer information itself contains useful decoding information. Comparisons against $A$ show whether either learned path improves the established baseline.

## Training and leakage controls

Because simulation exposes the true logical observable, it can generate labeled data directly. Training and evaluation must use independent sampler seeds, and no held-out labels may enter feature construction, fitting, threshold selection, or model selection.

The first experiment should use one declared nonuniform effective noise family. Training should cover nearby physical configurations rather than repeating one constant configuration, because point-level hardware features cannot be learned when they never vary. The model is then frozen and evaluated at unseen configurations

$$
\theta_0 + \Delta\theta.
$$

Relevant variations include photon loss, Pauli error, fusion failure, missed flags, false positives, timing uncertainty, and spatially nonuniform erasure scales.

## Initial implementation

The Phase 4 repository should preserve the Phase 3 Stim/PyMatching circuit, herald handling, Peeling + MWPM decoder, both logical bases, $T=d$, exact per-shot grading, and graphlike-approximation disclosures. Add:

1. a reproducible dataset generator that records syndrome, heralds, physical features, baseline predictions, and true logical labels;
2. a small NumPy learned residual classifier with feature standardization and regularization;
3. separate syndrome-only and syndrome-plus-photonic feature paths;
4. a held-out benchmark that evaluates all three decoders on identical shots; and
5. serialized training metadata, confidence intervals, paired win/loss counts, and explicit non-claims.

No additional machine-learning dependency is necessary for this first integration. A more expressive neural, graph, or correlation-aware decoder should be added only after the data interface and held-out comparison are verified.

## Generalization and success criteria

Do not infer an advantage from one seed or one point estimate. A stronger Phase 4 result should:

- reproduce across independent training and evaluation seeds;
- include both logical bases and multiple distances with $T=d$;
- test multiple mixed-noise and nearby unseen physical configurations;
- report Wilson $95\%$ confidence intervals and paired comparisons;
- compare $C$ with both $A$ and $B$;
- remain useful under modest physical drift; and
- show a distance-scaling trend before any fault-tolerance claim.

The principal ratios are

$$
R_{C/A}=\frac{P_L^{\mathrm{learned+photonic}}}{P_L^{\mathrm{Peeling/MWPM}}}
\qquad\text{and}\qquad
R_{C/B}=\frac{P_L^{\mathrm{learned+photonic}}}{P_L^{\mathrm{learned syndrome-only}}}.
$$

Values below $1$ are favorable point estimates, but uncertainty and paired outcomes determine whether they support a claim.

## Scope boundary

Phase 4 does not jointly optimize the photonic hardware and decoder. The physical configuration is sampled from a declared training family, the learned decoder is fitted and frozen, and the comparison is made on held-out trials. Whether a learned decoder should later enter the hardware-allocation loop depends on the physical model and on evidence that it adds value beyond Peeling + MWPM.

The current circuit remains a six-ring/RHG effective-channel abstraction. It is a circuit-level simulation, not a native fusion-based detector circuit, full-architecture Fock-space simulation, calibrated device prediction, or hardware validation.

## Current Phase 4 evidence

The first predeclared learned-decoder study covered distances $d=3,5,7$, both logical bases, and three independent training/evaluation seed pairs. Each run trained on $30{,}000$ shots across erasure rates $0.02$, $0.03$, and $0.04$, used a training-only calibration split, and graded the frozen decoders on $100{,}000$ held-out shots at erasure rate $0.035$, Pauli rate $0.001$, and fusion-failure rate $0.01$. The complete evaluation therefore contained $1.8$ million held-out shots.

Peeling + MWPM produced $12{,}945$ failures, or $0.71917\%$. The syndrome-only learned residual produced $13{,}147$ failures, or $0.73039\%$, and the syndrome-plus-photonic learned residual produced $13{,}148$ failures, or $0.73044\%$.

Against Peeling + MWPM, the photonic learned model had only $15$ paired wins and $218$ paired losses, with a pooled exact two-sided McNemar value of $2.43\times10^{-47}$ favoring the baseline. Against the syndrome-only learned control, it had $159$ wins and $160$ losses, with $p=1.0$. The initial linear learned-decoder implementation therefore does **not** support either a learned-decoder advantage or an added benefit from the supplied photonic features.

The baseline remained distance-suppressing in both logical bases. Its pooled logical error decreased from $1.1107\%$ to $0.7163\%$ to $0.4490\%$ for the $X$ memory and from $1.0467\%$ to $0.6150\%$ to $0.3773\%$ for the $Z$ memory as distance increased from $3$ to $5$ to $7$. This ordering held in every outer seed and supports the continued use of the Phase 3 simulation backbone.

This null result does not falsify the broader decoder-aware co-design hypothesis. The training family varied global erasure probability but kept location-specific quality uniform, while Peeling + MWPM already consumed the herald record. The remaining logical residual was rare and structurally nonlinear, and the first model was only a linear classifier over flattened features.

The learned model in this study is a **logical residual classifier**: it predicts whether to flip the final Peeling + MWPM logical decision. It is not a model that reconstructs every physical error location or directly performs location-by-location decoding.

The Phase 4 study also did not decode a frozen Phase 2 optimized allocation. It used a fixed rotated-memory circuit mapped onto effective six-ring roles, with uniform location-specific quality scales. The training variation was global rather than a decoder-aware, cost-optimized spatial allocation. The experiment therefore did not supply the learned model with the heterogeneous location-quality structure that the broader co-design hypothesis ultimately concerns.

Later analytical or Strawberry Fields component and small-subsystem modeling may produce more realistic heterogeneous, correlated, or analog effective channels for Stim. Those channels could create useful decoder side information, but they could also show that Peeling + MWPM remains close to optimal. Greater physical realism creates an opportunity for learned decoding; it does not guarantee that a learned decoder will win.

Because the decoder target and useful feature structure may change substantially when the physical model is revised, further hyperparameter or architecture optimization against the present uniform effective-channel abstraction is deferred. Revisit learned-decoder design only after the physical channels and architecture-specific mapping are stable enough to define the information that the decoder should consume.

**Phase 4 status: complete as a scoped learned-decoder feasibility study with a null result.** It establishes the data interface, controls, held-out evaluation, and decision boundary. It does not establish an ML advantage, and no such advantage is required to close this phase honestly.

## Connection to the complete project

Phase 4 changes the decoder portion of the broader co-design pipeline:

$$
\theta
\rightarrow
\text{effective noise}
\rightarrow
\text{QEC}
\rightarrow
\boxed{\text{decoder aware of }\theta}
\rightarrow
P_L.
$$

Stim and PyMatching are not naturally differentiable. The eventual closed loop may therefore use alternating optimization, finite differences, Bayesian optimization, or a differentiable surrogate rather than assuming that gradients pass directly through sampled faults and discrete decoder decisions.

## Connections

- [[Anish's Second Brain/Projects/Quantum/Phase 1 Notes - Surface-Code Memory and Simulation Fundamentals|Phase 1 Notes - Surface-Code Memory and Simulation Fundamentals]]
- [[Anish's Second Brain/Projects/Quantum/Phase 2 Notes - Decoder-Aware Photonic Hardware Allocation|Phase 2 Notes - Decoder-Aware Photonic Hardware Allocation]]
- [[Anish's Second Brain/Projects/Quantum/Phase 3 Notes - Hybrid Erasure-MWPM Decoder for Photonic Circuits|Phase 3 Notes - Hybrid Erasure-MWPM Decoder for Photonic Circuits]]
- [[Ideas/End-to-End Differentiable Photonic Fault-Tolerance Co-Design|End-to-End Differentiable Photonic Fault-Tolerance Co-Design]]
- [[Ideas/Analog-Information Decoding Across CV-DV Photonic QEC|Analog-Information Decoding Across CV-DV Photonic QEC]]

#quantum-photonics #qec #learned-decoder #mwpm #co-design
