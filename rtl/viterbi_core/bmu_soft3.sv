`timescale 1ns/1ps
import viterbi_pkg::*;

module bmu_soft3 (
  input  logic [OUTPUT_BITS*SOFT_WIDTH_BITS-1:0] rx_symbol,
  input  logic [OUTPUT_BITS-1:0] expected_symbol,
  output logic [HERO_METRIC_WIDTH-1:0] metric
);
  always_comb begin
    metric = branch_metric_soft3(rx_symbol, expected_symbol);
  end
endmodule

