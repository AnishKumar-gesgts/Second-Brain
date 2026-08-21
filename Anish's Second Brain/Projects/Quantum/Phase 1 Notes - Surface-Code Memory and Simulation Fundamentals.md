# Phase 1 Notes - Surface-Code Memory and Simulation Fundamentals

[[Anish's Second Brain/Projects/Quantum/Phase 2 Notes - Decoder-Aware Photonic Hardware Allocation|Phase 2 Notes - Decoder-Aware Photonic Hardware Allocation]]
[[End-to-End Differentiable Photonic Fault-Tolerance Co-Design]]

## Purpose of Phase 1

Build and validate a uniform-noise surface-code memory experiment before adding photonic hardware allocation or optimization. The baseline must correctly simulate physical faults, extract syndromes, decode them, and estimate logical error rates with uncertainty.

The basic pipeline is

$$
\text{surface-code circuit}
\rightarrow \text{physical faults}
\rightarrow \text{detection events}
\rightarrow \text{decoder}
\rightarrow \text{logical failure estimate }P_L.
$$

The optimizer comes later. It will propose photonic designs and use this pipeline to judge their logical performance.

## 1. Physical and logical qubits

A physical qubit is one hardware degree of freedom. A logical qubit is quantum information encoded nonlocally across many physical data qubits.

For a rotated surface code of distance $d$,

$$
N_{\mathrm{data}}=d^2,
\qquad
N_{\mathrm{ancilla}}=d^2-1.
$$

Thus $d\sim\sqrt{N_{\mathrm{data}}}$ because the code is laid out in two spatial dimensions. This is a geometric relation for this code family, not a universal QEC law.

Distance $d$ is the minimum weight of an undetectable logical operator. Ideally, a distance-$d$ code can correct up to

$$
t=\left\lfloor\frac{d-1}{2}\right\rfloor
$$

physical errors under the assumed noise model.

## 2. States, amplitudes, and eigenstates

A qubit state is

$$
|\psi\rangle=\alpha|0\rangle+\beta|1\rangle,
\qquad
|\alpha|^2+|\beta|^2=1.
$$

$|0\rangle$ does not have “no amplitude.” It has amplitude $1$ on $|0\rangle$ and $0$ on $|1\rangle$:

$$
|0\rangle=1|0\rangle+0|1\rangle.
$$

An eigenstate of an operator $A$ satisfies

$$
A|\psi\rangle=\lambda|\psi\rangle,
$$

where $\lambda$ is the eigenvalue. A $+1$ eigenstate obeys $A|\psi\rangle=|\psi\rangle$.

Examples:

$$
Z|0\rangle=+|0\rangle,
\qquad
Z|1\rangle=-|1\rangle,
$$

so $|0\rangle$ and $|1\rangle$ are the $+1$ and $-1$ eigenstates of $Z$. Likewise,

$$
|+\rangle=\frac{|0\rangle+|1\rangle}{\sqrt2},
\qquad
|-\rangle=\frac{|0\rangle-|1\rangle}{\sqrt2},
$$

are the $+1$ and $-1$ eigenstates of $X$.

Although $Z|1\rangle=-|1\rangle$ adds a minus sign, this is only a global phase for the isolated state $|1\rangle$. In a superposition, however, $Z$ changes the relative phase:

$$
Z\left(\alpha|0\rangle+\beta|1\rangle\right)
=\alpha|0\rangle-\beta|1\rangle.
$$

## 3. Pauli operators and Pauli noise

The Pauli errors are:

- $X$: bit flip, $X|0\rangle=|1\rangle$ and $X|1\rangle=|0\rangle$;
- $Z$: phase flip, changing the relative phase between basis components;
- $Y$: both bit- and phase-error components, up to global phase;
- $I$: no error.

A depolarizing Pauli channel may apply

$$
I,X,Y,Z
$$

with probabilities $1-p,p/3,p/3,p/3$. Real hardware noise need not literally be a random Pauli operation, but Pauli noise is efficient to simulate in Clifford/stabilizer circuits. Heralded photon loss must be represented separately rather than being silently converted into Pauli noise.

### How the Phase 1 noise model is applied

The simulation has two distinct layers of variation. First, the sweep runs many
independent parameter points, combining each selected distance, logical basis,
erasure probability, and Pauli-noise probability. Second, within each point,
many independent shots are sampled. A shot is one complete memory experiment:
state preparation, repeated syndrome-extraction rounds, and final logical
measurement.

The erasure probability $p_{\mathrm{erase}}$ is a separate heralded-erasure
channel. At the beginning of every syndrome round, each data qubit is subjected
to an independent `HERALDED_ERASE` event with probability
$p_{\mathrm{erase}}$. If it occurs, the qubit is erased and the event location
is exposed to the decoder as herald information. Thus $p_{\mathrm{erase}}$ does
not mean that a Pauli error was detected and relabeled as an erasure; it is the
probability of a distinct, known-location loss event.

The Pauli probability $p_{\mathrm{pauli}}$ controls an unheralded,
circuit-level background model. Stim applies it in the generated surface-code
circuit as:

- depolarizing noise after Clifford gates;
- measurement-result flips before measurements; and
- Pauli flips after reset operations.

Consequently, Pauli faults can occur throughout a shot, including between
successive stabilizer-measurement rounds. The model does not insert a separate
independent channel immediately before every gate or simulate a microscopic
continuous-time error process. For a Clifford circuit, a Pauli fault before a
Clifford gate can often be commuted through the gate and represented as an
equivalent transformed Pauli fault after it, which motivates the post-Clifford
convention. This is a controlled circuit-level approximation, not a complete
hardware noise characterization.

Stim both constructs and samples the noisy circuit. PyMatching does not add
noise; it receives the detector events (including erasure heralds) and predicts
the logical correction. The prediction is compared with Stim's hidden actual
logical observable for that same shot to estimate the logical-error rate.

## 4. Operators as gates versus observables

As a gate, $X$ transforms a state by swapping its computational-basis amplitudes:

$$
X(\alpha|0\rangle+\beta|1\rangle)
=\beta|0\rangle+\alpha|1\rangle.
$$

As an observable, $X$ defines the measurement basis $\{|+\rangle,|-\rangle\}$. An $X$ measurement does not mean “apply $X$ and observe the change.” It asks whether the state is aligned with the $+1$ or $-1$ eigenstate of $X$.

For a general state,

$$
\langle X\rangle=2\operatorname{Re}(\alpha^*\beta),
\qquad
\langle Y\rangle=2\operatorname{Im}(\alpha^*\beta),
\qquad
\langle Z\rangle=|\alpha|^2-|\beta|^2.
$$

Therefore, $Z$ measures computational-basis population imbalance, while $X$ and $Y$ reveal complementary phase-sensitive components. For equal-amplitude states, $X$ perfectly distinguishes relative phases $0$ and $\pi$:

$$
|+\rangle\mapsto +1,
\qquad
|-\rangle\mapsto -1.
$$

## 5. Why both Z-memory and X-memory experiments are required

| Experiment | Prepare    | Final measurement | Mainly detects |                   |
| ---------- | ---------- | ----------------- | -------------- | ----------------- |
| Z memory   | $0\rangle$ | $0\rangle_L$      | $Z_L$          | Logical $X$ flips |
| X memory   | $0\rangle$ | $+\rangle_L$      | $X_L$          | Logical $Z$ flips |

A logical $X$ error changes

$$
X_L|0\rangle_L=|1\rangle_L,
$$

which the final $Z_L$ measurement detects. A logical $Z$ error changes

$$
Z_L|+\rangle_L=|-\rangle_L,
$$

which the final $X_L$ measurement detects.

“Memory X/Z” names the logical observable being preserved, not the error being corrected.

Measuring in the $X$ basis prevents learning the $Z$ value from that same copy. This is not a problem: a memory experiment tests preservation of one known observable per shot. It does not reconstruct an unknown quantum state. Full state reconstruction would require many identically prepared copies measured in different bases.

## 6. Stabilizers and anticommutation

A stabilizer $S_i$ defines a parity property of the code state. Valid code states satisfy

$$
S_i|\psi_L\rangle=+|\psi_L\rangle
$$

for every stabilizer generator.

Operators $A$ and $B$ anticommute when

$$
AB=-BA.
$$

If an error $E$ anticommutes with stabilizer $S$, then

$$
S(E|\psi\rangle)=-E(S|\psi\rangle)=-E|\psi\rangle.
$$

The stabilizer eigenvalue flips from $+1$ to $-1$, revealing that an error affected that check. In a surface code:

- $X$ errors flip nearby $Z$-type stabilizers;
- $Z$ errors flip nearby $X$-type stabilizers;
- $Y$ errors can flip both types.

## 7. Ancillas and syndrome extraction

Ancillas do not receive copies of data-qubit states. They temporarily collect one collective parity per QEC round.

For

$$
S_Z=Z_1Z_2Z_3Z_4,
$$

prepare ancilla $A$ in $|0\rangle$, apply four ordinary CNOTs sequentially,

$$
\operatorname{CNOT}(D_1,A),\ldots,
\operatorname{CNOT}(D_4,A),
$$

and measure $A$. This is not one four-controlled CCNOT. The ancilla reports

$$
q_1\oplus q_2\oplus q_3\oplus q_4,
$$

the even/odd parity, without identifying the individual data values.

Bulk ancillas generally interact with four nearby data qubits; boundary checks may involve two. There are separate $X$-type and $Z$-type check ancillas.

After measurement, the ancilla result is stored classically. The ancilla is reset and reused, or its photon is consumed and replaced in photonic hardware. Its previous quantum state is not reusable.

## 8. Why stabilizer measurement preserves logical information

For $S=Z_1Z_2$, the $+1$ eigenspace is spanned by $|00\rangle$ and $|11\rangle$, while the $-1$ eigenspace is spanned by $|01\rangle$ and $|10\rangle$.

A general state

$$
a|00\rangle+b|11\rangle+c|01\rangle+d|10\rangle
$$

is projected by a stabilizer measurement into one eigenspace. If the result is $+1$, the surviving state is proportional to

$$
a|00\rangle+b|11\rangle.
$$

A valid code state already has definite stabilizer eigenvalues. Measuring a stabilizer therefore confirms the eigenspace it already occupies without distinguishing the logical states inside it. The measurement detects whether the state remains in the code space while preserving logical amplitudes such as $\alpha$ and $\beta$.

## 9. XOR and tensor-product notation

The circled plus

$$
\oplus
$$

means XOR, or addition modulo $2$:

| $a$ | $b$ | $a\oplus b$ |
|---:|---:|---:|
| 0 | 0 | 0 |
| 0 | 1 | 1 |
| 1 | 0 | 1 |
| 1 | 1 | 0 |

Do not confuse it with the tensor product $\otimes$. For example,

$$
Z_1Z_2\equiv Z\otimes Z.
$$

## 10. Rounds, shots, syndromes, and detection events

A **round** is one complete cycle of stabilizer extraction within an experiment. A **shot** is one full independent repetition:

$$
\text{prepare}
\rightarrow \text{rounds }1,2,\ldots,T
\rightarrow \text{final logical measurement}.
$$

Results are compared between consecutive rounds of the same shot, never between different shots.

Using the convention

$$
0\leftrightarrow +1,
\qquad
1\leftrightarrow -1,
$$

the detection bit for check $a$ at time $t$ is

$$
D_{a,t}=s_{a,t}\oplus s_{a,t-1}.
$$

| Round $t$ | 1 | 2 | 3 | 4 |
|---|---:|---:|---:|---:|
| Stabilizer bit $s_{a,t}$ | 0 | 0 | 1 | 1 |
| Detection bit $D_{a,t}$ | -- | 0 | 1 | 0 |

Interpretation:

- round 2: $0\oplus0=0$, so nothing changed;
- round 3: $1\oplus0=1$, so a detection event occurs;
- round 4: $1\oplus1=0$, so the stabilizer remains at $-1$ but no new transition occurs.

The detection event marks a change, not every round in which the stabilizer value is $-1$.

## 11. Why decoding is difficult

One changed check does not uniquely identify the fault. The cause could be a neighboring data error, a measurement error, multiple errors, or a time-dependent chain.

The decoder uses the complete space-time detection pattern $(x,y,t)$:

- a data error often produces events at neighboring checks;
- a measurement error often produces events at one check in consecutive times;
- an error chain may leave events only at its endpoints.

The decoder finds a likely correction consistent with the syndrome. It usually does not discard a data qubit. Ordinary Pauli corrections can be tracked in a classical **Pauli frame** and applied when interpreting the final measurement. Heralded erasure supplies extra location information, but it is still not generally equivalent to excluding that qubit's output.

## 12. Stim and PyMatching

Stim simulates the complete noisy stabilizer experiment. For each shot it:

1. samples physical faults;
2. propagates them through the Clifford circuit;
3. simulates syndrome extraction;
4. produces detection events and any herald data;
5. tracks the true logical-observable flip for grading.

For example, CNOT propagation can map

$$
X\otimes I\longrightarrow X\otimes X.
$$

PyMatching receives the detection events, not the hidden actual error. It predicts the logical correction. Comparing that prediction with Stim's hidden logical flip determines whether the shot was decoded successfully.

The decoder output is separate from an algorithm's output. It protects or reinterprets the final logical measurement; it does not search for the quantum algorithm's best answer.

## 13. Algorithm output versus QEC output

| Stage | Output | Role |
|---|---|---|
| Quantum algorithm | Logical bitstring sample | Sample from the algorithm's intended distribution |
| QEC decoder | Predicted correction or logical-flip bits | Correct the effect of physical faults |
| Classical postprocessing | Interpreted result | Combine corrected samples to answer the computational question |

Quantum interference changes the ideal probability distribution by increasing useful amplitudes and suppressing others. QEC attempts to keep hardware noise from distorting that distribution.

In this Phase 1 memory experiment there is no algorithmic answer bitstring. Each shot asks only whether the stored logical observable was decoded correctly. Across many shots,

$$
\hat P_L=
\frac{N_{\mathrm{logical\ failures}}}{N_{\mathrm{shots}}}.
$$

## 14. Approximation error and $O(p^2)$

Writing

$$
\Delta=O(p^2)
$$

means the leading discrepancy scales quadratically for sufficiently small $p$:

$$
\Delta\approx Cp^2.
$$

Halving $p$ should therefore reduce this term by approximately a factor of four. In graphlike error-model decompositions, an incorrect combination may require two rare branches to occur together, producing probability proportional to $p\times p=p^2$.

## 15. Confidence intervals and validation

The objective is to estimate and eventually minimize $P_L$, not to minimize confidence-interval width. More shots narrow uncertainty around a physically fixed $P_L$.

Confidence intervals are necessary to determine whether:

- increasing code distance truly lowers logical error;
- an optimized allocation truly beats the uniform baseline;
- a zero-failure run meaningfully constrains $P_L$;
- an optimizer selected a genuinely better design rather than a lucky Monte Carlo fluctuation.

If zero failures occur in $N$ shots, a useful rough 95% upper limit is the rule of three:

$$
P_L\lesssim\frac{3}{N}.
$$

Final candidate designs must be reevaluated with fresh random samples, many more shots, confidence intervals, and preferably paired comparisons with the baseline.

## 16. Baseline completion criteria

Phase 1 is complete only when the implementation demonstrates:

- both rotated-surface-code X- and Z-memory circuits;
- sensible logical-error estimates versus physical error rate;
- logical suppression as distance increases below an appropriate threshold regime;
- correct separation of rounds and shots;
- verified Stim-to-PyMatching detector and observable conventions;
- reproducible seeds and saved experiment parameters;
- confidence intervals and appropriate handling of zero failures;
- no optimization or photonic-specific claims mixed into the baseline results.

## 17. Next phase

After this uniform baseline is validated, continue to [[Anish's Second Brain/Projects/Quantum/Phase 2 Notes - Decoder-Aware Photonic Hardware Allocation|Phase 2 Notes - Decoder-Aware Photonic Hardware Allocation]]. The Phase 2 physical model, selective-allocation study, and component-derived channels are documented there rather than in this Phase 1 note.

#quantum-photonics #qec #surface-code #stim #pymatching #phase-1 #learning-notes
