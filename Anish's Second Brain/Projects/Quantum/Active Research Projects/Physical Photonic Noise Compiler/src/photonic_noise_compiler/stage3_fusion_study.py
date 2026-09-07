"""Frozen higher-Fock-space study of the second adapter through a Bell fusion."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

from .adapters.heralded_source import HeraldedSourceParameters
from .adapters.standard_bsm import compile_standard_bsm


def run_stage3_fusion(config_path: Path, output_dir: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    rows: list[dict[str, float]] = []
    for mu in config["pair_probabilities"]:
        for eta_s in config["signal_efficiencies"]:
            for eta_id in config["idler_efficiencies"]:
                for eta_d in config["fusion_detector_efficiencies"]:
                    result = compile_standard_bsm(
                        HeraldedSourceParameters(mu, eta_s, eta_id),
                        detector_efficiency=eta_d,
                        photon_cutoff=int(config["photon_cutoff"]),
                        name=f"bsm_mu{mu:g}_s{eta_s:g}_i{eta_id:g}_d{eta_d:g}",
                    )
                    if result.max_full_bell_coherence > float(
                        config["bell_coherence_tolerance"]
                    ):
                        raise RuntimeError(
                            "full-success state is not Bell-diagonal within tolerance"
                        )
                    rows.append(
                        {
                            "pair_probability": mu,
                            "signal_efficiency": eta_s,
                            "idler_efficiency": eta_id,
                            "fusion_detector_efficiency": eta_d,
                            "full_success_probability": result.probability_full_success,
                            "partial_failure_probability": result.probability_partial_failure,
                            "count_rejection_probability": result.probability_count_rejection,
                            "full_success_hidden_error_probability": result.full_success_hidden_error_probability,
                            "hidden_error_given_full_success": result.accepted_error_given_full_success,
                            "partial_retained_parity_error_probability": result.partial_retained_parity_error_probability,
                            "xx_flip_marginal": result.channel.marginal("flip", "XX"),
                            "zz_flip_marginal": result.channel.marginal("flip", "ZZ"),
                            "max_full_bell_coherence": result.max_full_bell_coherence,
                        }
                    )

    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "fusion_grid.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    worst = max(rows, key=lambda row: row["hidden_error_given_full_success"])
    best = min(rows, key=lambda row: row["hidden_error_given_full_success"])
    summary = {
        "conditions": len(rows),
        "hidden_error_given_full_success_min": best[
            "hidden_error_given_full_success"
        ],
        "hidden_error_given_full_success_max": worst[
            "hidden_error_given_full_success"
        ],
        "best_condition": best,
        "worst_condition": worst,
        "maximum_full_success_bell_coherence": max(
            row["max_full_bell_coherence"] for row in rows
        ),
        "claim_boundary": config["claim_boundary"],
    }
    (output_dir / "fusion_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.1))
    marker_by_detector = {0.85: "o", 0.95: "s", 0.99: "^"}
    for eta_d in config["fusion_detector_efficiencies"]:
        selected = [row for row in rows if row["fusion_detector_efficiency"] == eta_d]
        axes[0].scatter(
            [row["pair_probability"] for row in selected],
            [100 * row["hidden_error_given_full_success"] for row in selected],
            alpha=0.55,
            marker=marker_by_detector[eta_d],
            label=f"detector {eta_d:.2f}",
        )
        axes[1].scatter(
            [100 * row["count_rejection_probability"] for row in selected],
            [100 * row["hidden_error_given_full_success"] for row in selected],
            alpha=0.55,
            marker=marker_by_detector[eta_d],
            label=f"detector {eta_d:.2f}",
        )
    axes[0].set_xlabel("pair probability")
    axes[0].set_ylabel("hidden error among full BSM records (%)")
    axes[0].set_title("Multiphoton emission creates false full records")
    axes[1].set_xlabel("wrong-total-count rejection probability (%)")
    axes[1].set_ylabel("hidden error among full BSM records (%)")
    axes[1].set_title("Visible rejection does not remove every false record")
    axes[1].legend(frameon=True)
    for axis in axes:
        axis.grid(alpha=0.25)
    fig.suptitle("Exact four-mode BSM propagation of heralded-source number noise")
    fig.tight_layout()
    fig.savefig(output_dir / "fusion_hidden_errors.png", dpi=200)
    plt.close(fig)
    return summary
