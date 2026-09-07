"""Frozen source-level study for the second physical adapter."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from .adapters.heralded_source import (
    HeraldedSourceParameters,
    compile_heralded_source,
    conditional_pair_signal_probability,
    conditional_signal_probability,
    one_count_herald_probability,
)


def _row(parameters: HeraldedSourceParameters, cutoff: int) -> dict[str, float]:
    channel = compile_heralded_source(
        parameters,
        name=(
            f"hsps_mu{parameters.pair_probability:g}_"
            f"etas{parameters.signal_efficiency:g}_"
            f"etaid{parameters.idler_efficiency:g}"
        ),
        photon_cutoff=cutoff,
    )
    vacuum = channel.marginal("erasure", "source_signal")
    multiphoton = channel.marginal("leakage", "source_signal")
    two_pair_masked = sum(
        conditional_pair_signal_probability(2, n, parameters)
        for n in range(3)
    )
    two_pair_hidden_fault = sum(
        conditional_pair_signal_probability(2, n, parameters)
        for n in (0, 2)
    )
    return {
        "pair_probability": parameters.pair_probability,
        "signal_efficiency": parameters.signal_efficiency,
        "idler_efficiency": parameters.idler_efficiency,
        "one_count_herald_probability": one_count_herald_probability(parameters),
        "conditional_vacuum_probability": vacuum,
        "conditional_single_photon_probability": 1.0 - vacuum - multiphoton,
        "conditional_multiphoton_probability": multiphoton,
        "conditional_hidden_fault_probability": vacuum + multiphoton,
        "two_pair_masked_fraction_of_valid_heralds": two_pair_masked,
        "two_pair_hidden_fault_probability": two_pair_hidden_fault,
        "decoder_visible_record_count": float(len(channel.decoder_distribution())),
    }


def run_stage3(config_path: Path, output_dir: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    cutoff = int(config["photon_cutoff"])
    reference_cutoff = int(config["convergence_reference_cutoff"])
    rows: list[dict[str, float]] = []
    max_tail = 0.0
    for mu in config["pair_probabilities"]:
        for eta_s in config["signal_efficiencies"]:
            for eta_id in config["idler_efficiencies"]:
                parameters = HeraldedSourceParameters(mu, eta_s, eta_id)
                row = _row(parameters, cutoff)
                reference_mass = sum(
                    conditional_signal_probability(n, parameters)
                    for n in range(reference_cutoff + 1)
                )
                cutoff_mass = sum(
                    conditional_signal_probability(n, parameters)
                    for n in range(cutoff + 1)
                )
                tail = max(0.0, reference_mass - cutoff_mass)
                row["cutoff_tail_probability"] = tail
                rows.append(row)
                max_tail = max(max_tail, tail)
    if max_tail > float(config["convergence_tolerance"]):
        raise RuntimeError(
            f"cutoff tail {max_tail:.3e} exceeds frozen tolerance"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0])
    with (output_dir / "source_grid.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    worst = max(rows, key=lambda row: row["conditional_hidden_fault_probability"])
    best = min(rows, key=lambda row: row["conditional_hidden_fault_probability"])
    summary = {
        "conditions": len(rows),
        "max_cutoff_tail_probability": max_tail,
        "hidden_fault_probability_min": best["conditional_hidden_fault_probability"],
        "hidden_fault_probability_max": worst["conditional_hidden_fault_probability"],
        "worst_condition": worst,
        "best_condition": best,
        "all_decoder_records_alias_hidden_histories": all(
            row["decoder_visible_record_count"] == 1.0 for row in rows
        ),
        "claim_boundary": config["claim_boundary"],
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    fig, axes = plt.subplots(
        1, len(config["pair_probabilities"]), figsize=(16, 3.7), sharey=True
    )
    for axis, mu in zip(axes, config["pair_probabilities"], strict=True):
        matrix = np.array(
            [
                [
                    next(
                        row["conditional_hidden_fault_probability"]
                        for row in rows
                        if row["pair_probability"] == mu
                        and row["signal_efficiency"] == eta_s
                        and row["idler_efficiency"] == eta_id
                    )
                    for eta_id in config["idler_efficiencies"]
                ]
                for eta_s in config["signal_efficiencies"]
            ]
        )
        image = axis.imshow(matrix, origin="lower", vmin=0, vmax=max(0.2, matrix.max()), cmap="magma")
        axis.set_title(f"pair probability = {mu:g}")
        axis.set_xticks(range(len(config["idler_efficiencies"])), config["idler_efficiencies"], rotation=45)
        axis.set_yticks(range(len(config["signal_efficiencies"])), config["signal_efficiencies"])
        axis.set_xlabel("idler + detector efficiency")
    axes[0].set_ylabel("signal efficiency")
    color_axis = fig.add_axes((0.925, 0.20, 0.012, 0.62))
    fig.colorbar(
        image,
        cax=color_axis,
        label="hidden fault probability | valid herald",
    )
    fig.suptitle("Valid one-count heralds alias vacuum and multiphoton source states")
    fig.subplots_adjust(left=0.06, right=0.90, bottom=0.24, top=0.76, wspace=0.18)
    fig.savefig(output_dir / "hidden_fault_grid.png", dpi=200)
    plt.close(fig)
    return summary
