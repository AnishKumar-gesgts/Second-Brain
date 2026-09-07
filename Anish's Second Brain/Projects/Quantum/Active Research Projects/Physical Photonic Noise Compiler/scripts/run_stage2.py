from __future__ import annotations

import argparse
from pathlib import Path

from photonic_noise_compiler.stage2_study import run_stage2


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config/stage2.json"))
    parser.add_argument("--output", type=Path, default=Path("results/stage2"))
    args = parser.parse_args()
    summary = run_stage2(args.config, args.output)
    print(
        f"held-out: {summary['heldout_significant_full_lower']} full-lower, "
        f"{summary['heldout_significant_full_higher']} full-higher, "
        f"{summary['heldout_non_saturated_significant_differences']} "
        "non-saturated significant"
    )


if __name__ == "__main__":
    main()
