"""Small-system test of the raw positive-P-to-click projection in Dellios et al.

The published method also applies an iterative whitening/coloring correction; this
probe intentionally omits that step and is not a Jiuzhang 4 simulation.
"""
import json
from pathlib import Path
import numpy as np


def haar_unitary(m, rng):
    z = (rng.normal(size=(m, m)) + 1j * rng.normal(size=(m, m))) / np.sqrt(2)
    q, r = np.linalg.qr(z)
    return q * (np.diag(r) / abs(np.diag(r)))


def exact_click_probs(r, u, eta):
    m = len(r)
    re, im = u.real, u.imag
    sym = np.block([[re, -im], [im, re]])
    vin = np.diag(np.r_[np.exp(-2 * r) / 2, np.exp(2 * r) / 2])
    v = eta * (sym @ vin @ sym.T) + (1 - eta) * np.eye(2 * m) / 2
    p0 = np.ones(1 << m)
    for mask in range(1, 1 << m):
        sites = [i for i in range(m) if mask & (1 << i)]
        inds = sites + [i + m for i in sites]
        sub = v[np.ix_(inds, inds)] + np.eye(2 * len(sites)) / 2
        p0[mask] = 1 / np.sqrt(np.linalg.det(sub))
    exact = np.zeros(1 << m)
    allmask = (1 << m) - 1
    for clicked in range(1 << m):
        noclick = allmask ^ clicked
        val = 0.0
        sub = clicked
        while True:
            val += (-1) ** sub.bit_count() * p0[noclick | sub]
            if sub == 0:
                break
            sub = (sub - 1) & clicked
        exact[clicked] = val
    return exact, p0


def projected_probs(r, u, eta, rng, target_single_vac, shots=400_000, batch=50_000):
    m = len(r)
    n = np.sinh(r) ** 2
    anomalous = -np.sinh(r) * np.cosh(r)
    dp = np.sqrt(((n + anomalous) / 2).astype(complex))
    dm = np.sqrt(((n - anomalous) / 2).astype(complex))
    out = np.zeros(1 << m)
    unprojected_vac = 0.0
    raw_vac_samples = np.empty((m, shots))
    for start in range(0, shots, batch):
        b = min(batch, shots - start)
        w = rng.normal(size=(2, m, b))
        alpha = dp[:, None] * w[0] + 1j * dm[:, None] * w[1]
        beta = dp[:, None] * w[0] - 1j * dm[:, None] * w[1]
        alpha = np.sqrt(eta) * u @ alpha
        beta = np.sqrt(eta) * u.conj() @ beta
        vacuum_weight = np.exp(-alpha * beta)
        unprojected_vac += float(np.sum(np.prod(vacuum_weight, axis=0).real))
        raw_vac_samples[:, start:start + b] = vacuum_weight.real
        no = np.clip(vacuum_weight.real, 0, 1)
        yes = 1 - no
        for mask in range(1 << m):
            probs = np.prod([yes[i] if mask & (1 << i) else no[i] for i in range(m)], axis=0)
            out[mask] += probs.sum()
    calibrated = np.empty_like(raw_vac_samples)
    for i in range(m):
        lo, hi = -5.0, 5.0
        for _ in range(40):
            mid = (lo + hi) / 2
            if np.clip(raw_vac_samples[i] + mid, 0, 1).mean() < target_single_vac[i]:
                lo = mid
            else:
                hi = mid
        calibrated[i] = np.clip(raw_vac_samples[i] + (lo + hi) / 2, 0, 1)
    corrected = np.zeros(1 << m)
    for mask in range(1 << m):
        probs = np.prod([1 - calibrated[i] if mask & (1 << i) else calibrated[i] for i in range(m)], axis=0)
        corrected[mask] = probs.mean()
    return out / shots, corrected, unprojected_vac / shots


def main():
    rng = np.random.default_rng(20260930)
    configs = [
        ("mixed_squeezing", [0.8, 0.7, 0.6, 0.0], 0.51),
        ("uniform_medium", [0.6] * 4, 0.51),
        ("uniform_high", [0.9] * 4, 0.51),
    ]
    entries = []
    for name, rlist, eta in configs:
        r = np.array(rlist)
        u = haar_unitary(len(r), rng)
        exact, p0 = exact_click_probs(r, u, eta)
        approx, corrected, rawvac = projected_probs(r, u, eta, rng, p0[[1 << i for i in range(len(r))]])
        popcount = np.array([x.bit_count() for x in range(len(exact))])
        exact_count = np.bincount(popcount, weights=exact, minlength=len(r) + 1)
        approx_count = np.bincount(popcount, weights=approx, minlength=len(r) + 1)
        corrected_count = np.bincount(popcount, weights=corrected, minlength=len(r) + 1)
        entries.append({"case": name, "r": r.tolist(), "eta": eta,
                        "exact_sum": float(exact.sum()), "min_exact_probability": float(exact.min()),
                        "raw_positive_p_all_vacuum": rawvac, "exact_all_vacuum": float(p0[-1]),
                        "projected_full_tvd": float(0.5 * abs(exact - approx).sum()),
                        "projected_count_tvd": float(0.5 * abs(exact_count - approx_count).sum()),
                        "single_mode_calibrated_full_tvd": float(0.5 * abs(exact - corrected).sum()),
                        "single_mode_calibrated_count_tvd": float(0.5 * abs(exact_count - corrected_count).sum()),
                        "exact_count_distribution": exact_count.round(6).tolist(),
                        "projected_count_distribution": approx_count.round(6).tolist()})
    result = {"scope": "raw positive-P projection, four output modes; excludes published whitening-coloring correction and Jiuzhang 4 hardware", "cases": entries}
    dest = Path(__file__).resolve().parents[1] / "outputs" / "gbs_projection_probe.json"
    dest.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
