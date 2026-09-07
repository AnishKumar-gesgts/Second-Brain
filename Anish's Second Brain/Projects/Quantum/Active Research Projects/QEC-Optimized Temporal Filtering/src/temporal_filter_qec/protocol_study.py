"""Predeclared protocol-specific type-II fusion study on the six-ring bulk graph."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .fusion_events import FusionEventTable, compile_type_ii_detuning_events
from .fusion_network import simulate_bulk_component_error
from .physics import PhysicalParameters, event_table


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _gate_label(gate: float | None) -> str:
    return "no_filter" if gate is None else f"{gate:g}_ps"


def _simulate(
    table: FusionEventTable,
    distance: int,
    shots: int,
    seed: int,
) -> dict[str, Any]:
    return simulate_bulk_component_error(
        table,
        distance,
        shots,
        seed,
        channel_profile="six_ring_type_ii",
    ).to_dict()


def _plot_map(
    path: Path,
    summaries: list[dict[str, Any]],
    detunings: list[float],
    jitters: list[float],
) -> None:
    matrix = np.full((len(jitters), len(detunings)), np.nan)
    for row in summaries:
        i = jitters.index(float(row["detector_jitter_ps"]))
        j = detunings.index(float(row["frequency_detuning_ghz"]))
        matrix[i, j] = 100.0 * float(row["heldout_relative_reduction"])
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    image = ax.imshow(matrix, origin="lower", aspect="auto", cmap="RdYlGn", vmin=-25, vmax=25)
    ax.set_xticks(range(len(detunings)), detunings)
    ax.set_yticks(range(len(jitters)), jitters)
    ax.set_xlabel("Mean detuning (GHz)")
    ax.set_ylabel("Detector jitter (ps)")
    ax.set_title("Held-out temporal-filter change at d=5")
    for i in range(len(jitters)):
        for j in range(len(detunings)):
            ax.text(j, i, f"{matrix[i, j]:+.1f}%", ha="center", va="center")
    fig.colorbar(image, ax=ax, label="Relative logical-error reduction")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _plot_reference(path: Path, rows: list[dict[str, Any]]) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for role in ("narrow_control", "pilot_candidate", "no_filter"):
        subset = sorted(
            (row for row in rows if row["role"] == role),
            key=lambda row: int(row["distance"]),
        )
        if not subset:
            continue
        ax.errorbar(
            [row["distance"] for row in subset],
            [row["logical_error_rate"] for row in subset],
            yerr=[
                [row["logical_error_rate"] - row["ci_low"] for row in subset],
                [row["ci_high"] - row["logical_error_rate"] for row in subset],
            ],
            marker="o",
            capsize=3,
            label=f"{role.replace('_', ' ')} ({subset[0]['gate_label'].replace('_', ' ')})",
        )
    ax.set_xlabel("Periodic bulk distance")
    ax.set_ylabel("Logical winding error")
    ax.set_xticks(sorted({int(row["distance"]) for row in rows}))
    ax.grid(alpha=0.25)
    ax.legend()
    ax.set_title("Protocol-specific reference condition")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def run_protocol_study(config_path: Path, output_dir: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)
    detunings = [float(value) for value in config["detunings_ghz"]]
    jitters = [float(value) for value in config["detector_jitters_ps"]]
    distances = [int(value) for value in config["distances"]]
    selection_distance = int(config["selection_distance"])
    gates: list[float | None] = [float(value) for value in config["gate_widths_ps"]] + [None]

    tables: dict[tuple[float, float, float | None], FusionEventTable] = {}
    pilot_rows: list[dict[str, Any]] = []
    for jitter_index, jitter in enumerate(jitters):
        for detuning_index, detuning in enumerate(detunings):
            params = PhysicalParameters(
                wavepacket_sigma_ps=float(config["physical"]["wavepacket_sigma_ps"]),
                detector_jitter_ps=jitter,
                frequency_detuning_ghz=detuning,
                detector_efficiency=float(config["physical"]["detector_efficiency"]),
                spectral_diffusion_ghz=float(config["physical"].get("spectral_diffusion_ghz", 0.0)),
            )
            for gate_index, gate in enumerate(gates):
                table = compile_type_ii_detuning_events(
                    event_table(params, gate, grid_points=int(config["temporal_grid_points"])),
                    intrinsic_failure_probability=float(config["intrinsic_failure_probability"]),
                )
                tables[(jitter, detuning, gate)] = table
                estimate = _simulate(
                    table,
                    selection_distance,
                    int(config["pilot_shots"]),
                    int(config["pilot_seed"]) + 100_000 * jitter_index + 1000 * detuning_index + gate_index,
                )
                pilot_rows.append(
                    {
                        "detector_jitter_ps": jitter,
                        "frequency_detuning_ghz": detuning,
                        "gate_width_ps": gate,
                        "gate_label": _gate_label(gate),
                        **table.to_dict(),
                        **estimate,
                    }
                )
    _write_csv(output_dir / "pilot_sweep.csv", pilot_rows)

    heldout_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    reference = config["reference_condition"]
    for jitter_index, jitter in enumerate(jitters):
        for detuning_index, detuning in enumerate(detunings):
            subset = [
                row for row in pilot_rows
                if row["detector_jitter_ps"] == jitter
                and row["frequency_detuning_ghz"] == detuning
            ]
            no_filter_pilot = next(row for row in subset if row["gate_width_ps"] is None)
            candidate = min(
                (row for row in subset if row["gate_width_ps"] is not None),
                key=lambda row: row["logical_error_rate"],
            )
            guard_passed = candidate["ci_high"] < no_filter_pilot["ci_low"]
            role_gates: dict[str, float | None] = {
                "pilot_candidate": float(candidate["gate_width_ps"]),
                "no_filter": None,
            }
            if jitter == float(reference["detector_jitter_ps"]) and detuning == float(reference["detuning_ghz"]):
                role_gates["narrow_control"] = float(config["narrow_control_gate_ps"])

            cached: dict[tuple[float | None, int], dict[str, Any]] = {}
            for gate_index, gate in enumerate(dict.fromkeys(role_gates.values())):
                table = tables[(jitter, detuning, gate)]
                for distance in distances:
                    estimate = _simulate(
                        table,
                        distance,
                        int(config["heldout_shots"]),
                        int(config["heldout_seed"]) + 100_000 * jitter_index + 10_000 * detuning_index + 100 * gate_index + distance,
                    )
                    cached[(gate, distance)] = {
                        "detector_jitter_ps": jitter,
                        "frequency_detuning_ghz": detuning,
                        "gate_width_ps": gate,
                        "gate_label": _gate_label(gate),
                        **table.to_dict(),
                        **estimate,
                    }
            for role, gate in role_gates.items():
                for distance in distances:
                    heldout_rows.append({"role": role, **cached[(gate, distance)]})

            candidate_d = cached[(float(candidate["gate_width_ps"]), selection_distance)]
            no_filter_d = cached[(None, selection_distance)]
            no_filter_rate = float(no_filter_d["logical_error_rate"])
            relative_reduction = (
                1.0 - float(candidate_d["logical_error_rate"]) / no_filter_rate
                if no_filter_rate else 0.0
            )
            summaries.append(
                {
                    "detector_jitter_ps": jitter,
                    "frequency_detuning_ghz": detuning,
                    "pilot_candidate_gate_ps": candidate["gate_width_ps"],
                    "pilot_confidence_guard_passed": guard_passed,
                    "heldout_candidate_rate": candidate_d["logical_error_rate"],
                    "heldout_candidate_ci_low": candidate_d["ci_low"],
                    "heldout_candidate_ci_high": candidate_d["ci_high"],
                    "heldout_no_filter_rate": no_filter_rate,
                    "heldout_no_filter_ci_low": no_filter_d["ci_low"],
                    "heldout_no_filter_ci_high": no_filter_d["ci_high"],
                    "heldout_relative_reduction": relative_reduction,
                    "heldout_significant_improvement": candidate_d["ci_high"] < no_filter_d["ci_low"],
                    "heldout_significant_harm": candidate_d["ci_low"] > no_filter_d["ci_high"],
                }
            )

    _write_csv(output_dir / "heldout_scaling.csv", heldout_rows)
    _write_csv(output_dir / "condition_summary.csv", summaries)
    _plot_map(output_dir / "heldout_phase_map.png", summaries, detunings, jitters)
    reference_rows = [
        row for row in heldout_rows
        if row["detector_jitter_ps"] == float(reference["detector_jitter_ps"])
        and row["frequency_detuning_ghz"] == float(reference["detuning_ghz"])
    ]
    _plot_reference(output_dir / "reference_distance_scaling.png", reference_rows)

    significant = [row for row in summaries if row["heldout_significant_improvement"]]
    guards = [row for row in summaries if row["pilot_confidence_guard_passed"]]
    relative_changes = [float(row["heldout_relative_reduction"]) for row in summaries]
    stop_branch = len(significant) == 0
    broad_by_detuning = {
        str(detuning): sum(
            bool(row["heldout_significant_improvement"])
            for row in summaries
            if row["frequency_detuning_ghz"] == detuning
        )
        for detuning in detunings
    }
    result = {
        "config": config,
        "protocol_mapping": {
            "accepted_detuning_error": "ZZ-outcome flip only",
            "xx_edges": "three cubic-axis directions per vertex",
            "zz_edges": "three face-diagonal directions per vertex",
            "full_erasure": "temporal rejection or photon loss",
            "source": "Chan et al., PRX Quantum 6, 020304 (2025), Appendix F",
        },
        "conditions": summaries,
        "pilot_guard_passes": len(guards),
        "heldout_significant_improvements": len(significant),
        "significant_improvements_by_detuning": broad_by_detuning,
        "stopping_rule": "Stop if support requires a materially narrower operating corner or does not show a broad, exceptional architecture-level advantage.",
        "decision": "stop" if stop_branch else "reassess breadth before continuing",
        "decision_reason": (
            "No held-out condition significantly improved; further optimization would narrow the hypothesis without demonstrated architecture-level advantage."
            if stop_branch
            else "At least one held-out condition improved; breadth and distance scaling still require assessment."
        ),
        "claim_boundary": "Periodic six-ring bulk syndrome graph with the published type-II outcome map; not a planar logical block, full resource-state circuit, source/device experiment, or hardware validation.",
    }
    (output_dir / "summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    report = f"""# Protocol-specific six-ring bulk result

## Decision evidence

The predeclared study tested {len(summaries)} detuning/jitter conditions. {len(guards)} passed the pilot confidence guard, and {len(significant)} showed a nonoverlapping-95%-interval improvement in the independent held-out comparison at distance {selection_distance}.

The compiler now uses the published type-II mapping: detuning-induced partial distinguishability flips only the `ZZ` measurement outcome, while each six-ring syndrome graph assigns `XX` outcomes to cubic-axis edges and `ZZ` outcomes to face diagonals. Temporal rejection and loss erase both kinds of edge.

This is the decisive test for the current project hypothesis. A continuation is justified only if the benefit is broad across the predeclared physical grid and remains favorable as distance increases. A benefit confined to a small tuned corner is recorded but does not justify narrowing the original top-journal-scale claim.

The observed relative changes ranged from {100 * max(relative_changes):.2f}% better to {-100 * min(relative_changes):.2f}% worse, with overlapping 95% Wilson intervals in every condition.

## Stopping decision

{"Stop this gate-optimization branch. No held-out condition significantly improved, so further tuning would narrow the original hypothesis without demonstrating an architecture-level advantage." if stop_branch else "Reassess the breadth and distance scaling of the supported conditions before deciding whether to continue."}

## Claim boundary

This is a periodic bulk syndrome-graph calculation, not a planar logical block, a full six-ring resource-state circuit, a multimode Fock-space device simulation, an experiment, or hardware validation.
"""
    (output_dir / "REPORT.md").write_text(report, encoding="utf-8")
    return result
