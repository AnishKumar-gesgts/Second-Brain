"""Counterexample to extrapolating a subsystem likelihood-ratio trend.

All three distributions are supported on 20-bit strings with exactly 10 clicks.
This is a mathematical stress test of the inference in Jiuzhang 4 Fig. 2c,
not a model of Jiuzhang's optical hardware or its actual datasets.
"""
import json
from pathlib import Path
import numpy as np


def marginal(states, weights, size):
    return np.bincount(states & ((1 << size) - 1), weights=weights, minlength=1 << size)


def main():
    modes, clicks, mockup_spike = 20, 10, 0.2
    states = np.fromiter((x for x in range(1 << modes) if x.bit_count() == clicks), dtype=np.int64)
    ground_truth = np.full(len(states), 1 / len(states))

    # The synthetic "experiment" has an even number of clicks in the first
    # ten modes. Its small subsystem marginals look very similar to the uniform
    # fixed-click ground truth until those ten modes are jointly observed.
    first_half_mask = (1 << clicks) - 1
    experiment = np.array([(x & first_half_mask).bit_count() % 2 == 0 for x in states], dtype=float)
    experiment /= experiment.sum()

    # Efficiently samplable adversary: draw from the parity-conditioned
    # experiment with 80% probability, or a specific ten-click string with 20%.
    mockup = (1 - mockup_spike) * experiment
    mockup[np.searchsorted(states, first_half_mask)] += mockup_spike
    assert np.isclose(ground_truth.sum(), 1)
    assert np.isclose(experiment.sum(), 1)
    assert np.isclose(mockup.sum(), 1)

    rng = np.random.default_rng(20260930)
    observed_indices = rng.choice(len(states), size=100_000, p=experiment)
    observed = states[observed_indices]
    rows = []
    for size in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 16, 20]:
        q = marginal(states, experiment, size)
        p0 = marginal(states, ground_truth, size)
        p1 = marginal(states, mockup, size)
        support = q > 0
        expected = float(np.sum(q[support] * np.log(p0[support] / p1[support])))
        per_sample = np.log(p0[observed & ((1 << size) - 1)] / p1[observed & ((1 << size) - 1)])
        rows.append({"subsystem_modes": size,
                     "expected_log_bayes_score_per_sample": expected,
                     "sample_mean_log_bayes_score": float(per_sample.mean()),
                     "sample_standard_error": float(per_sample.std(ddof=1) / np.sqrt(len(per_sample)))})

    result = {
        "scope": "synthetic fixed-click distributions; counterexample to extrapolation, not Jiuzhang data",
        "modes": modes, "clicks_per_sample": clicks, "sample_count": len(observed),
        "ground_truth": "uniform among all 20-mode strings with 10 clicks",
        "synthetic_experiment": "uniform among fixed-click strings with even click parity in modes 1-10",
        "mockup": "80% parity-conditioned distribution plus 20% one fixed-click string",
        "score_convention": "mean log[ground_truth_probability / mockup_probability] under synthetic experiment; positive favors ground truth",
        "rows": rows,
    }
    output = Path(__file__).resolve().parents[1] / "outputs" / "jiuzhang_subsystem_bayes_counterexample.json"
    output.write_text(json.dumps(result, indent=2))
    for row in rows:
        print(f"{row['subsystem_modes']:2d} modes  expected {row['expected_log_bayes_score_per_sample']:+.6f}  "
              f"sample {row['sample_mean_log_bayes_score']:+.6f} ± {row['sample_standard_error']:.6f}")
    print(f"saved {output}")


if __name__ == "__main__":
    main()
