# Stage 3 Fusion-Level Report

## Method

The study propagated two independently heralded, photon-number-imperfect inputs
through a balanced polarization-preserving Bell-measurement beamsplitter. Each
input photon was modeled as half of an ideal remote-photon Bell pair. The model
retained the full source distribution through ten photons, applied independent
detector loss, traced the lost output modes, and reconstructed the two remote
qubits for every two-count record.

Ideal-limit checks recovered 50% full Bell success, 50% one-parity failure, zero
wrong-count rejection, and zero hidden error. Hong-Ou-Mandel cancellation and
positive-semidefinite conditional density matrices were tested independently.

## Frozen grid

The 135 conditions combined five source pair probabilities, three signal
efficiencies, three idler/detector efficiencies, and three fusion-detector
efficiencies. No condition was selected after observing its logical behavior.

Hidden error conditioned on an apparently valid full Bell record ranged from
**0.000360001% to 1.752806%**.

The worst condition was
$\mu=0.20$, $\eta_s=0.99$, $\eta_{id}=0.85$, and $\eta_d=0.85$:

- full Bell-record probability: **32.5616%**;
- one-parity failure probability: **33.1765%**;
- wrong-total-count rejection: **34.2619%**;
- hidden `XX`-outcome error probability: **0.570741%** per attempted fusion;
- hidden retained-`ZZ` error during a partial failure: **0.307466%** per attempt;
- hidden error conditioned on full success: **1.752806%**.

Across the entire grid, the largest off-diagonal Bell-basis term for a full
success record was $1.32\times10^{-17}$. Thus, the full-success output is
Bell-diagonal to numerical precision and maps directly to stochastic fusion-bit
errors within this primitive.

## Boundary

This is an exact result for the stated remote-photon Bell-pair input model. It
does not validate a complete six-ring resource-state generator. The unboosted
primitive's intrinsic failure rate also prevents this channel from serving as a
useful unencoded six-ring operating point. A decisive logical study requires a
validated boosted, encoded, or repeat-until-success architecture.
