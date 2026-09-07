"""End-to-end baseline study and artifact generation."""

from __future__ import annotations

import csv
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .fock import balanced_beamsplitter_validation
from .physics import PhysicalParameters, analytic_unfiltered, event_table, sample_event_frequencies
from .qec import simulate_logical_error


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _label(gate: float | None) -> str:
    return "no_filter" if gate is None else f"{gate:g}_ps"


def _plot_physics(path: Path, rows: list[dict[str, Any]]) -> None:
    finite = [row for row in rows if row["gate_width_ps"] is not None]
    x = np.array([row["gate_width_ps"] for row in finite], dtype=float)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    axes[0].plot(x, [r["acceptance"] for r in finite], "o-", label="accepted")
    axes[0].plot(x, [r["erasure"] for r in finite], "o-", label="heralded erasure")
    axes[0].plot(x, [r["accepted_wrong"] for r in finite], "o-", label="unheralded fault")
    axes[0].set_xscale("log")
    axes[0].set_xlabel("Half-width of temporal gate (ps)")
    axes[0].set_ylabel("Probability per location")
    axes[0].legend()
    axes[0].grid(alpha=0.25)
    axes[1].plot(x, [r["conditional_accepted_error"] for r in finite], "o-", color="tab:red")
    axes[1].set_xscale("log")
    axes[1].set_xlabel("Half-width of temporal gate (ps)")
    axes[1].set_ylabel("Error among accepted events")
    axes[1].grid(alpha=0.25)
    fig.suptitle("Temporal filtering trades unheralded faults for heralded erasures")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _plot_logical(path: Path, pilot_rows: list[dict[str, Any]], heldout_rows: list[dict[str, Any]]) -> None:
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    distances = sorted({int(row["distance"]) for row in pilot_rows})
    for distance in distances:
        rows = [r for r in pilot_rows if int(r["distance"]) == distance and r["gate_width_ps"] is not None]
        x = np.array([r["gate_width_ps"] for r in rows], dtype=float)
        floor = 0.5 / max(r["shots"] for r in rows)
        y = np.maximum([r["logical_error_rate"] for r in rows], floor)
        line = ax.plot(x, y, "o-", label=f"pilot d={distance}")[0]
        held = [r for r in heldout_rows if int(r["distance"]) == distance and r["gate_width_ps"] is not None]
        if held:
            ax.errorbar(
                [r["gate_width_ps"] for r in held],
                [max(r["logical_error_rate"], 0.5 / r["shots"]) for r in held],
                yerr=[
                    [r["logical_error_rate"] - r["ci_low"] for r in held],
                    [r["ci_high"] - r["logical_error_rate"] for r in held],
                ],
                fmt="s",
                capsize=3,
                color=line.get_color(),
            )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Half-width of temporal gate (ps)")
    ax.set_ylabel("Decoded logical error rate")
    ax.set_title("Stim/PyMatching code-capacity benchmark")
    ax.grid(alpha=0.25, which="both")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _plot_distance_scaling(path: Path, heldout_rows: list[dict[str, Any]]) -> None:
    fig, ax = plt.subplots(figsize=(6.8, 4.6))
    labels = list(dict.fromkeys(row["gate_label"] for row in heldout_rows))
    for label in labels:
        rows = sorted(
            (row for row in heldout_rows if row["gate_label"] == label),
            key=lambda row: int(row["distance"]),
        )
        ax.errorbar(
            [int(row["distance"]) for row in rows],
            [row["logical_error_rate"] for row in rows],
            yerr=[
                [row["logical_error_rate"] - row["ci_low"] for row in rows],
                [row["ci_high"] - row["logical_error_rate"] for row in rows],
            ],
            marker="o",
            capsize=3,
            label=label.replace("_", " "),
        )
    ax.set_xlabel("Surface-code distance")
    ax.set_ylabel("Decoded logical error rate")
    ax.set_title("Held-out distance scaling")
    ax.set_xticks(sorted({int(row["distance"]) for row in heldout_rows}))
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def run_study(config_path: Path, output_dir: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    params = PhysicalParameters(**config["physical"])
    output_dir.mkdir(parents=True, exist_ok=True)
    grid_points = int(config["temporal_grid_points"])
    gates: list[float | None] = [float(x) for x in config["gate_widths_ps"]] + [None]

    physical_tables = [event_table(params, gate, grid_points=grid_points) for gate in gates]
    physical_rows = [table.to_dict() for table in physical_tables]
    _write_csv(output_dir / "physical_sweep.csv", physical_rows)

    fock_rows = [balanced_beamsplitter_validation(cutoff).__dict__ for cutoff in (3, 4)]
    unfiltered_numeric = physical_tables[-1]
    unfiltered_exact = analytic_unfiltered(params)
    validation = {
        "fock_cutoffs": fock_rows,
        "unfiltered_max_abs_error": max(
            abs(float(unfiltered_numeric.to_dict()[key]) - float(unfiltered_exact.to_dict()[key]))
            for key in ("accepted_correct", "accepted_wrong", "rejected", "loss")
        ),
        "monte_carlo_60ps": sample_event_frequencies(
            params, 60.0, 500_000, int(config["pilot_seed"]) + 991
        ),
        "integrated_60ps": event_table(params, 60.0, grid_points=grid_points).to_dict(),
    }
    (output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")

    pilot_rows: list[dict[str, Any]] = []
    for gate_index, table in enumerate(physical_tables):
        for distance in config["distances"]:
            estimate = simulate_logical_error(
                table,
                int(distance),
                int(distance),
                int(config["pilot_shots"]),
                int(config["pilot_seed"]) + 1000 * gate_index + int(distance),
            )
            pilot_rows.append(
                {"gate_width_ps": table.gate_width_ps, "gate_label": _label(table.gate_width_ps), **estimate.to_dict()}
            )
    _write_csv(output_dir / "pilot_logical_sweep.csv", pilot_rows)

    selection_distance = int(config["selection_distance"])
    selection_rows = [r for r in pilot_rows if int(r["distance"]) == selection_distance]
    best = min(selection_rows, key=lambda row: row["logical_error_rate"])
    best_gate = best["gate_width_ps"]
    finite_gates = [gate for gate in gates if gate is not None]
    comparison_gates: list[float | None] = list(dict.fromkeys([best_gate, min(finite_gates), None]))

    heldout_rows: list[dict[str, Any]] = []
    for gate_index, gate in enumerate(comparison_gates):
        table = event_table(params, gate, grid_points=grid_points)
        for distance in config["distances"]:
            estimate = simulate_logical_error(
                table,
                int(distance),
                int(distance),
                int(config["heldout_shots"]),
                int(config["heldout_seed"]) + 1000 * gate_index + int(distance),
            )
            heldout_rows.append(
                {"gate_width_ps": gate, "gate_label": _label(gate), **estimate.to_dict()}
            )
    _write_csv(output_dir / "heldout_logical.csv", heldout_rows)

    controls: list[dict[str, Any]] = []
    for detuning in config["control_detunings_ghz"]:
        control_params = replace(params, frequency_detuning_ghz=float(detuning))
        for gate in (best_gate, None):
            table = event_table(control_params, gate, grid_points=grid_points)
            estimate = simulate_logical_error(
                table,
                selection_distance,
                selection_distance,
                int(config["heldout_shots"]),
                int(config["heldout_seed"]) + int(float(detuning) * 10_000) + (0 if gate is None else 500),
            )
            controls.append(
                {"detuning_ghz": detuning, "gate_width_ps": gate, "gate_label": _label(gate), **table.to_dict(), **estimate.to_dict()}
            )
    _write_csv(output_dir / "controls.csv", controls)

    blind_table = event_table(params, best_gate, grid_points=grid_points)
    blind = simulate_logical_error(
        blind_table,
        selection_distance,
        selection_distance,
        int(config["heldout_shots"]),
        int(config["heldout_seed"]) + 700_000,
        heralded_decoder=False,
    )
    _plot_physics(output_dir / "physical_tradeoff.png", physical_rows)
    _plot_logical(output_dir / "logical_error_vs_gate.png", pilot_rows, heldout_rows)
    _plot_distance_scaling(output_dir / "distance_scaling.png", heldout_rows)

    best_held = next(
        r for r in heldout_rows if r["gate_width_ps"] == best_gate and int(r["distance"]) == selection_distance
    )
    no_filter = next(
        r for r in heldout_rows if r["gate_width_ps"] is None and int(r["distance"]) == selection_distance
    )
    improvement = (
        no_filter["logical_error_rate"] / best_held["logical_error_rate"]
        if best_held["logical_error_rate"] > 0
        else float("inf")
    )
    supported = best_held["ci_high"] < no_filter["ci_low"]
    selected_distance_rows = sorted(
        (r for r in heldout_rows if r["gate_width_ps"] == best_gate), key=lambda r: int(r["distance"])
    )
    unfiltered_distance_rows = sorted(
        (r for r in heldout_rows if r["gate_width_ps"] is None), key=lambda r: int(r["distance"])
    )
    selected_suppresses = selected_distance_rows[-1]["ci_high"] < selected_distance_rows[0]["ci_low"]
    unfiltered_suppresses = unfiltered_distance_rows[-1]["ci_high"] < unfiltered_distance_rows[0]["ci_low"]
    summary = {
        "config": config,
        "selected_gate_width_ps": best_gate,
        "selection_distance": selection_distance,
        "heldout_selected": best_held,
        "heldout_no_filter": no_filter,
        "heldout_rate_ratio_no_filter_over_selected": improvement,
        "nonoverlapping_95pct_wilson_intervals": supported,
        "flag_blind_selected_gate": blind.to_dict(),
        "hypothesis_supported": supported,
        "selected_gate_distance_3_to_7_ratio": selected_distance_rows[-1]["logical_error_rate"] / selected_distance_rows[0]["logical_error_rate"],
        "no_filter_distance_3_to_7_ratio": unfiltered_distance_rows[-1]["logical_error_rate"] / unfiltered_distance_rows[0]["logical_error_rate"],
        "selected_gate_has_significant_distance_suppression": selected_suppresses,
        "no_filter_has_significant_distance_suppression": unfiltered_suppresses,
        "claim_boundary": "Gaussian two-photon primitive plus code-capacity rotated-surface-code mapping; not a native FBQC threshold or hardware validation.",
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    verdict = "supports" if supported else "does not yet support"
    selected_gate_text = "no filtering" if best_gate is None else f"{best_gate:g} ps"
    report = f"""# Baseline result

The frozen held-out study **{verdict}** the model-scoped hypothesis that a finite temporal gate can reduce decoded logical error relative to no filtering.

- Selected pilot gate: **{selected_gate_text}** at distance {selection_distance}.
- Held-out selected-gate logical error: **{best_held['logical_error_rate']:.6g}** (95% Wilson CI {best_held['ci_low']:.6g}-{best_held['ci_high']:.6g}).
- Held-out no-filter logical error: **{no_filter['logical_error_rate']:.6g}** (95% Wilson CI {no_filter['ci_low']:.6g}-{no_filter['ci_high']:.6g}).
- Rate ratio (no filter / selected): **{improvement:.3g}x**.
- Same selected gate with herald flags hidden from the decoder: **{blind.logical_error_rate:.6g}**.
- Selected-gate distance-3 to distance-7 rate ratio: **{summary['selected_gate_distance_3_to_7_ratio']:.3g}** (significant suppression: **{selected_suppresses}**).
- No-filter distance-3 to distance-7 rate ratio: **{summary['no_filter_distance_3_to_7_ratio']:.3g}** (significant suppression: **{unfiltered_suppresses}**).

## Interpretation

The result is evidence for the tradeoff within the specified Gaussian detuning model and decoder mapping. It is not evidence for a device-independent optimum, a full six-ring/RHG architecture, or a photonic fault-tolerance threshold. The next useful extension is to replace the hard gate with a calibrated time-dependent soft/phase-aware decision rule and test it under non-Gaussian wavepackets and imperfect heralds.
"""
    (output_dir / "REPORT.md").write_text(report, encoding="utf-8")
    return summary
