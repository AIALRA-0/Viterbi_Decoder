#!/usr/bin/env python3
import argparse
import json
import re
import sys
import time
from pathlib import Path

import serial


CASE_RE = re.compile(
    r"^\[(?P<name>[^\]]+)\] len=(?P<length>\d+) cycles=(?P<cycles>\d+) mismatches=(?P<mismatches>\d+) status=0x(?P<status>[0-9a-fA-F]+)$"
)
SUMMARY_RE = re.compile(r"^Completed (?P<count>\d+) cases, failures=(?P<failures>-?\d+)$")
ARCH_RE = re.compile(r"^Console=(?P<console>[^,]+), arch_id=(?P<arch_id>\d+)$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture and judge ZU4EV UART logs.")
    parser.add_argument("--port", required=True)
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--open-timeout", type=float, default=20.0)
    parser.add_argument("--capture-timeout", type=float, default=180.0)
    parser.add_argument("--log", required=True)
    parser.add_argument("--json", required=True)
    return parser.parse_args()


def open_serial(port: str, baud: int, open_timeout: float) -> serial.Serial:
    deadline = time.time() + open_timeout
    last_error = None
    while time.time() < deadline:
        try:
            return serial.Serial(port=port, baudrate=baud, timeout=0.25)
        except Exception as exc:  # pragma: no cover - hardware dependent
            last_error = str(exc)
            time.sleep(0.5)
    raise RuntimeError(last_error or f"Unable to open {port}")


def main() -> int:
    args = parse_args()
    log_path = Path(args.log)
    json_path = Path(args.json)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    result = {
        "port": args.port,
        "baud": args.baud,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "arch_id": None,
        "console": None,
        "cases": [],
        "summary": None,
        "passed": False,
        "failure_class": None,
        "failure_detail": None,
    }
    lines = []

    try:
        ser = open_serial(args.port, args.baud, args.open_timeout)
    except Exception as exc:  # pragma: no cover - hardware dependent
        result["failure_class"] = "serial_open_failed"
        result["failure_detail"] = str(exc)
        log_path.write_text("", encoding="utf-8")
        json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return 1

    deadline = time.time() + args.capture_timeout
    try:
        while time.time() < deadline:
            raw = ser.readline()
            if not raw:
                continue
            line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
            if not line:
                continue
            print(line)
            sys.stdout.flush()
            lines.append(line)

            arch_match = ARCH_RE.match(line)
            if arch_match:
                result["console"] = arch_match.group("console")
                result["arch_id"] = int(arch_match.group("arch_id"))
                continue

            case_match = CASE_RE.match(line)
            if case_match:
                result["cases"].append(
                    {
                        "name": case_match.group("name"),
                        "length": int(case_match.group("length")),
                        "cycles": int(case_match.group("cycles")),
                        "mismatches": int(case_match.group("mismatches")),
                        "status_hex": case_match.group("status"),
                    }
                )
                continue

            summary_match = SUMMARY_RE.match(line)
            if summary_match:
                result["summary"] = {
                    "case_count": int(summary_match.group("count")),
                    "failures": int(summary_match.group("failures")),
                }
                break
    finally:
        ser.close()

    if result["summary"] is None:
        result["failure_class"] = "serial_timeout"
        result["failure_detail"] = "Did not observe completion sentinel on UART"
    else:
        any_mismatch = any(case["mismatches"] != 0 for case in result["cases"])
        any_error_status = any(int(case["status_hex"], 16) & 0x4 for case in result["cases"])
        passed = (
            result["summary"]["failures"] == 0
            and not any_mismatch
            and not any_error_status
        )
        result["passed"] = passed
        if not passed:
            result["failure_class"] = "functional_failure"
            result["failure_detail"] = "Non-zero failures, mismatches, or error status observed"

    result["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    log_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
