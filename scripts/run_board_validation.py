#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def run_cmd(cmd: list[str], cwd: Path, log_path: Path, env: dict[str, str] | None = None) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            sys.stdout.write(line)
            log.write(line)
        return proc.wait()


def append_summary(summary_csv: Path, row: dict[str, object]) -> None:
    summary_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "run_id",
        "timestamp",
        "port",
        "baud",
        "program_returncode",
        "capture_returncode",
        "passed",
        "case_count",
        "failures",
        "cases",
        "total_mismatches",
        "first_mismatch",
        "failure_class",
        "failure_detail",
        "build_info",
        "uart_log",
        "program_log",
    ]
    write_header = not summary_csv.exists()
    with summary_csv.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in fieldnames})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build, program, and UART-capture the ZU4EV Viterbi board run.")
    parser.add_argument("--xsa", default=r"%VITERBI_STAGE%\viterbi_zu4ev_shell.xsa")
    parser.add_argument("--arch", default="hero_soft3")
    parser.add_argument("--port", default="COM9")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--stage-root", default=r"C:\viterbi_stage\zu4ev")
    parser.add_argument("--capture-timeout", type=float, default=180.0)
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--build-info", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(__file__).resolve().parents[1]
    run_id = "m7_board_" + time.strftime("%Y%m%d_%H%M%S")
    run_dir = repo / "data" / "board_runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    build_log = run_dir / "build.log"
    program_log = run_dir / "program_driver.log"
    uart_log = run_dir / "uart.log"
    uart_json = run_dir / "uart_capture.json"

    if args.skip_build:
        if not args.build_info:
            raise SystemExit("--skip-build requires --build-info")
        build_info_path = Path(args.build_info)
    else:
        build_cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(repo / "scripts" / "build_zu4ev_app.ps1"),
            "-XsaPath",
            args.xsa,
            "-Arch",
            args.arch,
            "-StageRoot",
            args.stage_root,
        ]
        build_rc = run_cmd(build_cmd, repo, build_log)
        if build_rc != 0:
            row = {
                "run_id": run_id,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "port": args.port,
                "baud": args.baud,
                "program_returncode": "",
                "capture_returncode": "",
                "passed": False,
                "failure_class": "build_failed",
                "failure_detail": f"build return code {build_rc}",
                "build_info": "",
                "uart_log": str(uart_log),
                "program_log": str(program_log),
            }
            append_summary(repo / "data" / "board_runs" / "board_summary.csv", row)
            return build_rc
        build_info_path = Path(args.stage_root) / args.arch / "artifacts" / "build_info.json"

    capture_cmd = [
        sys.executable,
        str(repo / "scripts" / "capture_uart.py"),
        "--port",
        args.port,
        "--baud",
        str(args.baud),
        "--capture-timeout",
        str(args.capture_timeout),
        "--log",
        str(uart_log),
        "--json",
        str(uart_json),
    ]
    capture = subprocess.Popen(
        capture_cmd,
        cwd=str(repo),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    time.sleep(2.0)

    program_cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(repo / "scripts" / "program_zu4ev.ps1"),
        "-BuildInfoPath",
        str(build_info_path),
        "-HwServerUrl",
        "tcp:127.0.0.1:3121",
    ]
    program_rc = run_cmd(program_cmd, repo, program_log)

    capture_lines: list[str] = []
    try:
        capture_stdout, _ = capture.communicate(timeout=args.capture_timeout + 20.0)
        if capture_stdout:
            capture_lines = capture_stdout.splitlines()
            for line in capture_lines:
                print(line)
        capture_rc = capture.returncode
    except subprocess.TimeoutExpired:
        capture.kill()
        capture_stdout, _ = capture.communicate()
        if capture_stdout:
            capture_lines = capture_stdout.splitlines()
            for line in capture_lines:
                print(line)
        capture_rc = 124

    if not uart_json.exists():
        uart_result = {
            "passed": False,
            "summary": None,
            "cases": [],
            "failure_class": "capture_missing_json",
            "failure_detail": "UART capture did not produce JSON",
        }
        uart_json.write_text(json.dumps(uart_result, indent=2), encoding="utf-8")
    else:
        uart_result = json.loads(uart_json.read_text(encoding="utf-8"))

    cases = uart_result.get("cases", [])
    summary = uart_result.get("summary") or {}
    total_mismatches = sum(int(case.get("mismatches", 0)) for case in cases)
    first_mismatch = ""
    for case in cases:
        if int(case.get("mismatches", 0)) != 0:
            first_mismatch = case.get("name", "")
            break

    passed = bool(uart_result.get("passed")) and program_rc == 0 and capture_rc == 0
    row = {
        "run_id": run_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "port": args.port,
        "baud": args.baud,
        "program_returncode": program_rc,
        "capture_returncode": capture_rc,
        "passed": passed,
        "case_count": summary.get("case_count", len(cases)),
        "failures": summary.get("failures", ""),
        "cases": ";".join(str(case.get("name", "")) for case in cases),
        "total_mismatches": total_mismatches,
        "first_mismatch": first_mismatch,
        "failure_class": uart_result.get("failure_class", ""),
        "failure_detail": uart_result.get("failure_detail", ""),
        "build_info": str(build_info_path),
        "uart_log": str(uart_log),
        "program_log": str(program_log),
    }
    append_summary(repo / "data" / "board_runs" / "board_summary.csv", row)
    (run_dir / "run_result.json").write_text(json.dumps(row, indent=2), encoding="utf-8")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
