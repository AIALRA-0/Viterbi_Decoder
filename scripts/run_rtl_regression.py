#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RTL_FILES = [
    "rtl/common/viterbi_pkg.sv",
    "rtl/viterbi_core/bmu_hard.sv",
    "rtl/viterbi_core/acs_unit.sv",
    "rtl/viterbi_core/acs_array.sv",
    "rtl/viterbi_core/path_metric_bank.sv",
    "rtl/viterbi_core/survivor_ram.sv",
    "rtl/viterbi_core/traceback_engine.sv",
    "rtl/viterbi_core/viterbi_decoder_core.sv",
    "tb/tb_viterbi_core.sv",
]
DEFAULT_CASES = ["no_noise", "all_zero", "impulse_one", "single_bit_error"]


def parse_env(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def run_cmd(command: str, log_path: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["cmd", "/c", command],
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(result.stdout, encoding="utf-8", errors="replace")
    return result


def vivado_prefix(settings: str) -> str:
    return f"call {settings} && cd /d {PROJECT_ROOT} && "


def compile_design(settings: str, log_dir: Path) -> None:
    files = " ".join(RTL_FILES)
    command = vivado_prefix(settings) + f"xvlog -sv {files}"
    result = run_cmd(command, log_dir / "xvlog.log")
    if result.returncode != 0:
        raise RuntimeError("xvlog failed; see data/regression/xsim_logs/xvlog.log")

    command = vivado_prefix(settings) + "xelab tb_viterbi_core -s tb_viterbi_core_sim"
    result = run_cmd(command, log_dir / "xelab.log")
    if result.returncode != 0:
        raise RuntimeError("xelab failed; see data/regression/xsim_logs/xelab.log")


def run_case(settings: str, case: str, log_dir: Path) -> dict[str, str | int]:
    (PROJECT_ROOT / "tb/current_case.txt").write_text(case + "\n", encoding="ascii")
    command = vivado_prefix(settings) + "xsim tb_viterbi_core_sim -R"
    result = run_cmd(command, log_dir / f"xsim_{case}.log")
    text = result.stdout
    passed = result.returncode == 0 and "CASE_PASS" in text
    first_mismatch = ""
    mismatch_count = ""
    for line in text.splitlines():
        if "CASE_FAIL" in line:
            for token in line.split():
                if token.startswith("first_mismatch="):
                    first_mismatch = token.split("=", 1)[1]
                if token.startswith("mismatch="):
                    mismatch_count = token.split("=", 1)[1]
    if passed:
        mismatch_count = "0"
    return {
        "case_id": case,
        "result": "PASS" if passed else "FAIL",
        "mismatch_count": mismatch_count,
        "first_mismatch": first_mismatch,
        "log": str(log_dir / f"xsim_{case}.log"),
    }


def write_summary(path: Path, rows: list[dict[str, str | int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", default="config/local.env")
    parser.add_argument("--cases", nargs="*", default=DEFAULT_CASES)
    args = parser.parse_args()

    env = parse_env(PROJECT_ROOT / args.env)
    settings = env["VIVADO_SETTINGS"]
    subprocess.check_call(
        [sys.executable, "scripts/gen_rtl_pkg.py", "--spec", "spec/viterbi_spec.json", "--out", "rtl/common/viterbi_pkg.sv"],
        cwd=PROJECT_ROOT,
    )

    log_dir = PROJECT_ROOT / "data/regression/xsim_logs"
    compile_design(settings, log_dir)
    rows = [run_case(settings, case, log_dir) for case in args.cases]
    write_summary(PROJECT_ROOT / "data/regression/rtl_regression_summary.csv", rows)
    failed = [row for row in rows if row["result"] != "PASS"]
    for row in rows:
        print(
            f"[CASE] {row['case_id']} result={row['result']} "
            f"mismatch={row['mismatch_count']} first={row['first_mismatch']}"
        )
    print(f"[SUMMARY] cases={len(rows)} failed={len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
