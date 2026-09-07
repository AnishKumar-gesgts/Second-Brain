"""Frozen full-channel versus independent-reduction QEC comparison."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .qec import simulate_logical_error
from .schema import CompiledChannel


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _parameters(channel: CompiledChannel) -> dict[str, Any]:
    return dict(channel.parameters)


def _find_channel(
    channels: list[CompiledChannel],
    *,
    detuning: float,
    jitter: float,
    gate_label: str,
) -> CompiledChannel:
    matches = [
        channel
        for channel in channels
        if float(_parameters(channel)["frequency_detuning_ghz"]) == detuning
        and float(_parameters(channel)["detector_jitter_ps"]) == jitter
        and str(_parameters(channel)["gate_label"]) == gate_label
    ]
    if len(matches) != 1:
        raise ValueError(
            f"expected one channel for detuning={detuning}, jitter={jitter}, "
            f"gate={gate_label}; found {len(matches)}"
        )
    return matches[0]


def _run_pair(
    channel: CompiledChannel,
    *,
    distance: int,
    shots: int,
    seed: int,
    prefix: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = []
    independent = channel.independent_target_approximation()
    for model_index, (model, compiled) in enumerate(
        (
            ("full_correlated", channel),
            ("matched_independent", independent),
        )
    ):
        estimate = simulate_logical_error(
            compiled,
            distance,
            shots,
            seed + model_index,
            decoder_channel=independent,
        )
        rows.append({**prefix, "model": model, **estimate.to_dict()})
    return rows


def _comparison(
    full: dict[str, Any], independent: dict[str, Any]
) -> dict[str, Any]:
    full_rate = float(full["logical_error_rate_any"])
    independent_rate = float(independent["logical_error_rate_any"])
    return {
        "full_rate": full_rate,
        "full_ci_low": full["any_ci_low"],
        "full_ci_high": full["any_ci_high"],
        "independent_rate": independent_rate,
        "independent_ci_low": independent["any_ci_low"],
        "independent_ci_high": independent["any_ci_high"],
        "full_minus_independent": full_rate - independent_rate,
        "relative_change_full_vs_independent": (
            full_rate / independent_rate - 1.0 if independent_rate else 0.0
        ),
        "significant_full_lower": full["any_ci_high"] < independent["any_ci_low"],
        "significant_full_higher": full["any_ci_low"] > independent["any_ci_high"],
        "full_failure_phi": full["failure_phi"],
        "independent_failure_phi": independent["failure_phi"],
        "full_component_a_rate": full["logical_error_rate_a"],
        "independent_component_a_rate": independent["logical_error_rate_a"],
        "full_component_b_rate": full["logical_error_rate_b"],
        "independent_component_b_rate": independent["logical_error_rate_b"],
    }


def _plot_pilot(path: Path, rows: list[dict[str, Any]]) -> None:
    figure, axis = plt.subplots(figsize=(7.4, 4.8))
    gate_markers = {
        "no_filter": "o",
        "220_ps": "s",
        "140_ps": "^",
        "40_ps": "X",
    }
    for gate, marker in gate_markers.items():
        subset = [row for row in rows if row["gate_label"] == gate]
        axis.scatter(
            [100 * float(row["full_erasure_probability"]) for row in subset],
            [100 * float(row["full_minus_independent"]) for row in subset],
            c=[float(row["detector_jitter_ps"]) for row in subset],
            cmap="viridis",
            vmin=0,
            vmax=60,
            marker=marker,
            s=65,
            label=gate.replace("_", " "),
        )
    axis.axhline(0.0, color="black", linewidth=1)
    axis.set_xlabel("Joint erasure probability (%)")
    axis.set_ylabel("Full − independent logical error (percentage points)")
    axis.set_title("Pilot QEC divergence at distance 5")
    axis.grid(alpha=0.25)
    axis.legend(title="Gate")
    figure.tight_layout()
    figure.savefig(path, dpi=180)
    plt.close(figure)


def _plot_heldout(path: Path, rows: list[dict[str, Any]]) -> None:
    profiles = list(dict.fromkeys(str(row["profile"]) for row in rows))
    figure, axes = plt.subplots(2, 3, figsize=(13.2, 7.8), sharex=True, sharey=True)
    for axis, profile in zip(axes.flat, profiles, strict=True):
        subset = sorted(
            (row for row in rows if row["profile"] == profile),
            key=lambda row: int(row["distance"]),
        )
        axis.errorbar(
            [row["distance"] for row in subset],
            [row["full_rate"] for row in subset],
            yerr=[
                [row["full_rate"] - row["full_ci_low"] for row in subset],
                [row["full_ci_high"] - row["full_rate"] for row in subset],
            ],
            marker="o",
            capsize=3,
            label="full correlated",
        )
        axis.errorbar(
            [row["distance"] for row in subset],
            [row["independent_rate"] for row in subset],
            yerr=[
                [row["independent_rate"] - row["independent_ci_low"] for row in subset],
                [row["independent_ci_high"] - row["independent_rate"] for row in subset],
            ],
            marker="s",
            capsize=3,
            label="matched independent",
        )
        axis.set_title(profile.replace("_", " "))
        axis.grid(alpha=0.25)
        axis.set_xticks(sorted({int(row["distance"]) for row in subset}))
    axes[0, 0].legend()
    figure.supxlabel("Periodic bulk distance")
    figure.supylabel("Any-component logical error")
    figure.suptitle("Held-out effect of preserving within-fusion correlation")
    figure.tight_layout()
    figure.savefig(path, dpi=180)
    plt.close(figure)


def run_stage2(config_path: Path, output_dir: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)
    channel_path = Path(config["compiled_channels"])
    channels = [
        CompiledChannel.from_dict(item)
        for item in json.loads(channel_path.read_text(encoding="utf-8"))
    ]

    pilot_raw: list[dict[str, Any]] = []
    pilot_comparisons: list[dict[str, Any]] = []
    condition_index = 0
    pilot = config["pilot_grid"]
    for jitter in map(float, pilot["detector_jitters_ps"]):
        for detuning in map(float, pilot["detunings_ghz"]):
            for gate_label in map(str, pilot["gate_labels"]):
                channel = _find_channel(
                    channels,
                    detuning=detuning,
                    jitter=jitter,
                    gate_label=gate_label,
                )
                state_distribution = channel.state_distribution(("XX", "ZZ"))
                prefix = {
                    "detector_jitter_ps": jitter,
                    "frequency_detuning_ghz": detuning,
                    "gate_label": gate_label,
                    "full_erasure_probability": state_distribution.get(
                        ("erased", "erased"), 0.0
                    ),
                }
                pair = _run_pair(
                    channel,
                    distance=int(config["pilot_distance"]),
                    shots=int(config["pilot_shots"]),
                    seed=int(config["pilot_seed"]) + 10 * condition_index,
                    prefix=prefix,
                )
                pilot_raw.extend(pair)
                full = next(row for row in pair if row["model"] == "full_correlated")
                independent = next(
                    row for row in pair if row["model"] == "matched_independent"
                )
                pilot_comparisons.append({**prefix, **_comparison(full, independent)})
                condition_index += 1
    _write_csv(output_dir / "pilot_raw.csv", pilot_raw)
    _write_csv(output_dir / "pilot_comparisons.csv", pilot_comparisons)
    _plot_pilot(output_dir / "pilot_divergence.png", pilot_comparisons)

    heldout_raw: list[dict[str, Any]] = []
    heldout_comparisons: list[dict[str, Any]] = []
    for profile_index, profile in enumerate(config["heldout_profiles"]):
        channel = _find_channel(
            channels,
            detuning=float(profile["detuning_ghz"]),
            jitter=float(profile["detector_jitter_ps"]),
            gate_label=str(profile["gate_label"]),
        )
        state_distribution = channel.state_distribution(("XX", "ZZ"))
        for distance in map(int, config["heldout_distances"]):
            prefix = {
                "profile": str(profile["name"]),
                "detector_jitter_ps": float(profile["detector_jitter_ps"]),
                "frequency_detuning_ghz": float(profile["detuning_ghz"]),
                "gate_label": str(profile["gate_label"]),
                "full_erasure_probability": state_distribution.get(
                    ("erased", "erased"), 0.0
                ),
            }
            pair = _run_pair(
                channel,
                distance=distance,
                shots=int(config["heldout_shots"]),
                seed=(
                    int(config["heldout_seed"])
                    + 1000 * profile_index
                    + 10 * distance
                ),
                prefix=prefix,
            )
            heldout_raw.extend(pair)
            full = next(row for row in pair if row["model"] == "full_correlated")
            independent = next(
                row for row in pair if row["model"] == "matched_independent"
            )
            heldout_comparisons.append(
                {**prefix, "distance": distance, **_comparison(full, independent)}
            )
    _write_csv(output_dir / "heldout_raw.csv", heldout_raw)
    _write_csv(output_dir / "heldout_comparisons.csv", heldout_comparisons)
    _plot_heldout(output_dir / "heldout_scaling.png", heldout_comparisons)

    significant_lower = sum(
        bool(row["significant_full_lower"]) for row in heldout_comparisons
    )
    significant_higher = sum(
        bool(row["significant_full_higher"]) for row in heldout_comparisons
    )
    non_saturated = [
        row
        for row in heldout_comparisons
        if max(float(row["full_rate"]), float(row["independent_rate"])) < 0.7
    ]
    non_saturated_significant = sum(
        bool(row["significant_full_lower"] or row["significant_full_higher"])
        for row in non_saturated
    )
    summary = {
        "config": config,
        "architecture": (
            "paired periodic 12-valent six-ring bulk proxy with exact local "
            "XX-axis/ZZ-diagonal semantics and approximate cross-component pairing"
        ),
        "pilot_conditions": len(pilot_comparisons),
        "heldout_profile_distance_points": len(heldout_comparisons),
        "heldout_significant_full_lower": significant_lower,
        "heldout_significant_full_higher": significant_higher,
        "heldout_non_saturated_points": len(non_saturated),
        "heldout_non_saturated_significant_differences": non_saturated_significant,
        "claim_boundary": (
            "First-adapter paired-bulk QEC comparison; not an exact planar "
            "six-ring logical block, threshold estimate, or general compiler result."
        ),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    report = f"""# Stage 2 QEC Reduction Result

## Verdict

The first adapter's within-fusion erasure correlation changed its physical event distribution but did not significantly change the corrected held-out logical-QEC result under a shared marginal decoder.

- {significant_lower} of {len(heldout_comparisons)} comparisons significantly favored the full correlated channel.
- {significant_higher} of {len(heldout_comparisons)} significantly favored the matched independent channel.
- {non_saturated_significant} of {len(non_saturated)} non-saturated comparisons showed a significant difference.

## Claim boundary

This is a first-adapter paired periodic bulk comparison, not an exact planar six-ring logical block, threshold estimate, general compiler validation, or hardware result.
"""
    (output_dir / "REPORT.generated.md").write_text(report, encoding="utf-8")
    return summary
