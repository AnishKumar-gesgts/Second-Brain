from pathlib import Path

from photonic_noise_compiler.stage3_fusion_study import run_stage3_fusion


ROOT = Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    summary = run_stage3_fusion(
        ROOT / "config" / "stage3_fusion.json", ROOT / "results" / "stage3"
    )
    print(
        f"stage3 fusion grid: {summary['conditions']} conditions; "
        "hidden error among full records "
        f"{summary['hidden_error_given_full_success_min']:.6g}-"
        f"{summary['hidden_error_given_full_success_max']:.6g}"
    )
