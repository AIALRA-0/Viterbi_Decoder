#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib.pyplot as plt

from model.trellis import load_code_spec, load_project_spec
from model.viterbi_golden import decode_hard, decode_soft3


def read_hex_values(path: Path) -> list[int]:
    return [int(line.strip(), 16) for line in path.read_text(encoding="ascii").splitlines() if line.strip()]


def first_mismatch(expected: list[int], actual: list[int]) -> int | None:
    for idx, (left, right) in enumerate(zip(expected, actual)):
        if left != right:
            return idx
    if len(expected) != len(actual):
        return min(len(expected), len(actual))
    return None


def mismatch_count(expected: list[int], actual: list[int]) -> int:
    return abs(len(expected) - len(actual)) + sum(1 for left, right in zip(expected, actual) if left != right)


def run_case(
    case_dir: Path,
    code_spec,
    traceback_depth: int,
    path_metric_width: int,
    normalization: str,
) -> dict[str, object]:
    metadata = json.loads((case_dir / "metadata.json").read_text(encoding="utf-8"))
    expected = read_hex_values(case_dir / "input_bits.hex")
    if metadata["decision_mode"] == "soft3":
      received = read_hex_values(case_dir / "rx_soft3.hex")
      decoded = decode_soft3(
          received,
          code_spec,
          decoded_length=len(expected),
          path_metric_width=path_metric_width,
          normalization=normalization,
          traceback_depth=traceback_depth,
      ).decoded_bits
    else:
      received = read_hex_values(case_dir / "rx_hard.hex")
      decoded = decode_hard(
          received,
          code_spec,
          decoded_length=len(expected),
          path_metric_width=path_metric_width,
          normalization=normalization,
          traceback_depth=traceback_depth,
      ).decoded_bits
    first = first_mismatch(expected, decoded)
    mismatch = mismatch_count(expected, decoded)
    return {
        "case_id": metadata["case_id"],
        "run_id": f"m5_{metadata['case_id']}_tb{traceback_depth}_pm{path_metric_width}_{normalization}",
        "decision_mode": metadata["decision_mode"],
        "channel": metadata["channel"],
        "traceback_depth": traceback_depth,
        "path_metric_width": path_metric_width,
        "normalization": normalization,
        "payload_length": len(expected),
        "mismatch_count": mismatch,
        "first_mismatch": "" if first is None else first,
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def plot_traceback(rows: list[dict[str, object]], out: Path, source: str) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    soft_rows = [row for row in rows if row["decision_mode"] == "soft3"]
    depths = sorted({int(row["traceback_depth"]) for row in soft_rows})
    widths = sorted({int(row["path_metric_width"]) for row in soft_rows})
    plt.figure(figsize=(9, 5))
    for normalization in ["none", "subtract_min"]:
        y_values = []
        for depth in depths:
            total = sum(
                int(row["mismatch_count"])
                for row in soft_rows
                if int(row["traceback_depth"]) == depth and row["normalization"] == normalization
            )
            y_values.append(total)
        plt.plot(depths, y_values, marker="o", label=normalization)
    plt.title(f"M5 soft3 mismatch vs traceback depth\nsource={source}")
    plt.xlabel("traceback depth")
    plt.ylabel("total mismatch across soft_awgn cases")
    plt.grid(True, alpha=0.3)
    plt.legend(title="normalization")
    plt.tight_layout()
    plt.savefig(out, dpi=160)
    plt.close()

    plt.figure(figsize=(8, 5))
    matrix = []
    for width in widths:
        matrix.append([
            sum(
                int(row["mismatch_count"])
                for row in soft_rows
                if int(row["path_metric_width"]) == width
                and int(row["traceback_depth"]) == depth
                and row["normalization"] == "subtract_min"
            )
            for depth in depths
        ])
    plt.imshow(matrix, aspect="auto", cmap="viridis")
    plt.colorbar(label="total mismatch")
    plt.xticks(range(len(depths)), depths)
    plt.yticks(range(len(widths)), widths)
    plt.xlabel("traceback depth")
    plt.ylabel("path metric width")
    plt.title(f"M5 subtract_min soft3 mismatch heatmap\nsource={source}")
    plt.tight_layout()
    plt.savefig(out.parent / "m5_soft3_subtract_min_heatmap.png", dpi=160)
    plt.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", default="spec/viterbi_spec.json")
    parser.add_argument("--vectors", default="vectors")
    parser.add_argument("--out", default="data/analysis/sweep_results.csv")
    args = parser.parse_args()

    start = time.time()
    spec = load_project_spec(args.spec)
    code_spec = load_code_spec(args.spec, "code")
    decoder = spec["decoder"]
    case_dirs = sorted(path for path in Path(args.vectors).iterdir() if (path / "metadata.json").exists())
    rows: list[dict[str, object]] = []
    for case_dir in case_dirs:
        for traceback_depth in decoder["traceback_depths"]:
            for path_metric_width in decoder["path_metric_widths"]:
                for normalization in decoder["normalization_modes"]:
                    rows.append(
                        run_case(
                            case_dir,
                            code_spec,
                            int(traceback_depth),
                            int(path_metric_width),
                            str(normalization),
                        )
                    )
    out_path = Path(args.out)
    write_csv(out_path, rows)
    plot_traceback(rows, Path("docs/assets/plots/m5_soft3_mismatch_vs_traceback.png"), str(out_path))
    elapsed = time.time() - start
    total_mismatch = sum(int(row["mismatch_count"]) for row in rows)
    print(f"[SUMMARY] rows={len(rows)} total_mismatch={total_mismatch} elapsed_sec={elapsed:.3f}")
    print(f"[DATA] {out_path}")
    print("[PLOT] docs/assets/plots/m5_soft3_mismatch_vs_traceback.png")
    print("[PLOT] docs/assets/plots/m5_soft3_subtract_min_heatmap.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
