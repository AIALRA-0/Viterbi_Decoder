#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def octal_literal(value: int | str, width: int) -> str:
    return f"{width}'o{value}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", default="spec/viterbi_spec.json")
    parser.add_argument("--out", default="rtl/common/viterbi_pkg.sv")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    code = spec["code"]
    vectors = spec["vector_generation"]
    k = int(code["constraint_length"])
    output_bits = int(code["rate"].split("/")[1])
    num_states = int(code["state_count"])
    payload_bits = int(vectors["default_payload_length"])
    frame_bits = payload_bits + k - 1
    code_bits = frame_bits * output_bits
    metric_width = max(10, code_bits.bit_length() + 2)
    state_bits = (num_states - 1).bit_length()
    polynomials = code["polynomials_octal"]

    if len(polynomials) != output_bits:
        raise ValueError("Polynomial count does not match code rate")

    polynomial_cases = "\n".join(
        f"      {idx}: polynomial = {octal_literal(poly, k)};"
        for idx, poly in enumerate(polynomials)
    )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        f"""`timescale 1ns/1ps
package viterbi_pkg;
  localparam int K = {k};
  localparam int OUTPUT_BITS = {output_bits};
  localparam int NUM_STATES = {num_states};
  localparam int STATE_BITS = {state_bits};
  localparam int PAYLOAD_BITS = {payload_bits};
  localparam int FRAME_BITS = {frame_bits};
  localparam int CODE_BITS = {code_bits};
  localparam int METRIC_WIDTH = {metric_width};
  localparam logic [METRIC_WIDTH-1:0] INF_METRIC = {{METRIC_WIDTH{{1'b1}}}};

  function automatic logic [K-1:0] polynomial(input int idx);
    begin
      polynomial = '0;
      case (idx)
{polynomial_cases}
        default: polynomial = '0;
      endcase
    end
  endfunction

  function automatic logic parity(input logic [K-1:0] value);
    parity = ^value;
  endfunction

  function automatic logic [OUTPUT_BITS-1:0] expected_output(
    input logic input_bit,
    input logic [STATE_BITS-1:0] state
  );
    logic [K-1:0] reg_value;
    begin
      reg_value = ({{1'b0, state}} << 1) | input_bit;
      for (int i = 0; i < OUTPUT_BITS; i++) begin
        expected_output[i] = parity(reg_value & polynomial(i));
      end
    end
  endfunction

  function automatic logic [STATE_BITS-1:0] next_state_fn(
    input logic input_bit,
    input logic [STATE_BITS-1:0] state
  );
    next_state_fn = ((state << 1) | input_bit) & (NUM_STATES - 1);
  endfunction

  function automatic logic [METRIC_WIDTH-1:0] branch_metric_hard(
    input logic [OUTPUT_BITS-1:0] rx_symbol,
    input logic [OUTPUT_BITS-1:0] expected_symbol
  );
    logic [METRIC_WIDTH-1:0] metric;
    begin
      metric = '0;
      for (int i = 0; i < OUTPUT_BITS; i++) begin
        metric = metric + (rx_symbol[i] ^ expected_symbol[i]);
      end
      branch_metric_hard = metric;
    end
  endfunction
endpackage
""",
        encoding="ascii",
    )
    print(f"[OK] wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
