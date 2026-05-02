`timescale 1ns/1ps
import viterbi_pkg::*;

module bmu_hard (
  input  logic [OUTPUT_BITS-1:0] rx_symbol,
  input  logic [OUTPUT_BITS-1:0] expected_symbol,
  output logic [METRIC_WIDTH-1:0] metric
);
  always_comb begin
    metric = branch_metric_hard(rx_symbol, expected_symbol);
  end
endmodule

