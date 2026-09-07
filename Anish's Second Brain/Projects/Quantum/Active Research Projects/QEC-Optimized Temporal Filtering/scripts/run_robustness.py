from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from temporal_filter_qec.robustness import run_robustness


def main() -> None:
    parser = argparse.ArgumentParser(description="Run detuning/jitter robustness maps")
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "robustness.json")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "robustness")
    args = parser.parse_args()
    print(json.dumps(run_robustness(args.config.resolve(), args.output.resolve()), indent=2))


if __name__ == "__main__":
    main()
