`timescale 1ns/1ps
import viterbi_pkg::*;

module acs_unit (
  input  logic [METRIC_WIDTH-1:0] metric_a,
  input  logic [METRIC_WIDTH-1:0] metric_b,
  input  logic [METRIC_WIDTH-1:0] branch_a,
  input  logic [METRIC_WIDTH-1:0] branch_b,
  output logic [METRIC_WIDTH-1:0] metric_out,
  output logic select_b
);
  logic [METRIC_WIDTH-1:0] candidate_a;
  logic [METRIC_WIDTH-1:0] candidate_b;

  always_comb begin
    candidate_a = metric_a + branch_a;
    candidate_b = metric_b + branch_b;
    if (candidate_b < candidate_a) begin
      metric_out = candidate_b;
      select_b = 1'b1;
    end else begin
      metric_out = candidate_a;
      select_b = 1'b0;
    end
  end
endmodule

