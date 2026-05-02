#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


DEFAULT_CASES = ("no_noise", "single_bit_error", "soft_awgn_2db")


def read_hex_values(path: Path) -> list[int]:
    values: list[int] = []
    for line_no, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            values.append(int(line, 16))
        except ValueError:
            values.append(int(line, 10))
    return values


def c_identifier(case_id: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in case_id.lower())


def format_array(values: list[int], indent: str = "    ") -> str:
    chunks: list[str] = []
    for idx in range(0, len(values), 16):
        row = ", ".join(str(value) for value in values[idx : idx + 16])
        chunks.append(f"{indent}{row},")
    return "\n".join(chunks)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Vitis board vectors from M2 hex files.")
    parser.add_argument("--vectors", default="vectors")
    parser.add_argument("--out-dir", default="vitis/zu4ev_baremetal/src/generated")
    parser.add_argument("--cases", nargs="+", default=list(DEFAULT_CASES))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    vectors_root = Path(args.vectors)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    case_records: list[dict[str, object]] = []
    max_input = 0
    max_output = 0

    for case_id in args.cases:
        case_dir = vectors_root / case_id
        input_values = read_hex_values(case_dir / "rx_soft3.hex")
        golden_values = read_hex_values(case_dir / "golden_decoded.hex")
        max_input = max(max_input, len(input_values))
        max_output = max(max_output, len(golden_values))
        case_records.append(
            {
                "case_id": case_id,
                "ident": c_identifier(case_id),
                "input": input_values,
                "golden": golden_values,
            }
        )

    header = f"""#ifndef VITERBI_ZU4EV_VECTORS_H
#define VITERBI_ZU4EV_VECTORS_H

#include <stdint.h>

#define VITERBI_MAX_INPUT_LENGTH {max_input}U
#define VITERBI_MAX_OUTPUT_LENGTH {max_output}U

typedef struct {{
    const char *name;
    const char *run_id;
    uint32_t input_length;
    uint32_t output_length;
    const int16_t *input;
    const int16_t *golden;
}} viterbi_vector_case_t;

"""

    source = '#include "viterbi_vectors.h"\n\n'

    for record in case_records:
        ident = str(record["ident"])
        input_values = record["input"]
        golden_values = record["golden"]
        assert isinstance(input_values, list)
        assert isinstance(golden_values, list)

        header += f"extern const int16_t viterbi_case_{ident}_input[{len(input_values)}];\n"
        header += f"extern const int16_t viterbi_case_{ident}_golden[{len(golden_values)}];\n\n"

        source += f"const int16_t viterbi_case_{ident}_input[{len(input_values)}] = {{\n"
        source += format_array(input_values)
        source += "\n};\n\n"
        source += f"const int16_t viterbi_case_{ident}_golden[{len(golden_values)}] = {{\n"
        source += format_array(golden_values)
        source += "\n};\n\n"

    header += f"extern const viterbi_vector_case_t g_viterbi_vector_cases[{len(case_records)}];\n"
    header += "extern const uint32_t g_viterbi_vector_case_count;\n\n"
    header += "#endif\n"

    source += f"const viterbi_vector_case_t g_viterbi_vector_cases[{len(case_records)}] = {{\n"
    for record in case_records:
        ident = str(record["ident"])
        case_id = str(record["case_id"])
        input_len = len(record["input"])  # type: ignore[arg-type]
        output_len = len(record["golden"])  # type: ignore[arg-type]
        source += (
            f'    {{"{case_id}", "m2_{case_id}", {input_len}U, {output_len}U, '
            f"viterbi_case_{ident}_input, viterbi_case_{ident}_golden}},\n"
        )
    source += "};\n\n"
    source += f"const uint32_t g_viterbi_vector_case_count = {len(case_records)}U;\n"

    (out_dir / "viterbi_vectors.h").write_text(header, encoding="ascii")
    (out_dir / "viterbi_vectors.c").write_text(source, encoding="ascii")
    print(f"Wrote {out_dir / 'viterbi_vectors.h'}")
    print(f"Wrote {out_dir / 'viterbi_vectors.c'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
