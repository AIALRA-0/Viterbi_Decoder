#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RTL_FILES = [
    "rtl/common/viterbi_pkg.sv",
    "rtl/viterbi_core/bmu_soft3.sv",
    "rtl/viterbi_core/path_metric_normalizer.sv",
    "rtl/viterbi_core/viterbi_decoder_core_soft3.sv",
    "tb/tb_viterbi_soft3.sv",
]
DEFAULT_CASES = ["soft_awgn_0db", "soft_awgn_1db", "soft_awgn_2db"]


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


def compile_design(settings: str, log_dir: Path) -> None:
    files = " ".join(RTL_FILES)
    result = run_cmd(vivado_prefix(settings) + f"xvlog -sv {files}", log_dir / "soft3_xvlog.log")
    if result.returncode != 0:
        raise RuntimeError("soft3 xvlog failed")
    result = run_cmd(vivado_prefix(settings) + "xelab tb_viterbi_soft3 -s tb_viterbi_soft3_sim", log_dir / "soft3_xelab.log")
    if result.returncode != 0:
        raise RuntimeError("soft3 xelab failed")


def run_case(settings: str, case: str, log_dir: Path) -> dict[str, str]:
    (PROJECT_ROOT / "tb/current_case.txt").write_text(case + "\n", encoding="ascii")
    result = run_cmd(vivado_prefix(settings) + "xsim tb_viterbi_soft3_sim -R", log_dir / f"xsim_soft3_{case}.log")
    text = result.stdout
    passed = result.returncode == 0 and "CASE_PASS" in text
    mismatch_count = "0" if passed else ""
    first_mismatch = ""
    for line in text.splitlines():
        if "CASE_FAIL" in line:
            for token in line.split():
                if token.startswith("mismatch="):
                    mismatch_count = token.split("=", 1)[1]
                if token.startswith("first_mismatch="):
                    first_mismatch = token.split("=", 1)[1]
    return {
        "case_id": case,
        "result": "PASS" if passed else "FAIL",
        "mismatch_count": mismatch_count,
        "first_mismatch": first_mismatch,
        "log": str(log_dir / f"xsim_soft3_{case}.log"),
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
    parser.add_argument("--cases", nargs="*", default=DEFAULT_CASES)
    args = parser.parse_args()

    env = parse_env(PROJECT_ROOT / args.env)
    subprocess.check_call(
        [sys.executable, "scripts/gen_rtl_pkg.py", "--spec", "spec/viterbi_spec.json", "--out", "rtl/common/viterbi_pkg.sv"],
        cwd=PROJECT_ROOT,
    )
    log_dir = PROJECT_ROOT / "data/regression/xsim_logs"
    compile_design(env["VIVADO_SETTINGS"], log_dir)
    rows = [run_case(env["VIVADO_SETTINGS"], case, log_dir) for case in args.cases]
    write_summary(PROJECT_ROOT / "data/regression/soft3_regression_summary.csv", rows)
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
