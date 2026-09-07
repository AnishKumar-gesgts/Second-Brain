"""Robustness maps over detuning, timing jitter, and spectral diffusion."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .physics import PhysicalParameters, event_table
from .qec import simulate_logical_error


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _select_and_confirm(
    params: PhysicalParameters,
    config: dict[str, Any],
    seed_offset: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    gates: list[float | None] = [float(x) for x in config["gate_widths_ps"]] + [None]
    selection_distance = int(config["selection_distance"])
    pilot: list[tuple[float | None, Any]] = []
    for index, gate in enumerate(gates):
        table = event_table(params, gate, grid_points=int(config["temporal_grid_points"]))
        estimate = simulate_logical_error(
            table,
            selection_distance,
            selection_distance,
            int(config["pilot_shots"]),
            int(config["pilot_seed"]) + seed_offset * 1000 + index,
        )
        pilot.append((gate, estimate))
    candidate_gate, candidate_estimate = min(
        pilot, key=lambda item: item[1].logical_error_rate
    )
    no_filter_estimate = next(estimate for gate, estimate in pilot if gate is None)
    selection_passed = (
        candidate_gate is not None
        and candidate_estimate.ci_high < no_filter_estimate.ci_low
    )
    # Guard against winner's-curse overfitting in low-noise regimes: retain no
    # filtering unless the pilot improvement already clears both 95% intervals.
    best_gate = candidate_gate if selection_passed else None
    pilot_rate = (
        candidate_estimate.logical_error_rate
        if selection_passed
        else no_filter_estimate.logical_error_rate
    )

    heldout: list[dict[str, Any]] = []
    for rule_index, (rule, gate) in enumerate((("selected", best_gate), ("no_filter", None))):
        if rule == "no_filter" and best_gate is None:
            heldout.extend({**row, "rule": "no_filter"} for row in heldout if row["rule"] == "selected")
            continue
        table = event_table(params, gate, grid_points=int(config["temporal_grid_points"]))
        for distance in config["distances"]:
            estimate = simulate_logical_error(
                table,
                int(distance),
                int(distance),
                int(config["heldout_shots"]),
                int(config["heldout_seed"]) + seed_offset * 1000 + rule_index * 100 + int(distance),
            )
            heldout.append(
                {
                    "rule": rule,
                    "gate_width_ps": gate,
                    "distance": int(distance),
                    **estimate.to_dict(),
                }
            )
    selected = sorted((r for r in heldout if r["rule"] == "selected"), key=lambda r: r["distance"])
    unfiltered = sorted((r for r in heldout if r["rule"] == "no_filter"), key=lambda r: r["distance"])
    selected_d5 = next(r for r in selected if r["distance"] == selection_distance)
    unfiltered_d5 = next(r for r in unfiltered if r["distance"] == selection_distance)
    summary = {
        **params.to_dict(),
        "pilot_candidate_gate_width_ps": candidate_gate,
        "selection_passed_confidence_guard": selection_passed,
        "selected_gate_width_ps": best_gate,
        "pilot_selected_rate": pilot_rate,
        "selected_d5_rate": selected_d5["logical_error_rate"],
        "no_filter_d5_rate": unfiltered_d5["logical_error_rate"],
        "relative_d5_improvement": 1.0 - selected_d5["logical_error_rate"] / unfiltered_d5["logical_error_rate"] if unfiltered_d5["logical_error_rate"] else 0.0,
        "selected_d5_ci_low": selected_d5["ci_low"],
        "selected_d5_ci_high": selected_d5["ci_high"],
        "no_filter_d5_ci_low": unfiltered_d5["ci_low"],
        "no_filter_d5_ci_high": unfiltered_d5["ci_high"],
        "significant_d5_improvement": selected_d5["ci_high"] < unfiltered_d5["ci_low"],
        "significant_d5_harm": selected_d5["ci_low"] > unfiltered_d5["ci_high"],
        "selected_d7_over_d3": selected[-1]["logical_error_rate"] / selected[0]["logical_error_rate"] if selected[0]["logical_error_rate"] else 0.0,
        "no_filter_d7_over_d3": unfiltered[-1]["logical_error_rate"] / unfiltered[0]["logical_error_rate"] if unfiltered[0]["logical_error_rate"] else 0.0,
        "selected_significant_suppression": selected[-1]["ci_high"] < selected[0]["ci_low"],
        "no_filter_significant_suppression": unfiltered[-1]["ci_high"] < unfiltered[0]["ci_low"],
        "suppression_recovered": selected[-1]["ci_high"] < selected[0]["ci_low"] and not unfiltered[-1]["ci_high"] < unfiltered[0]["ci_low"],
    }
    return summary, heldout


def _heatmaps(path: Path, rows: list[dict[str, Any]], detunings: list[float], jitters: list[float]) -> None:
    metrics = [
        ("relative_d5_improvement", "Relative improvement at d=5", "RdYlGn", -0.15, 0.25),
        ("selected_d7_over_d3", "Selected gate: d=7 / d=3", "RdYlGn_r", 0.5, 1.5),
        ("selected_gate_width_ps", "Selected half-width (ps)", "viridis", None, None),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
    for ax, (key, title, cmap, vmin, vmax) in zip(axes, metrics):
        matrix = np.full((len(jitters), len(detunings)), np.nan)
        for row in rows:
            i = jitters.index(float(row["detector_jitter_ps"]))
            j = detunings.index(float(row["frequency_detuning_ghz"]))
            value = row[key]
            matrix[i, j] = np.nan if value is None else float(value)
        image = ax.imshow(matrix, origin="lower", aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax)
        ax.set_xticks(range(len(detunings)), detunings)
        ax.set_yticks(range(len(jitters)), jitters)
        ax.set_xlabel("Mean detuning (GHz)")
        ax.set_ylabel("Detector jitter (ps)")
        ax.set_title(title)
        for i in range(len(jitters)):
            for j in range(len(detunings)):
                label = "none" if np.isnan(matrix[i, j]) else f"{matrix[i, j]:.2f}"
                ax.text(j, i, label, ha="center", va="center", fontsize=8)
        fig.colorbar(image, ax=ax, shrink=0.82)
    fig.suptitle("Held-out robustness map (200,000 shots per point)")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _plot_diffusion(path: Path, rows: list[dict[str, Any]]) -> None:
    rows = sorted(rows, key=lambda row: float(row["spectral_diffusion_ghz"]))
    x = [row["spectral_diffusion_ghz"] for row in rows]
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4))
    axes[0].plot(x, [row["relative_d5_improvement"] for row in rows], "o-")
    axes[0].axhline(0, color="black", linewidth=1)
    axes[0].set_ylabel("Relative d=5 improvement")
    axes[1].plot(x, [row["selected_d7_over_d3"] for row in rows], "o-", label="selected")
    axes[1].plot(x, [row["no_filter_d7_over_d3"] for row in rows], "o-", label="no filter")
    axes[1].axhline(1, color="black", linewidth=1)
    axes[1].set_ylabel("Distance-7 / distance-3 rate")
    axes[1].legend()
    for ax in axes:
        ax.set_xlabel("Spectral diffusion standard deviation (GHz)")
        ax.grid(alpha=0.25)
    fig.suptitle("Robustness to shot-to-shot spectral diffusion")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def run_robustness(config_path: Path, output_dir: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)
    summaries: list[dict[str, Any]] = []
    heldout_rows: list[dict[str, Any]] = []
    offset = 1
    for jitter in config["jitters_ps"]:
        for detuning in config["detunings_ghz"]:
            params = PhysicalParameters(
                float(config["wavepacket_sigma_ps"]),
                float(jitter),
                float(detuning),
                float(config["detector_efficiency"]),
            )
            summary, heldout = _select_and_confirm(params, config, offset)
            summaries.append(summary)
            heldout_rows.extend({**params.to_dict(), **row} for row in heldout)
            offset += 1

    diffusion_rows: list[dict[str, Any]] = []
    for diffusion in config["spectral_diffusions_ghz"]:
        params = PhysicalParameters(
            float(config["wavepacket_sigma_ps"]),
            float(config["diffusion_reference_jitter_ps"]),
            float(config["diffusion_reference_detuning_ghz"]),
            float(config["detector_efficiency"]),
            float(diffusion),
        )
        summary, heldout = _select_and_confirm(params, config, offset)
        diffusion_rows.append(summary)
        heldout_rows.extend({**params.to_dict(), **row} for row in heldout)
        offset += 1

    _write_csv(output_dir / "robustness_summary.csv", summaries)
    _write_csv(output_dir / "spectral_diffusion_summary.csv", diffusion_rows)
    _write_csv(output_dir / "robustness_heldout.csv", heldout_rows)
    detunings = [float(x) for x in config["detunings_ghz"]]
    jitters = [float(x) for x in config["jitters_ps"]]
    _heatmaps(output_dir / "robustness_heatmaps.png", summaries, detunings, jitters)
    _plot_diffusion(output_dir / "spectral_diffusion.png", diffusion_rows)
    result = {
        "config": config,
        "grid_points": len(summaries),
        "filtering_improves_count": sum(row["relative_d5_improvement"] > 0 for row in summaries),
        "significant_improvement_count": sum(bool(row["significant_d5_improvement"]) for row in summaries),
        "suppression_recovered_count": sum(bool(row["suppression_recovered"]) for row in summaries),
        "filtering_harms_count": sum(row["relative_d5_improvement"] < 0 for row in summaries),
        "significant_harm_count": sum(bool(row["significant_d5_harm"]) for row in summaries),
        "best_relative_improvement": max(row["relative_d5_improvement"] for row in summaries),
        "worst_relative_improvement": min(row["relative_d5_improvement"] for row in summaries),
        "diffusion_results": diffusion_rows,
    }
    (output_dir / "robustness_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
