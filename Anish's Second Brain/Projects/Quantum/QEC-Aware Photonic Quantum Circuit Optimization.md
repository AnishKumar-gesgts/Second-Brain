## Core idea

Train a small photonic quantum circuit or photonic quantum neural network for a task while also optimizing how well it survives photon loss and can be recovered by a logical decoder. The project treats circuit accuracy, physical loss, logical error, and optical resource cost as connected objectives.

## Research question

Can a photonic model trained with a logical-error and resource-aware objective achieve lower post-decoding error than a model trained only for task accuracy?

## Candidate system

- A small binary task such as XOR, reduced binary Iris, or two digit classes.
- Dual-rail or Fock-state encoding.
- Beam splitters and phase shifters, with squeezing or displacement only if needed.
- Photon counting and an explicit optical-loss channel.
- A small encoded logical circuit or surface/fusion-based protection layer for evaluation.

## Software roles

- **PennyLane:** differentiable model definition, parameterized photonic circuit, and training through an optimizer such as PyTorch.
- **Strawberry Fields:** physically motivated optical simulation, Fock-state behavior, loss, detection, and fusion/resource-state statistics.
- **Stim:** scalable stabilizer or detector-error-model simulation for the larger error-correction experiment where the model can be represented in that form.
- **Decoder:** PyMatching or a custom decoder to estimate logical recovery performance.
- **Qiskit (optional):** independent validation of small encoded-qubit circuits and recovery operations; it is not required for the photonic simulation itself.

## Training objective

Start with classification loss, then add measurable robustness and resource terms:

$
\mathcal L_{total}=\mathcal L_{task}+\lambda P_L+\mu C_{photon}+\nu C_{circuit}.
$

Here, $P_L$ is the logical error probability after decoding, $C_{photon}$ can represent mean photon number or state-preparation cost, and $C_{circuit}$ can represent depth, modes, measurements, or other implementation cost. Sweep the coefficients rather than selecting one unexplained value.

## Feasible implementation plan

1. Build and test the unencoded PennyLane model on a small synthetic dataset.
2. Add Strawberry Fields loss and detector sampling; verify that the observed statistics match simple limiting cases.
3. Define a fixed encoded or detector-error-model interface between the photonic simulation and the decoder.
4. Establish baselines: task-only training, a fixed robust circuit, and a noise-aware objective without decoder feedback.
5. Add logical-error estimation, initially with Monte Carlo samples and a fixed decoder.
6. Compare task accuracy, physical loss, logical error, photon number, circuit depth, training stability, and inference cost.
7. Test multiple loss rates, detector imperfections, code sizes, random seeds, and held-out noise settings.

## Important scope boundary

End-to-end differentiable training through a sampled decoder may be difficult. A defensible first version can use alternating optimization, a surrogate logical-error penalty, finite-difference or parameter-shift estimates, or periodic decoder evaluation rather than claiming fully differentiable fault-tolerant training.

## Main risks

- Small photonic simulations may not scale to the code sizes needed for strong claims.
- Stim only applies directly where the modeled protection process has a compatible stabilizer/detector representation.
- A decoder score can be noisy; report confidence intervals and evaluate each trial against its known input.
- Improving logical error may simply increase photon number or circuit complexity, so resource-normalized comparisons are essential.

## Expected contribution

The strongest realistic contribution is an experimentally reproducible training objective and benchmark showing when decoder-aware photonic circuit optimization improves the accuracy–loss–resource trade-off. The project should avoid claiming a new fault-tolerant architecture unless the implementation and comparisons support that claim.
