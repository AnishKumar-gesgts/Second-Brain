from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from temporal_filter_qec.physics import PhysicalParameters, event_table
from temporal_filter_qec.qec import simulate_logical_error


def main() -> None:
    output = ROOT / "results" / "herald_robustness"
    output.mkdir(parents=True, exist_ok=True)
    params = PhysicalParameters(60.0, 15.0, 1.2, 0.995)
    misses = [0.0, 0.05, 0.1, 0.2, 0.25, 0.3, 0.35, 0.4, 0.5, 1.0]
    shots = 500_000
    rows = []
    for miss_index, miss in enumerate(misses):
        for rule_index, (rule, gate) in enumerate((("140_ps", 140.0), ("no_filter", None))):
            table = event_table(params, gate)
            for distance in (3, 5, 7):
                estimate = simulate_logical_error(
                    table,
                    distance,
                    distance,
                    shots,
                    20264001 + miss_index * 1000 + rule_index * 100 + distance,
                    missed_erasure_fraction=miss,
                )
                rows.append({"missed_fraction": miss, "rule": rule, **estimate.to_dict()})
    with (output / "herald_robustness.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    for rule in ("140_ps", "no_filter"):
        d5 = [r for r in rows if r["rule"] == rule and r["distance"] == 5]
        axes[0].plot(misses, [r["logical_error_rate"] for r in d5], "o-", label=rule.replace("_", " "))
        ratios = []
        for miss in misses:
            subset = {r["distance"]: r for r in rows if r["rule"] == rule and r["missed_fraction"] == miss}
            ratios.append(subset[7]["logical_error_rate"] / subset[3]["logical_error_rate"])
        axes[1].plot(misses, ratios, "o-", label=rule.replace("_", " "))
    axes[0].set_ylabel("Distance-5 logical error")
    axes[1].set_ylabel("Distance-7 / distance-3 rate")
    axes[1].axhline(1, color="black", linewidth=1)
    for ax in axes:
        ax.set_xlabel("Fraction of physical erasures whose flag is missed")
        ax.grid(alpha=0.25)
        ax.legend()
    fig.suptitle("Sensitivity to imperfect erasure heralding")
    fig.tight_layout()
    fig.savefig(output / "herald_robustness.png", dpi=180)
    plt.close(fig)

    summary = []
    for miss in misses:
        selected = {r["distance"]: r for r in rows if r["rule"] == "140_ps" and r["missed_fraction"] == miss}
        unfiltered = {r["distance"]: r for r in rows if r["rule"] == "no_filter" and r["missed_fraction"] == miss}
        summary.append({
            "missed_fraction": miss,
            "selected_d5": selected[5]["logical_error_rate"],
            "no_filter_d5": unfiltered[5]["logical_error_rate"],
            "relative_improvement": 1 - selected[5]["logical_error_rate"] / unfiltered[5]["logical_error_rate"],
            "selected_d7_over_d3": selected[7]["logical_error_rate"] / selected[3]["logical_error_rate"],
            "selected_beats_no_filter_significantly": selected[5]["ci_high"] < unfiltered[5]["ci_low"],
            "selected_harms_significantly": selected[5]["ci_low"] > unfiltered[5]["ci_high"],
            "selected_suppresses_significantly": selected[7]["ci_high"] < selected[3]["ci_low"],
        })
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
