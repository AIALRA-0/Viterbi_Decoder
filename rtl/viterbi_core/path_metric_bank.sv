`timescale 1ns/1ps
import viterbi_pkg::*;

module path_metric_bank (
  input  logic clk,
  input  logic rst,
  input  logic load,
  input  logic init_zero,
  input  logic [METRIC_WIDTH-1:0] metric_next [0:NUM_STATES-1],
  output logic [METRIC_WIDTH-1:0] metric_q [0:NUM_STATES-1]
);
  always_ff @(posedge clk) begin
    if (rst || init_zero) begin
      for (int i = 0; i < NUM_STATES; i++) begin
        metric_q[i] <= (i == 0) ? '0 : INF_METRIC;
      end
    end else if (load) begin
      for (int i = 0; i < NUM_STATES; i++) begin
        metric_q[i] <= metric_next[i];
      end
    end
  end
endmodule

