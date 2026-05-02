`timescale 1ns/1ps
package viterbi_pkg;
  localparam int K = 7;
  localparam int OUTPUT_BITS = 2;
  localparam int NUM_STATES = 64;
  localparam int STATE_BITS = 6;
  localparam int PAYLOAD_BITS = 96;
  localparam int FRAME_BITS = 102;
  localparam int CODE_BITS = 204;
  localparam int METRIC_WIDTH = 10;
  localparam logic [METRIC_WIDTH-1:0] INF_METRIC = {METRIC_WIDTH{1'b1}};

  function automatic logic [K-1:0] polynomial(input int idx);
    begin
      polynomial = '0;
      case (idx)
      0: polynomial = 7'o171;
      1: polynomial = 7'o133;
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
      reg_value = ({1'b0, state} << 1) | input_bit;
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
