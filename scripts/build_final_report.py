#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "data" / "analysis"
IMPL_DIR = ROOT / "data" / "impl"
BOARD_DIR = ROOT / "data" / "board_runs"
PLOTS_DIR = ROOT / "docs" / "assets" / "plots"
REPORTS_DIR = ROOT / "reports"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def latest_pass_board_row(board_rows: list[dict[str, str]]) -> dict[str, str]:
    passed = [row for row in board_rows if row.get("passed") == "True"]
    if not passed:
        raise RuntimeError("No passing M7 board row found")
    return passed[-1]


def make_report_csvs() -> dict[str, Path]:
    sweep_rows = read_csv(ANALYSIS_DIR / "sweep_results.csv")

    ber_rows: list[dict[str, object]] = []
    for row in sweep_rows:
        payload = int(row["payload_length"])
        mismatches = int(row["mismatch_count"])
        ber_rows.append(
            {
                "case_id": row["case_id"],
                "decision_mode": row["decision_mode"],
                "channel": row["channel"],
                "traceback_depth": row["traceback_depth"],
                "path_metric_width": row["path_metric_width"],
                "normalization": row["normalization"],
                "payload_length": payload,
                "mismatch_count": mismatches,
                "observed_mismatch_rate": f"{mismatches / payload:.6f}",
                "source_run_id": row["run_id"],
            }
        )
    write_csv(
        ANALYSIS_DIR / "ber_summary.csv",
        [
            "case_id",
            "decision_mode",
            "channel",
            "traceback_depth",
            "path_metric_width",
            "normalization",
            "payload_length",
            "mismatch_count",
            "observed_mismatch_rate",
            "source_run_id",
        ],
        ber_rows,
    )

    depth_groups: dict[str, dict[str, object]] = defaultdict(lambda: {"payload": 0, "mismatches": 0, "rows": 0})
    for row in sweep_rows:
        if row["path_metric_width"] == "12" and row["normalization"] == "subtract_min":
            group = depth_groups[row["traceback_depth"]]
            group["payload"] = int(group["payload"]) + int(row["payload_length"])
            group["mismatches"] = int(group["mismatches"]) + int(row["mismatch_count"])
            group["rows"] = int(group["rows"]) + 1
    depth_rows = []
    for depth in sorted(depth_groups, key=lambda value: int(value)):
        group = depth_groups[depth]
        payload = int(group["payload"])
        mismatches = int(group["mismatches"])
        depth_rows.append(
            {
                "traceback_depth": depth,
                "path_metric_width": 12,
                "normalization": "subtract_min",
                "rows": group["rows"],
                "payload_bits_total": payload,
                "mismatch_count_total": mismatches,
                "observed_mismatch_rate": f"{mismatches / payload:.6f}" if payload else "0.000000",
                "source_csv": "data/analysis/sweep_results.csv",
            }
        )
    write_csv(
        ANALYSIS_DIR / "traceback_depth_sweep.csv",
        [
            "traceback_depth",
            "path_metric_width",
            "normalization",
            "rows",
            "payload_bits_total",
            "mismatch_count_total",
            "observed_mismatch_rate",
            "source_csv",
        ],
        depth_rows,
    )

    width_groups: dict[str, dict[str, object]] = defaultdict(lambda: {"payload": 0, "mismatches": 0, "rows": 0})
    for row in sweep_rows:
        if row["traceback_depth"] == "40" and row["normalization"] == "subtract_min":
            group = width_groups[row["path_metric_width"]]
            group["payload"] = int(group["payload"]) + int(row["payload_length"])
            group["mismatches"] = int(group["mismatches"]) + int(row["mismatch_count"])
            group["rows"] = int(group["rows"]) + 1
    width_rows = []
    for width in sorted(width_groups, key=lambda value: int(value)):
        group = width_groups[width]
        payload = int(group["payload"])
        mismatches = int(group["mismatches"])
        width_rows.append(
            {
                "path_metric_width": width,
                "traceback_depth": 40,
                "normalization": "subtract_min",
                "rows": group["rows"],
                "payload_bits_total": payload,
                "mismatch_count_total": mismatches,
                "observed_mismatch_rate": f"{mismatches / payload:.6f}" if payload else "0.000000",
                "source_csv": "data/analysis/sweep_results.csv",
            }
        )
    write_csv(
        ANALYSIS_DIR / "path_metric_width_sweep.csv",
        [
            "path_metric_width",
            "traceback_depth",
            "normalization",
            "rows",
            "payload_bits_total",
            "mismatch_count_total",
            "observed_mismatch_rate",
            "source_csv",
        ],
        width_rows,
    )

    return {
        "ber": ANALYSIS_DIR / "ber_summary.csv",
        "depth": ANALYSIS_DIR / "traceback_depth_sweep.csv",
        "width": ANALYSIS_DIR / "path_metric_width_sweep.csv",
    }


def estimate_fmax_mhz(wns_ns: float, target_period_ns: float = 10.0) -> float:
    required_period = target_period_ns - wns_ns
    if required_period <= 0:
        return float("inf")
    return 1000.0 / required_period


def make_plots() -> dict[str, Path]:
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    sweep_rows = read_csv(ANALYSIS_DIR / "sweep_results.csv")
    depth_rows = read_csv(ANALYSIS_DIR / "traceback_depth_sweep.csv")
    width_rows = read_csv(ANALYSIS_DIR / "path_metric_width_sweep.csv")
    impl_rows = read_csv(IMPL_DIR / "vivado_summary.csv")
    board_rows = read_csv(BOARD_DIR / "board_summary.csv")

    plot_paths: dict[str, Path] = {}

    k_values = list(range(3, 10))
    states = [2 ** (k - 1) for k in k_values]
    plt.figure(figsize=(6, 3.6))
    plt.plot(k_values, states, marker="o")
    plt.yscale("log", base=2)
    plt.xlabel("Constraint length K")
    plt.ylabel("State count")
    plt.title("State growth: 2^(K-1)")
    plt.grid(True, which="both", alpha=0.3)
    plot_paths["state_explosion"] = PLOTS_DIR / "fig04_state_explosion.png"
    plt.tight_layout()
    plt.savefig(plot_paths["state_explosion"], dpi=180)
    plt.close()

    rx_values = list(range(8))
    soft_metric_for_one = [abs(7 - value) for value in rx_values]
    hard_metric_for_one = [0 if value >= 4 else 1 for value in rx_values]
    plt.figure(figsize=(6, 3.6))
    plt.plot(rx_values, soft_metric_for_one, marker="o", label="soft3 distance to bit=1")
    plt.step(rx_values, hard_metric_for_one, where="mid", label="hard mismatch to bit=1")
    plt.xlabel("Received 3-bit symbol")
    plt.ylabel("Branch cost")
    plt.title("Hard vs soft metric shape")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plot_paths["hard_vs_soft"] = PLOTS_DIR / "fig05_hard_vs_soft_metric.png"
    plt.tight_layout()
    plt.savefig(plot_paths["hard_vs_soft"], dpi=180)
    plt.close()

    raw_a = [100, 116, 131, 148, 167, 184]
    raw_b = [104, 119, 136, 151, 169, 190]
    norm_a = [0]
    norm_b = [4]
    for a, b in zip(raw_a[1:], raw_b[1:]):
        m = min(a, b)
        norm_a.append(a - m)
        norm_b.append(b - m)
    plt.figure(figsize=(6, 3.6))
    plt.plot(raw_a, label="raw path A")
    plt.plot(raw_b, label="raw path B")
    plt.plot(norm_a, "--", label="normalized A")
    plt.plot(norm_b, "--", label="normalized B")
    plt.xlabel("Trellis step")
    plt.ylabel("Metric value")
    plt.title("Subtract-min keeps relative distance")
    plt.legend(fontsize=8)
    plt.grid(True, alpha=0.3)
    plot_paths["normalization"] = PLOTS_DIR / "fig09_normalization_effect.png"
    plt.tight_layout()
    plt.savefig(plot_paths["normalization"], dpi=180)
    plt.close()

    depths = [int(row["traceback_depth"]) for row in depth_rows]
    depth_rates = [float(row["observed_mismatch_rate"]) for row in depth_rows]
    plt.figure(figsize=(6, 3.6))
    plt.plot(depths, depth_rates, marker="o")
    plt.xlabel("Traceback depth")
    plt.ylabel("Observed mismatch rate")
    plt.title("Traceback depth tradeoff")
    plt.grid(True, alpha=0.3)
    plot_paths["depth_tradeoff"] = PLOTS_DIR / "fig14_depth_tradeoff.png"
    plt.tight_layout()
    plt.savefig(plot_paths["depth_tradeoff"], dpi=180)
    plt.close()

    widths = [int(row["path_metric_width"]) for row in width_rows]
    width_rates = [float(row["observed_mismatch_rate"]) for row in width_rows]
    plt.figure(figsize=(6, 3.6))
    plt.bar([str(width) for width in widths], width_rates)
    plt.xlabel("Path metric width")
    plt.ylabel("Observed mismatch rate")
    plt.title("Path metric width at traceback depth 40")
    plt.grid(True, axis="y", alpha=0.3)
    plot_paths["width_tradeoff"] = PLOTS_DIR / "fig15_width_resource_tradeoff.png"
    plt.tight_layout()
    plt.savefig(plot_paths["width_tradeoff"], dpi=180)
    plt.close()

    labels = []
    luts = []
    fmax_values = []
    for row in impl_rows:
        labels.append(row["run_id"].replace("m6_", "").replace("_viterbi_decoder_core", ""))
        luts.append(int(row["lut"]))
        fmax_values.append(estimate_fmax_mhz(float(row["wns_ns"])))
    plt.figure(figsize=(6.8, 3.8))
    plt.scatter(luts, fmax_values)
    for label, lut, fmax in zip(labels, luts, fmax_values):
        plt.annotate(label, (lut, fmax), fontsize=7)
    plt.xlabel("LUT")
    plt.ylabel("Estimated Fmax from 10 ns timing report (MHz)")
    plt.title("Resource and timing estimate")
    plt.grid(True, alpha=0.3)
    plot_paths["fmax_resource"] = PLOTS_DIR / "fig16_fmax_resource_plot.png"
    plt.tight_layout()
    plt.savefig(plot_paths["fmax_resource"], dpi=180)
    plt.close()

    run_labels = [row["run_id"].replace("m7_board_", "") for row in board_rows]
    pass_values = [1 if row["passed"] == "True" else 0 for row in board_rows]
    plt.figure(figsize=(7.2, 3.6))
    colors_for_runs = ["#2E7D32" if value else "#B71C1C" for value in pass_values]
    plt.bar(run_labels, pass_values, color=colors_for_runs)
    plt.ylim(0, 1.2)
    plt.ylabel("PASS=1")
    plt.title("Board validation attempts")
    plt.xticks(rotation=25, ha="right")
    plt.grid(True, axis="y", alpha=0.3)
    plot_paths["board_summary"] = PLOTS_DIR / "fig17_board_run_summary.png"
    plt.tight_layout()
    plt.savefig(plot_paths["board_summary"], dpi=180)
    plt.close()

    return plot_paths

def main() -> int:
    make_report_csvs()
    make_plots()
    print("Updated derived analysis CSVs and report plot assets.")
    print("Report.md and Report.pdf are intentionally not generated by this script.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
