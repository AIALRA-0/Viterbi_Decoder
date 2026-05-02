#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import random
import subprocess
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from model.channel import awgn_soft3, burst_error, flip_positions, hard_to_soft3, no_noise
from model.conv_encoder import encode_bits
from model.trellis import load_code_spec, load_project_spec
from model.viterbi_golden import decode_hard, decode_soft3


REQUIRED_VECTOR_FILES = [
    "metadata.json",
    "input_bits.hex",
    "encoded_bits.hex",
    "rx_hard.hex",
    "rx_soft3.hex",
    "golden_decoded.hex",
]


def git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return None


def random_payload(length: int, seed: int) -> list[int]:
    rng = random.Random(seed)
    return [rng.randrange(2) for _ in range(length)]


def make_payload(case: dict[str, Any]) -> list[int]:
    length = int(case["payload_length"])
    kind = case["payload"]
    if kind == "random":
        return random_payload(length, int(case["seed"]))
    if kind == "all_zero":
        return [0] * length
    if kind == "impulse_one":
        return [1] + [0] * (length - 1)
    raise ValueError(f"Unsupported payload kind: {kind}")


def hard_from_soft3(values: list[int]) -> list[int]:
    return [1 if value >= 4 else 0 for value in values]


def apply_channel(encoded: list[int], case: dict[str, Any]) -> tuple[list[int], list[int]]:
    channel = case["channel"]
    if channel == "no_noise":
        rx_hard = no_noise(encoded)
        return rx_hard, hard_to_soft3(rx_hard)
    if channel == "flip_positions":
        rx_hard = flip_positions(encoded, case["flip_positions"])
        return rx_hard, hard_to_soft3(rx_hard)
    if channel == "burst_error":
        rx_hard = burst_error(encoded, int(case["burst_start"]), int(case["burst_length"]))
        return rx_hard, hard_to_soft3(rx_hard)
    if channel == "random_hard":
        rng = random.Random(int(case["seed"]) + 100000)
        probability = float(case["bit_flip_probability"])
        positions = [idx for idx in range(len(encoded)) if rng.random() < probability]
        rx_hard = flip_positions(encoded, positions)
        return rx_hard, hard_to_soft3(rx_hard)
    if channel == "soft_awgn":
        rx_soft3 = awgn_soft3(encoded, float(case["snr_db"]), int(case["seed"]) + 200000)
        return hard_from_soft3(rx_soft3), rx_soft3
    raise ValueError(f"Unsupported channel: {channel}")


def first_mismatch(expected: list[int], actual: list[int]) -> int | None:
    for idx, (left, right) in enumerate(zip(expected, actual)):
        if left != right:
            return idx
    if len(expected) != len(actual):
        return min(len(expected), len(actual))
    return None


def mismatch_count(expected: list[int], actual: list[int]) -> int:
    total = abs(len(expected) - len(actual))
    total += sum(1 for left, right in zip(expected, actual) if left != right)
    return total


def write_values(path: Path, values: list[int]) -> None:
    path.write_text("".join(f"{value:x}\n" for value in values), encoding="ascii")


def generate_case(
    case: dict[str, Any],
    spec_path: Path,
    out_root: Path,
    hex_format: str,
) -> dict[str, Any]:
    code_spec = load_code_spec(spec_path, "code")
    payload = make_payload(case)
    encoded = encode_bits(payload, code_spec)
    rx_hard, rx_soft3 = apply_channel(encoded, case)
    if case["decision_mode"] == "hard":
        decoded = decode_hard(rx_hard, code_spec, decoded_length=len(payload)).decoded_bits
    elif case["decision_mode"] == "soft3":
        decoded = decode_soft3(rx_soft3, code_spec, decoded_length=len(payload)).decoded_bits
    else:
        raise ValueError(f"Unsupported decision_mode: {case['decision_mode']}")

    mismatch = mismatch_count(payload, decoded)
    first = first_mismatch(payload, decoded)
    case_dir = out_root / case["id"]
    case_dir.mkdir(parents=True, exist_ok=True)
    write_values(case_dir / "input_bits.hex", payload)
    write_values(case_dir / "encoded_bits.hex", encoded)
    write_values(case_dir / "rx_hard.hex", rx_hard)
    write_values(case_dir / "rx_soft3.hex", rx_soft3)
    write_values(case_dir / "golden_decoded.hex", decoded)

    metadata = {
        "case_id": case["id"],
        "run_id": f"m2_{case['id']}_{case['seed']}",
        "source_spec": str(spec_path),
        "generator_commit": git_commit(),
        "hex_format": hex_format,
        "payload_kind": case["payload"],
        "payload_length": len(payload),
        "encoded_bit_count": len(encoded),
        "rx_hard_count": len(rx_hard),
        "rx_soft3_count": len(rx_soft3),
        "golden_decoded_count": len(decoded),
        "seed": int(case["seed"]),
        "channel": case["channel"],
        "decision_mode": case["decision_mode"],
        "mismatch_count": mismatch,
        "first_mismatch": first,
        "case_config": case,
        "files": {name: name for name in REQUIRED_VECTOR_FILES if name != "metadata.json"},
    }
    (case_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return {
        "case_id": case["id"],
        "run_id": metadata["run_id"],
        "channel": case["channel"],
        "decision_mode": case["decision_mode"],
        "payload_length": len(payload),
        "encoded_bit_count": len(encoded),
        "mismatch_count": mismatch,
        "first_mismatch": "" if first is None else first,
        "metadata": str(case_dir / "metadata.json"),
    }


def verify_vectors(out_root: Path, rows: list[dict[str, Any]]) -> None:
    for row in rows:
        case_dir = out_root / row["case_id"]
        missing = [name for name in REQUIRED_VECTOR_FILES if not (case_dir / name).exists()]
        if missing:
            raise FileNotFoundError(f"{row['case_id']} missing files: {missing}")
        metadata = json.loads((case_dir / "metadata.json").read_text(encoding="utf-8"))
        for name in REQUIRED_VECTOR_FILES[1:]:
            values = (case_dir / name).read_text(encoding="ascii").splitlines()
            if not values:
                raise ValueError(f"{case_dir / name} is empty")
        if int(metadata["golden_decoded_count"]) != int(metadata["payload_length"]):
            raise ValueError(f"{row['case_id']} golden length mismatch")


def write_summary(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", default="spec/viterbi_spec.json")
    parser.add_argument("--out", default="vectors")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    out_root = Path(args.out)
    project_spec = load_project_spec(spec_path)
    vector_spec = project_spec["vector_generation"]
    rows = [
        generate_case(case, spec_path, out_root, vector_spec["hex_format"])
        for case in vector_spec["cases"]
    ]
    verify_vectors(out_root, rows)
    write_summary(out_root / "summary.csv", rows)
    write_summary(Path("data/model/vector_summary.csv"), rows)
    total_mismatch = sum(int(row["mismatch_count"]) for row in rows)
    print(f"[SUMMARY] generated={len(rows)} total_mismatch={total_mismatch}")
    for row in rows:
        print(
            f"[CASE] {row['case_id']} mode={row['decision_mode']} "
            f"channel={row['channel']} mismatch={row['mismatch_count']} "
            f"first={row['first_mismatch']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
