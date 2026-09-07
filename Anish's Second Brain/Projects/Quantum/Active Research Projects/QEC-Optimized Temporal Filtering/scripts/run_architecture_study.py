from __future__ import annotations

import argparse
from pathlib import Path

from temporal_filter_qec.architecture_study import run_architecture_study


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config/architecture.json"))
    parser.add_argument("--output", type=Path, default=Path("results/fusion_bulk"))
    args = parser.parse_args()
    summary = run_architecture_study(args.config, args.output)
    print(
        "fusion-bulk study complete:",
        summary["selection_guard_passes"],
        "guard passes;",
        summary["heldout_significant_improvements"],
        "held-out improvements;",
        summary["heldout_significant_harms"],
        "held-out harms",
    )


if __name__ == "__main__":
    main()
