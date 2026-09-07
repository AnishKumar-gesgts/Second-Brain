from pathlib import Path

from photonic_noise_compiler.stage3_study import run_stage3


ROOT = Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    summary = run_stage3(ROOT / "config" / "stage3.json", ROOT / "results" / "stage3")
    print(
        f"stage3 source grid: {summary['conditions']} conditions; "
        f"hidden-fault range "
        f"{summary['hidden_fault_probability_min']:.6g}-"
        f"{summary['hidden_fault_probability_max']:.6g}"
    )
