`timescale 1ns/1ps
import viterbi_pkg::*;

module traceback_engine (
  input  logic clk,
  input  logic rst,
  input  logic start,
  output logic busy,
  output logic done
);
  always_ff @(posedge clk) begin
    if (rst) begin
      busy <= 1'b0;
      done <= 1'b0;
    end else begin
      done <= 1'b0;
      if (start) begin
        busy <= 1'b1;
      end else if (busy) begin
        busy <= 1'b0;
        done <= 1'b1;
      end
    end
  end
endmodule

