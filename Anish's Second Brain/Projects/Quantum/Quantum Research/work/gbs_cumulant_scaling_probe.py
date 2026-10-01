"""Exact storage arithmetic for precomputing every cumulant through order K.

This is a lower bound for the explicit table used in Dodd et al.; it is not a
lower bound for every conceivable GBS algorithm or compressed representation.
"""
import json
from math import comb
from pathlib import Path


def main():
    rows = []
    for name, modes in [("Jiuzhang 2/3 example", 144), ("Jiuzhang 4 S64", 4336),
                        ("Jiuzhang 4 M256", 5104), ("Jiuzhang 4 L1024", 8176)]:
        for order in (2, 3, 4, 5):
            terms = sum(comb(modes, j) for j in range(1, order + 1))
            rows.append({"instance": name, "modes": modes, "max_cumulant_order": order,
                         "stored_terms": terms, "minimum_float32_bytes": 4 * terms,
                         "minimum_float32_terabytes": 4 * terms / 1e12,
                         "minimum_float32_exabytes": 4 * terms / 1e18})
    result = {"scope": "explicit dense table of all click cumulants, one 32-bit float per term",
              "limitation": "other structures, sparse terms, on-demand computation, or a different algorithm could use less memory",
              "rows": rows}
    path = Path(__file__).resolve().parents[1] / "outputs" / "gbs_cumulant_scaling_probe.json"
    path.write_text(json.dumps(result, indent=2))
    for row in rows:
        if row["max_cumulant_order"] in (3, 4, 5):
            print(f"{row['instance']}: K={row['max_cumulant_order']}, "
                  f"{row['stored_terms']:,} terms, min {row['minimum_float32_terabytes']:,.3f} TB")
    print(path)


if __name__ == "__main__":
    main()
