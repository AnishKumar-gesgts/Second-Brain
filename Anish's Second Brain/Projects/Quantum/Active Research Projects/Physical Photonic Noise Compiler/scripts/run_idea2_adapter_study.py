from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt

from photonic_noise_compiler.adapters import (
    ScalarTemporalTable,
    compile_temporal_type_ii,
)
from photonic_noise_compiler.diagnostics import compare_with_independent


DEFAULT_SOURCE = Path(
    "../QEC-Optimized Temporal Filtering/results/protocol_exact/pilot_sweep.csv"
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument(
        "--output", type=Path, default=Path("results/idea2_adapter")
    )
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    with args.source.open(newline="", encoding="utf-8") as handle:
        source_rows = list(csv.DictReader(handle))

    rows: list[dict[str, object]] = []
    channels = []
    for source_row in source_rows:
        jitter = float(source_row["detector_jitter_ps"])
        detuning = float(source_row["frequency_detuning_ghz"])
        gate_label = source_row["gate_label"]
        parameters = {
            "detector_jitter_ps": jitter,
            "frequency_detuning_ghz": detuning,
            "gate_label": gate_label,
        }
        channel = compile_temporal_type_ii(
            ScalarTemporalTable.from_idea2_row(source_row),
            name=f"idea2_j{jitter:g}_d{detuning:g}_{gate_label}",
            parameters=parameters,
            source_provenance=(str(args.source.resolve()),),
        )
        channels.append(channel)
        rows.append({**parameters, **compare_with_independent(channel)})

    with (args.output / "channel_diagnostics.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (args.output / "compiled_channels.json").write_text(
        json.dumps([channel.to_dict() for channel in channels], indent=2),
        encoding="utf-8",
    )

    max_tv = max(float(row["total_variation_from_independent"]) for row in rows)
    max_partial = max(
        float(row["independent_synthetic_partial_erasure_probability"])
        for row in rows
    )
    gate_summaries = {}
    for gate_label in sorted({str(row["gate_label"]) for row in rows}):
        subset = [row for row in rows if row["gate_label"] == gate_label]
        gate_summaries[gate_label] = {
            "minimum_full_erasure_probability": min(
                float(row["full_erasure_probability"]) for row in subset
            ),
            "maximum_full_erasure_probability": max(
                float(row["full_erasure_probability"]) for row in subset
            ),
            "minimum_total_variation": min(
                float(row["total_variation_from_independent"]) for row in subset
            ),
            "maximum_total_variation": max(
                float(row["total_variation_from_independent"]) for row in subset
            ),
        }
    summary = {
        "source": str(args.source.resolve()),
        "channels_compiled": len(channels),
        "probability_conservation_passes": sum(
            abs(channel.total_probability - 1.0) <= 1e-10
            for channel in channels
        ),
        "maximum_total_variation_from_independent": max_tv,
        "maximum_synthetic_partial_erasure_probability": max_partial,
        "by_gate": gate_summaries,
        "interpretation": (
            "The matched independent approximation preserves each XX/ZZ target "
            "marginal but invents partial-erasure branches absent from the physical "
            "temporal channel. This is interface-level evidence only; logical "
            "consequences require Stage 2."
        ),
        "claim_boundary": (
            "First-adapter contract validation, not general compiler validation "
            "or a logical-QEC result."
        ),
    }
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    figure, axis = plt.subplots(figsize=(7.2, 4.8))
    scatter = axis.scatter(
        [float(row["full_erasure_probability"]) for row in rows],
        [float(row["total_variation_from_independent"]) for row in rows],
        c=[float(row["detector_jitter_ps"]) for row in rows],
        cmap="viridis",
        alpha=0.8,
    )
    axis.set_xlabel("Physical joint XX/ZZ erasure probability")
    axis.set_ylabel("Total variation from matched independent model")
    axis.set_title("Information lost by independent scalarization")
    axis.grid(alpha=0.25)
    figure.colorbar(scatter, ax=axis, label="Detector jitter (ps)")
    figure.tight_layout()
    figure.savefig(
        args.output / "scalarization_information_loss.png", dpi=180
    )
    plt.close(figure)

    print(
        f"compiled {len(channels)} channels; max TV={max_tv:.4f}; "
        f"max synthetic partial erasure={max_partial:.4f}"
    )


if __name__ == "__main__":
    main()
