from __future__ import annotations

import argparse
from pathlib import Path

from temporal_filter_qec.protocol_study import run_protocol_study


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config/protocol_exact.json"))
    parser.add_argument("--output", type=Path, default=Path("results/protocol_exact"))
    args = parser.parse_args()
    summary = run_protocol_study(args.config, args.output)
    print(
        f"{summary['heldout_significant_improvements']}/{len(summary['conditions'])} "
        "held-out conditions improved significantly"
    )


if __name__ == "__main__":
    main()
