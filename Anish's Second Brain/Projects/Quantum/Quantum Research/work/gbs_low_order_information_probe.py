"""Small physical GBS test of whether low-order click data determine samples.

The surrogate is a maximum-entropy model fitted to all click moments through
order K. It is NOT Dodd et al.'s cumulant-chain-rule emulator. The experiment
isolates the information assumption common to low-order surrogate strategies.
"""
import itertools
import json
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp
from gbs_projection_probe import exact_click_probs, haar_unitary


def feature_matrix(m, order):
    outcomes = np.arange(1 << m)
    spins = 2 * ((outcomes[:, None] >> np.arange(m)) & 1) - 1
    subsets = [subset for k in range(1, order + 1)
               for subset in itertools.combinations(range(m), k)]
    features = np.column_stack([np.prod(spins[:, subset], axis=1) for subset in subsets]).astype(float)
    return features, subsets


def fit_maxent(exact, features):
    target = exact @ features
    def objective(theta):
        logits = features @ theta
        log_z = logsumexp(logits)
        p = np.exp(logits - log_z)
        return log_z - theta @ target, features.T @ p - target
    fit = minimize(objective, np.zeros(features.shape[1]), jac=True, method="L-BFGS-B",
                   options={"maxiter": 3000, "gtol": 1e-10, "ftol": 1e-15})
    logits = features @ fit.x
    approx = np.exp(logits - logsumexp(logits))
    moment_error = np.max(np.abs(exact @ features - approx @ features))
    return approx, float(moment_error), bool(fit.success)


def main():
    rng = np.random.default_rng(20260930)
    m = 8
    settings = [("four_sources_high_efficiency", np.array([.8] * 4 + [0.] * 4), .9),
                ("eight_sources_medium_efficiency", np.array([.7] * 8), .7),
                ("eight_sources_high_efficiency", np.array([.8] * 8), .9)]
    results = []
    for name, squeezing, transmission in settings:
        for seed in range(3):
            u = haar_unitary(m, rng)
            exact, _ = exact_click_probs(squeezing, u, transmission)
            assert exact.min() > -1e-10 and abs(exact.sum() - 1) < 1e-10
            exact = np.maximum(exact, 0)
            exact /= exact.sum()
            row = {"setting": name, "instance": seed, "modes": m,
                   "transmission": transmission, "squeezing": squeezing.tolist(),
                   "approximations": []}
            for k in (1, 2, 3, 4, 5):
                features, subsets = feature_matrix(m, k)
                approx, err, converged = fit_maxent(exact, features)
                row["approximations"].append({"matched_moment_order": k,
                    "number_of_matched_features": len(subsets),
                    "maximum_moment_error": err,
                    "full_distribution_tvd": float(.5 * np.abs(exact - approx).sum()),
                    "optimizer_converged": converged})
            results.append(row)
    output = {"scope": "exact eight-mode GBS versus maximum-entropy classical surrogate matched on all low-order click moments",
              "warning": "not a test of the published Dodd cumulant sampler or large Jiuzhang data",
              "results": results}
    path = Path(__file__).resolve().parents[1] / "outputs" / "gbs_low_order_information_probe.json"
    path.write_text(json.dumps(output, indent=2))
    for row in results:
        print(row["setting"], row["instance"],
              [(x["matched_moment_order"], round(x["full_distribution_tvd"], 5),
                round(x["maximum_moment_error"], 7)) for x in row["approximations"]])
    print(path)


if __name__ == "__main__":
    main()
