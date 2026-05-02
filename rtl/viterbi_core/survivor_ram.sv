`timescale 1ns/1ps
import viterbi_pkg::*;

module survivor_ram (
  input  logic clk,
  input  logic write_en,
  input  logic [$clog2(FRAME_BITS)-1:0] write_step,
  input  logic survivor_bit_in [0:NUM_STATES-1],
  input  logic [STATE_BITS-1:0] survivor_prev_in [0:NUM_STATES-1],
  input  logic [$clog2(FRAME_BITS)-1:0] read_step,
  input  logic [STATE_BITS-1:0] read_state,
  output logic read_bit,
  output logic [STATE_BITS-1:0] read_prev
);
  logic survivor_bit_mem [0:FRAME_BITS-1][0:NUM_STATES-1];
  logic [STATE_BITS-1:0] survivor_prev_mem [0:FRAME_BITS-1][0:NUM_STATES-1];

  always_ff @(posedge clk) begin
    if (write_en) begin
      for (int i = 0; i < NUM_STATES; i++) begin
        survivor_bit_mem[write_step][i] <= survivor_bit_in[i];
        survivor_prev_mem[write_step][i] <= survivor_prev_in[i];
      end
    end
  end

  always_comb begin
    read_bit = survivor_bit_mem[read_step][read_state];
    read_prev = survivor_prev_mem[read_step][read_state];
  end
endmodule

