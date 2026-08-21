HybridMCMC-CRW

Parent project: [[Anish's Second Brain/Projects/Quantum/Quantum Error Correction Research|Quantum research]]

This folder now stores the extracted project proposal for Hybrid Monte Carlo / correlated random-walk decoder work. Use it as the home for the proposal text, planning notes, and any future simulation scripts or parameter sweeps that grow out of the idea.

The immediate next step is to turn the proposal into a simple reproducible project brief: list the hypothesis, inputs, intended decoder comparison, and the Python dependencies needed for a first experiment.

## (C) Project Evaluation Summary (May 1, 2026)

Author: GitHub Copilot (GPT-5.3-Codex)
Source: Internal review conversation based on the proposal PDF in this folder.

### Preliminary ISEF Readiness Score

- Current estimate: 71/100 (proposal stage)
- Suggested target before competition: 85+/100

Scoring snapshot:

- Research Question: 9/10
- Design and Methodology: 12/15
- Execution (Data, Analysis, Interpretation): 12/20
- Creativity and Potential Impact: 18/20
- Presentation and Interview Readiness: 20/35

### What Is Already Strong

- Clear high-impact question: decoder latency vs accuracy tradeoff at scale.
- Novel mechanism: trigger-based controlled random walk to escape flat regions/local minima.
- Good baseline plan: compare against major decoders (Union-Find and MWPM).
- Strong scalability motivation for larger qubit/syndrome counts.

### What Needs Improvement

- Define a precise, testable hypothesis with measurable thresholds.
- Specify the ambiguity trigger mathematically (exact threshold rule and schedule).
- Add ablation studies to isolate the contribution of each hybrid component.
- Formalize statistics: confidence intervals, significance tests, fixed trials per condition.
- Guarantee benchmark fairness: same hardware, same stopping rules, same noise model per run.
- Prevent overfitting by separating tuning from final evaluation (train/validation/test regimes).
- Add a non-uniform noise stress-test campaign that sweeps from mild heterogeneity to extreme regimes near the critical logical error region.
- Separate claims about practical robustness from claims about theoretical thresholds.

## Main Goals To Strengthen the Project

1. Lock a measurable hypothesis.
- Example: reduce median decode time by at least 30% at matched logical error rate for selected code distances.

2. Build a reproducible experiment matrix.
- Predefine code distances, physical error rates, iteration limits, and random seed policy.

3. Implement full benchmark and ablation suite.
- Compare Union-Find, MWPM, baseline MCMC, and Hybrid MCMC-CRW with component-level ablations.

4. Add robust statistical reporting.
- Report means, medians, variance, confidence intervals, and significance tests across large trial counts.

5. Perform scaling-law and failure-mode analysis.
- Characterize runtime/accuracy trends as syndrome size grows and document where Hybrid MCMC-CRW underperforms.

6. Prepare competition-grade communication artifacts.
- Maintain a lab notebook, reproducible scripts, concise figures, and interview-ready explanations of novelty, limitations, and next steps.

7. Add near-threshold robustness experiments.
- Purposefully synthesize strongly non-uniform noise and compare all decoders close to critical logical error regimes.
- Measure both: (a) logical error at fixed time budget and (b) time to hit fixed logical error target.
- Include many random seeds and report confidence intervals.

8. Tighten claim wording for scientific defensibility.
- Primary claim should be practical: improved robustness/latency tradeoff under non-ideal and non-uniform noise.
- Avoid claiming a universally higher theoretical threshold unless asymptotic threshold analysis rigorously supports it.

## New Strategic Note: Extreme Non-Uniform Noise Testing

### Why this helps

- Real hardware noise is frequently non-uniform, biased, and drifting.
- Stress testing under heterogeneity can reveal robustness that is hidden under idealized i.i.d. noise.
- This strengthens novelty in a crowded computing category because the project addresses realistic deployment conditions.

### What to expect

- Under standard well-matched i.i.d. noise, strong baselines (especially MWPM) may remain very competitive in logical error rate.
- Under highly non-uniform or model-mismatched conditions, Hybrid MCMC-CRW may show better robustness and/or latency-accuracy tradeoff.
- Above threshold, all decoders eventually degrade; do not frame results as "beating physics."

### Recommended claim framing

- "Hybrid MCMC-CRW improves robustness and decode latency tradeoffs under non-uniform, high-stress noise landscapes, especially near critical operating regimes, relative to baseline decoders."

### Required fairness controls for this experiment

- Same hardware and software environment for all decoders.
- Same code distances, noise regimes, seeds, and stopping criteria.
- Clearly defined train/validation/test split for tuning thresholds.
- Include ablations to isolate the effect of the controlled random-walk trigger.

## Category Fit: Physics vs Computing

### Computing/Software-oriented categories (recommended primary fit)

Benefits:

- Core novelty is algorithmic design and optimization of a decoder.
- Evaluation depends on runtime, convergence behavior, and statistical performance.
- Benchmarking against established decoders aligns naturally with systems/software judging.
- A non-uniform near-threshold stress-test framing gives a strong "real-world robustness" angle that can stand out from generic AI projects.

Potential category homes:

- Systems Software
- Embedded Systems (if tied to hardware constraints or deployment pathway)
- Robotics and Intelligent Machines (only if framed as autonomous control system, usually less direct)

### Physics-oriented categories (possible but weaker default fit)

Benefits:

- Strong connection to quantum error correction and fault-tolerant quantum computing context.
- Could fit if the work is framed around physics-grounded noise models and theoretical interpretation with substantial physics analysis.

Limitations:

- Judges may expect more fundamental physics discovery than decoder engineering.
- If experiments are mostly algorithm benchmarking, physics fit can appear secondary.

### Current recommendation

- Primary: Computing-focused category (typically Systems Software).
- Secondary option: Physics and Astronomy only if project scope includes substantial physics-model and threshold behavior analysis beyond decoder performance metrics.
