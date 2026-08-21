# Analog-Information Decoding Across CV-DV Photonic QEC

[[Ideas]]

## Central question

How much logical information is lost when continuous-variable photonic syndrome measurements are converted too early into binary error/no-error decisions?

## Background

Continuous-variable photonic codes such as GKP-type encodings can produce continuous measurement values. Instead of reducing a measurement immediately to

$$
s_i \in \{0,1\},
$$

retain

$$
x_i \in \mathbb{R}
$$

and infer

$$
P(E_i \mid x_i).
$$

That likelihood can be passed into an outer discrete-variable QEC code.

## Core pipeline

$$
\text{CV measurement}
\rightarrow
\text{soft likelihood}
\rightarrow
\text{outer DV code}
\rightarrow
\text{logical correction}.
$$

### Hard versus soft decoding

Hard decoding converts $x_i \rightarrow s_i$ and gives the outer decoder only a binary syndrome.

Soft decoding retains $x_i \rightarrow P(E_i\mid x_i)$ and uses confidence to modify decoder weights. For an MWPM-style decoder, a natural weight is schematically

$$
w_i \propto -\log\left(\frac{p_i}{1-p_i}\right).
$$

## Main hypothesis

A concatenated CV-DV architecture performs better when the outer decoder receives continuous or soft reliability information rather than a thresholded binary syndrome. Compare

$$
\frac{P_L^{\mathrm{soft}}}{P_L^{\mathrm{hard}}}.
$$

If this is substantially below $1$ over realistic noise regimes, the project shows that hard discretization discards useful fault-tolerance information.

## Toolchain

1. **Strawberry Fields:** CV/GKP states and noisy analog measurements.
2. **PennyLane:** thresholds, likelihood mappings, or physical-parameter optimization.
3. **Stim:** outer stabilizer-code simulation.
4. **PyMatching:** likelihood-dependent decoding weights.

## Extensions

Optimize $x_i\mapsto p_i$; study likelihood calibration error and non-Gaussian noise; compare hard, soft, and partially quantized information; determine the analog precision actually needed; and optimize CV and DV decoder layers jointly.

## Connections

- [[End-to-End Differentiable Photonic Fault-Tolerance Co-Design]] could optimize the physical CV layer and outer decoder jointly.
- [[Correlated Photon-Loss Burst QEC]] could combine correlated loss with analog syndrome information.
- [[Anish's Second Brain/Projects/Quantum/Phase 2 Notes - Decoder-Aware Photonic Hardware Allocation|Phase 2 - Decoder-Aware Photonic Hardware Allocation]] could allocate better squeezing or detection where soft information has high logical value.

This is the idea that likely requires the most background study: CV/GKP measurement modeling, likelihood-based decoding, and the CV-to-DV interface all need to be understood together.

#continuous-variable #gkp #quantum-photonics #qec #soft-decoding
