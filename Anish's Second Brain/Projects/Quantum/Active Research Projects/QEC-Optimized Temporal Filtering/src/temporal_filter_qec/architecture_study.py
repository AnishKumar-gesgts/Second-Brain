"""Frozen pilot/held-out study for the 12-valent fusion-bulk proxy."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .fusion_events import FusionEventTable, compile_fusion_events
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


def _split(correlation_fraction: float) -> dict[str, float]:
    single = (1.0 - correlation_fraction) / 2.0
    return {
        "wrong_xx_fraction": single,
        "wrong_zz_fraction": single,
        "wrong_xx_zz_fraction": correlation_fraction,
    }


def _independent_outcome_table(p_error: float) -> FusionEventTable:
    total_wrong = 2.0 * p_error - p_error**2
    return FusionEventTable(
        gate_width_ps=None,
        correct=(1.0 - p_error) ** 2,
        wrong_xx=p_error * (1.0 - p_error),
        wrong_zz=p_error * (1.0 - p_error),
        wrong_xx_zz=p_error**2,
        erasure_xx=0.0,
        erasure_zz=0.0,
        erasure_full_rejected=0.0,
        erasure_full_loss=0.0,
        temporal_acceptance=1.0,
        temporal_rejection=0.0,
        intrinsic_failure_probability=0.0,
        wrong_xx_fraction=p_error * (1.0 - p_error) / total_wrong,
        wrong_zz_fraction=p_error * (1.0 - p_error) / total_wrong,
        wrong_xx_zz_fraction=p_error**2 / total_wrong,
    )


def _plot_calibration(path: Path, rows: list[dict[str, Any]]) -> None:
    fig, ax = plt.subplots(figsize=(7.0, 4.6))
    for p_error in sorted({float(row["independent_outcome_error"]) for row in rows}):
        subset = sorted(
            (row for row in rows if float(row["independent_outcome_error"]) == p_error),
            key=lambda row: int(row["distance"]),
        )
        ax.errorbar(
            [row["distance"] for row in subset],
            [row["logical_error_rate"] for row in subset],
            yerr=[
                [row["logical_error_rate"] - row["ci_low"] for row in subset],
                [row["ci_high"] - row["logical_error_rate"] for row in subset],
            ],
            marker="o",
            capsize=3,
            label=f"p={p_error:.3%}",
        )
    ax.set_xlabel("Periodic bulk distance")
    ax.set_ylabel("Logical winding error per syndrome graph")
    ax.set_xticks(sorted({int(row["distance"]) for row in rows}))
    ax.grid(alpha=0.25)
    ax.legend()
    ax.set_title("12-valent bulk-proxy calibration")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _plot_phase_map(
    path: Path,
    summaries: list[dict[str, Any]],
    detunings: list[float],
    correlations: list[float],
) -> None:
    matrix = np.full((len(correlations), len(detunings)), np.nan)
    for row in summaries:
        i = correlations.index(float(row["wrong_correlation_fraction"]))
        j = detunings.index(float(row["frequency_detuning_ghz"]))
        matrix[i, j] = float(row["heldout_candidate_relative_change"])
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    image = ax.imshow(
        matrix,
        origin="lower",
        aspect="auto",
        cmap="RdYlGn",
        vmin=-0.2,
        vmax=0.2,
    )
    ax.set_xticks(range(len(detunings)), detunings)
    ax.set_yticks(range(len(correlations)), correlations)
    ax.set_xlabel("Mean detuning (GHz)")
    ax.set_ylabel("Wrong XX/ZZ correlation fraction")
    ax.set_title("Held-out candidate change vs no filter at d=5")
    for i in range(len(correlations)):
        for j in range(len(detunings)):
            ax.text(j, i, f"{100 * matrix[i, j]:+.1f}%", ha="center", va="center")
    fig.colorbar(image, ax=ax, label="Relative logical-error reduction")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _plot_reference_scaling(path: Path, rows: list[dict[str, Any]]) -> None:
    fig, ax = plt.subplots(figsize=(7.0, 4.6))
    for label in ("overly_narrow", "pilot_candidate", "no_filter"):
        subset = sorted(
            (row for row in rows if row["role"] == label),
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
            label=f"{label.replace('_', ' ')} ({subset[0]['gate_label'].replace('_', ' ')})",
        )
    ax.set_xlabel("Periodic bulk distance")
    ax.set_ylabel("Logical winding error per syndrome graph")
    ax.set_xticks(sorted({int(row["distance"]) for row in rows}))
    ax.grid(alpha=0.25)
    ax.legend()
    ax.set_title("Reference condition: architecture-aware bulk proxy")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def run_architecture_study(config_path: Path, output_dir: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)
    distances = [int(value) for value in config["distances"]]
    gates: list[float | None] = [float(value) for value in config["gate_widths_ps"]] + [None]
    selection_distance = int(config["selection_distance"])
    detunings = [float(value) for value in config["detunings_ghz"]]
    correlations = [float(value) for value in config["wrong_correlation_fractions"]]

    calibration_rows: list[dict[str, Any]] = []
    for p_index, p_error in enumerate(config["calibration_outcome_errors"]):
        table = _independent_outcome_table(float(p_error))
        for distance in distances:
            estimate = simulate_bulk_component_error(
                table,
                distance,
                int(config["calibration_shots"]),
                int(config["calibration_seed"]) + 1000 * p_index + distance,
            )
            calibration_rows.append(
                {"independent_outcome_error": float(p_error), **estimate.to_dict()}
            )
    _write_csv(output_dir / "threshold_calibration.csv", calibration_rows)
    _plot_calibration(output_dir / "threshold_calibration.png", calibration_rows)

    pilot_rows: list[dict[str, Any]] = []
    condition_tables: dict[tuple[float, float, float | None], FusionEventTable] = {}
    for correlation_index, correlation in enumerate(correlations):
        split = _split(correlation)
        for detuning_index, detuning in enumerate(detunings):
            params = PhysicalParameters(
                wavepacket_sigma_ps=float(config["physical"]["wavepacket_sigma_ps"]),
                detector_jitter_ps=float(config["physical"]["detector_jitter_ps"]),
                frequency_detuning_ghz=detuning,
                detector_efficiency=float(config["physical"]["detector_efficiency"]),
                spectral_diffusion_ghz=float(config["physical"].get("spectral_diffusion_ghz", 0.0)),
            )
            for gate_index, gate in enumerate(gates):
                fusion = compile_fusion_events(
                    event_table(params, gate, grid_points=int(config["temporal_grid_points"])),
                    **split,
                    intrinsic_failure_probability=float(config["intrinsic_failure_probability"]),
                )
                condition_tables[(correlation, detuning, gate)] = fusion
                estimate = simulate_bulk_component_error(
                    fusion,
                    selection_distance,
                    int(config["pilot_shots"]),
                    int(config["pilot_seed"])
                    + 100_000 * correlation_index
                    + 1000 * detuning_index
                    + gate_index,
                )
                pilot_rows.append(
                    {
                        "wrong_correlation_fraction": correlation,
                        "frequency_detuning_ghz": detuning,
                        "gate_width_ps": gate,
                        "gate_label": _gate_label(gate),
                        **fusion.to_dict(),
                        **estimate.to_dict(),
                    }
                )
    _write_csv(output_dir / "pilot_sweep.csv", pilot_rows)

    heldout_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for correlation_index, correlation in enumerate(correlations):
        for detuning_index, detuning in enumerate(detunings):
            subset = [
                row
                for row in pilot_rows
                if row["wrong_correlation_fraction"] == correlation
                and row["frequency_detuning_ghz"] == detuning
            ]
            no_filter_pilot = next(row for row in subset if row["gate_width_ps"] is None)
            finite = [row for row in subset if row["gate_width_ps"] is not None]
            candidate = min(finite, key=lambda row: row["logical_error_rate"])
            guard_passed = candidate["ci_high"] < no_filter_pilot["ci_low"]
            selected_gate = candidate["gate_width_ps"] if guard_passed else None
            role_gates = {
                "selected": selected_gate,
                "pilot_candidate": candidate["gate_width_ps"],
                "no_filter": None,
            }
            is_reference = (
                detuning == float(config["reference_condition"]["detuning_ghz"])
                and correlation
                == float(config["reference_condition"]["wrong_correlation_fraction"])
            )
            if is_reference:
                role_gates["overly_narrow"] = float(config["overly_narrow_gate_ps"])
            cached: dict[tuple[float | None, int], dict[str, Any]] = {}
            for gate_index, gate in enumerate(dict.fromkeys(role_gates.values())):
                fusion = condition_tables[(correlation, detuning, gate)]
                for distance in distances:
                    estimate = simulate_bulk_component_error(
                        fusion,
                        distance,
                        int(config["heldout_shots"]),
                        int(config["heldout_seed"])
                        + 100_000 * correlation_index
                        + 10_000 * detuning_index
                        + 100 * gate_index
                        + distance,
                    )
                    cached[(gate, distance)] = {
                        "wrong_correlation_fraction": correlation,
                        "frequency_detuning_ghz": detuning,
                        "gate_width_ps": gate,
                        "gate_label": _gate_label(gate),
                        **fusion.to_dict(),
                        **estimate.to_dict(),
                    }
            for role, gate in role_gates.items():
                for distance in distances:
                    heldout_rows.append({"role": role, **cached[(gate, distance)]})

            candidate_d5 = cached[(candidate["gate_width_ps"], selection_distance)]
            no_filter_d5 = cached[(None, selection_distance)]
            relative_change = 1.0 - candidate_d5["logical_error_rate"] / no_filter_d5["logical_error_rate"] if no_filter_d5["logical_error_rate"] else 0.0
            summaries.append(
                {
                    "wrong_correlation_fraction": correlation,
                    "frequency_detuning_ghz": detuning,
                    "pilot_candidate_gate_ps": candidate["gate_width_ps"],
                    "selection_passed_confidence_guard": guard_passed,
                    "selected_gate_ps": selected_gate,
                    "heldout_candidate_rate": candidate_d5["logical_error_rate"],
                    "heldout_candidate_ci_low": candidate_d5["ci_low"],
                    "heldout_candidate_ci_high": candidate_d5["ci_high"],
                    "heldout_no_filter_rate": no_filter_d5["logical_error_rate"],
                    "heldout_no_filter_ci_low": no_filter_d5["ci_low"],
                    "heldout_no_filter_ci_high": no_filter_d5["ci_high"],
                    "heldout_candidate_relative_change": relative_change,
                    "heldout_significant_improvement": candidate_d5["ci_high"] < no_filter_d5["ci_low"],
                    "heldout_significant_harm": candidate_d5["ci_low"] > no_filter_d5["ci_high"],
                }
            )
    _write_csv(output_dir / "heldout_scaling.csv", heldout_rows)
    _write_csv(output_dir / "condition_summary.csv", summaries)
    _plot_phase_map(output_dir / "heldout_phase_map.png", summaries, detunings, correlations)

    reference = config["reference_condition"]
    reference_rows = [
        row
        for row in heldout_rows
        if row["frequency_detuning_ghz"] == float(reference["detuning_ghz"])
        and row["wrong_correlation_fraction"] == float(reference["wrong_correlation_fraction"])
    ]
    _plot_reference_scaling(output_dir / "reference_distance_scaling.png", reference_rows)

    missed_rows: list[dict[str, Any]] = []
    reference_candidate_gate = next(
        row["pilot_candidate_gate_ps"]
        for row in summaries
        if row["frequency_detuning_ghz"] == float(reference["detuning_ghz"])
        and row["wrong_correlation_fraction"] == float(reference["wrong_correlation_fraction"])
    )
    reference_table = condition_tables[
        (
            float(reference["wrong_correlation_fraction"]),
            float(reference["detuning_ghz"]),
            reference_candidate_gate,
        )
    ]
    for missed_index, missed in enumerate(config["missed_erasure_fractions"]):
        estimate = simulate_bulk_component_error(
            reference_table,
            selection_distance,
            int(config["heldout_shots"]),
            int(config["heldout_seed"]) + 900_000 + missed_index,
            missed_erasure_fraction=float(missed),
        )
        missed_rows.append(
            {
                "gate_width_ps": reference_candidate_gate,
                "frequency_detuning_ghz": float(reference["detuning_ghz"]),
                "wrong_correlation_fraction": float(reference["wrong_correlation_fraction"]),
                **estimate.to_dict(),
            }
        )
    _write_csv(output_dir / "missed_herald_control.csv", missed_rows)

    failure_rows: list[dict[str, Any]] = []
    reference_params = PhysicalParameters(
        wavepacket_sigma_ps=float(config["physical"]["wavepacket_sigma_ps"]),
        detector_jitter_ps=float(config["physical"]["detector_jitter_ps"]),
        frequency_detuning_ghz=float(reference["detuning_ghz"]),
        detector_efficiency=float(config["physical"]["detector_efficiency"]),
        spectral_diffusion_ghz=float(config["physical"].get("spectral_diffusion_ghz", 0.0)),
    )
    for failure_index, intrinsic_failure in enumerate(config["intrinsic_failure_controls"]):
        fusion = compile_fusion_events(
            event_table(reference_params, None, grid_points=int(config["temporal_grid_points"])),
            **_split(float(reference["wrong_correlation_fraction"])),
            intrinsic_failure_probability=float(intrinsic_failure),
        )
        for distance in distances:
            estimate = simulate_bulk_component_error(
                fusion,
                distance,
                int(config["heldout_shots"]),
                int(config["heldout_seed"]) + 950_000 + 100 * failure_index + distance,
            )
            failure_rows.append(
                {
                    "intrinsic_failure_probability": float(intrinsic_failure),
                    **fusion.to_dict(),
                    **estimate.to_dict(),
                }
            )
    _write_csv(output_dir / "intrinsic_failure_control.csv", failure_rows)

    calibration_by_p = {
        str(p): [
            row for row in calibration_rows if row["independent_outcome_error"] == p
        ]
        for p in sorted({row["independent_outcome_error"] for row in calibration_rows})
    }
    significant_improvements = sum(bool(row["heldout_significant_improvement"]) for row in summaries)
    significant_harms = sum(bool(row["heldout_significant_harm"]) for row in summaries)
    guard_passes = sum(bool(row["selection_passed_confidence_guard"]) for row in summaries)
    summary = {
        "config": config,
        "model": {
            "label": "periodic 12-valent six-ring bulk syndrome-graph proxy",
            "implemented": [
                "paired XX/ZZ fusion-event schema",
                "12-valent periodic bulk syndrome graph",
                "per-outcome erasure flags",
                "MWPM logical-winding decoding",
                "correlated wrong-XX/wrong-ZZ sensitivity",
                "intrinsic partial-erasure stress control",
            ],
            "not_implemented": [
                "explicit six-ring resource-state stabilizer construction",
                "published half-cell primal/dual crossing map",
                "planar logical-block boundaries",
                "architecture-scale multimode Fock simulation",
                "protocol-derived optical XX/ZZ error split",
            ],
        },
        "calibration": calibration_by_p,
        "conditions": summaries,
        "selection_guard_passes": guard_passes,
        "heldout_significant_improvements": significant_improvements,
        "heldout_significant_harms": significant_harms,
        "claim_boundary": "Architecture-aware periodic bulk proxy; not a native six-ring/RHG logical block, threshold estimate, multimode optical validation, or hardware result.",
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    report = f"""# Fusion-bulk proxy result

## Verdict

The architecture-aware upgrade **does not support** carrying the earlier surface-code-proxy improvement into the six-ring bulk model. None of the {len(summaries)} predeclared detuning/correlation conditions passed the pilot confidence guard, and the independent held-out comparison found {significant_improvements} significant candidate improvements and {significant_harms} significant harms.

The negative result has a direct mechanism. The six-ring bulk calibration changes from distance suppression near 0.5% independent error per fusion outcome to distance growth near 1.5%, with a crossing around 1%. At the original 1.2 GHz reference condition, the compiled wrong-outcome probability is several times larger than that scale even after filtering. Narrow gates reduce wrong outcomes but replace them with full XX/ZZ erasures quickly enough to saturate the logical winding measurement.

## What this establishes

- The new compiler preserves mutually exclusive correct, wrong-XX, wrong-ZZ, correlated-wrong, partial-erasure, full-rejection, and loss branches.
- The scalable benchmark uses a periodic 12-valent cubic-with-diagonals syndrome graph and decodes a noncontractible logical winding with MWPM.
- Pilot selection and held-out evaluation use frozen independent seeds and Wilson intervals.
- The unknown optical split between XX-only, ZZ-only, and correlated wrong outcomes is exposed as a sensitivity axis rather than fixed implicitly.
- The 40 ps control and 25% intrinsic fusion-failure control both test whether apparent fidelity gains are only produced by erasing too many outcomes.

## What this does not establish

This is not yet a native six-ring/RHG logical block. The code does not construct the six-qubit resource stabilizers, the exact half-cell-shifted primal/dual crossing map, or published planar boundaries from the fusion complex. It also does not derive the XX/ZZ split from a multimode type-II fusion calculation. Therefore, the result is evidence that the earlier gain is fragile under a threshold-calibrated architecture-aware mapping, not a six-ring threshold or hardware-performance claim.

At the 1.2 GHz reference condition, the 40 ps control converts 65.1% of fusion events into full erasure and remains saturated near 0.5 logical error per syndrome graph. A 25% intrinsic fusion-failure control is also saturated. Missed-herald sensitivity is not identifiable at this reference point because every tested herald quality lies within the same already-random regime.
"""
    (output_dir / "REPORT.md").write_text(report, encoding="utf-8")
    return summary
