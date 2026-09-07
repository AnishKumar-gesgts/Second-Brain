from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from temporal_filter_qec.study import run_study


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the frozen temporal-filter QEC study")
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "baseline.json")
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    summary = run_study(args.config.resolve(), args.output.resolve())
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
