#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import re
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_env(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def vivado_prefix(settings: str) -> str:
    return f"call {settings} && cd /d {PROJECT_ROOT} && "


def run_vivado(settings: str, script: str, top: str, out_dir: Path, part: str, log_path: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    command = (
        vivado_prefix(settings)
        + f"vivado -mode batch -source {script} -tclargs {top} {out_dir.as_posix()} {part}"
    )
    result = subprocess.run(
        ["cmd", "/c", command],
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    log_path.write_text(result.stdout, encoding="utf-8", errors="replace")
    return result.returncode


def table_value(report: str, names: list[str]) -> str:
    for line in report.splitlines():
        if not line.strip().startswith("|"):
            continue
        columns = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(columns) < 2:
            continue
        label = columns[0]
        if any(name.lower() in label.lower() for name in names):
            for item in columns[1:]:
                item = item.replace(",", "").strip()
                if re.fullmatch(r"-?\d+(\.\d+)?", item):
                    return item
    return ""


def parse_timing(report: str) -> tuple[str, str]:
    lines = report.splitlines()
    for idx, line in enumerate(lines):
        if "WNS(ns)" not in line or "TNS(ns)" not in line:
            continue
        for candidate in lines[idx + 1 : idx + 5]:
            numeric = re.findall(r"-?\d+\.\d+", candidate)
            if len(numeric) >= 2:
                return numeric[0], numeric[1]
    return "", ""


def parse_power(report: str) -> str:
    for line in report.splitlines():
        if "Total On-Chip Power" in line:
            numbers = re.findall(r"\d+\.\d+", line)
            if numbers:
                return numbers[0]
    return ""


def parse_reports(kind: str, top: str, out_dir: Path, returncode: int) -> dict[str, str]:
    util = (out_dir / "utilization.rpt").read_text(encoding="utf-8", errors="ignore") if (out_dir / "utilization.rpt").exists() else ""
    timing = (out_dir / "timing_summary.rpt").read_text(encoding="utf-8", errors="ignore") if (out_dir / "timing_summary.rpt").exists() else ""
    power = (out_dir / "power.rpt").read_text(encoding="utf-8", errors="ignore") if (out_dir / "power.rpt").exists() else ""
    wns, tns = parse_timing(timing)
    return {
        "run_id": f"m6_{kind}_{top}",
        "kind": kind,
        "top": top,
        "returncode": str(returncode),
        "status": "PASS" if returncode == 0 else "FAIL",
        "lut": table_value(util, ["CLB LUTs", "Slice LUTs"]),
        "ff": table_value(util, ["CLB Registers", "Slice Registers"]),
        "bram": table_value(util, ["Block RAM Tile", "Block RAM"]),
        "dsp": table_value(util, ["DSPs", "DSP"]),
        "wns_ns": wns,
        "tns_ns": tns,
        "total_power_w": parse_power(power),
        "report_dir": str(out_dir),
    }


def write_summary(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", default="config/local.env")
    args = parser.parse_args()
    env = parse_env(PROJECT_ROOT / args.env)
    settings = env["VIVADO_SETTINGS"]
    part = env["FPGA_PART"]

    runs = [
        ("synth", "viterbi_decoder_core", "vivado/tcl/run_synth.tcl", PROJECT_ROOT / "data/impl/baseline_synth"),
        ("synth", "viterbi_decoder_core_soft3", "vivado/tcl/run_synth.tcl", PROJECT_ROOT / "data/impl/hero_synth"),
        ("impl", "viterbi_decoder_core_soft3", "vivado/tcl/run_impl.tcl", PROJECT_ROOT / "data/impl/hero_impl"),
    ]
    rows: list[dict[str, str]] = []
    for kind, top, script, out_dir in runs:
        log_path = PROJECT_ROOT / "data/impl/logs" / f"{kind}_{top}.log"
        rc = run_vivado(settings, script, top, out_dir, part, log_path)
        row = parse_reports(kind, top, out_dir, rc)
        rows.append(row)
        print(
            f"[RUN] {kind} top={top} status={row['status']} "
            f"lut={row['lut']} ff={row['ff']} bram={row['bram']} dsp={row['dsp']} "
            f"wns={row['wns_ns']} power={row['total_power_w']}"
        )
        if rc != 0:
            write_summary(PROJECT_ROOT / "data/impl/vivado_summary.csv", rows)
            return 1
    write_summary(PROJECT_ROOT / "data/impl/vivado_summary.csv", rows)
    failed = [row for row in rows if row["status"] != "PASS"]
    print(f"[SUMMARY] runs={len(rows)} failed={len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
