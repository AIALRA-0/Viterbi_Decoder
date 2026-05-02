`timescale 1ns/1ps
import viterbi_pkg::*;

module viterbi_axis_wrapper #(
  parameter COUNT_WIDTH = 32
) (
  input  logic clk,
  input  logic rst,
  input  logic start_pulse,
  input  logic soft_reset,
  input  logic [COUNT_WIDTH-1:0] sample_count,
  input  logic s_axis_tvalid,
  output logic s_axis_tready,
  input  logic [15:0] s_axis_tdata,
  output logic m_axis_tvalid,
  input  logic m_axis_tready,
  output logic [15:0] m_axis_tdata,
  output logic m_axis_tlast,
  output logic [COUNT_WIDTH-1:0] debug_samples_seen,
  output logic [COUNT_WIDTH-1:0] debug_samples_emitted,
  output logic [COUNT_WIDTH-1:0] debug_input_valid_cycles,
  output logic [COUNT_WIDTH-1:0] debug_input_ready_cycles,
  output logic done,
  output logic busy,
  output logic error,
  output logic [31:0] cycle_count
);
  logic core_in_ready;
  logic core_out_valid;
  logic core_out_bit;
  logic [$clog2(PAYLOAD_BITS+1)-1:0] core_out_index;
  logic core_done;
  logic run_clear;

  assign run_clear = rst || soft_reset;
  assign s_axis_tready = busy && core_in_ready;
  assign m_axis_tvalid = core_out_valid;
  assign m_axis_tdata = {15'd0, core_out_bit};
  assign m_axis_tlast = core_out_valid && (core_out_index == PAYLOAD_BITS - 1);

  viterbi_decoder_core_soft3 u_core (
    .clk(clk),
    .rst(run_clear),
    .start(start_pulse),
    .in_valid(s_axis_tvalid && s_axis_tready),
    .rx_soft(s_axis_tdata[SOFT_WIDTH_BITS-1:0]),
    .in_ready(core_in_ready),
    .out_valid(core_out_valid),
    .out_bit(core_out_bit),
    .out_index(core_out_index),
    .done(core_done)
  );

  always_ff @(posedge clk) begin
    if (rst || soft_reset) begin
      debug_samples_seen <= '0;
      debug_samples_emitted <= '0;
      debug_input_valid_cycles <= '0;
      debug_input_ready_cycles <= '0;
      done <= 1'b0;
      busy <= 1'b0;
      error <= 1'b0;
      cycle_count <= 32'd0;
    end else begin
      if (start_pulse) begin
        debug_samples_seen <= '0;
        debug_samples_emitted <= '0;
        debug_input_valid_cycles <= '0;
        debug_input_ready_cycles <= '0;
        done <= 1'b0;
        busy <= (sample_count != 0);
        error <= (sample_count != CODE_BITS);
        cycle_count <= 32'd0;
      end else begin
        if (busy) begin
          cycle_count <= cycle_count + 1;
          if (s_axis_tvalid) begin
            debug_input_valid_cycles <= debug_input_valid_cycles + 1'b1;
          end
          if (s_axis_tready) begin
            debug_input_ready_cycles <= debug_input_ready_cycles + 1'b1;
          end
          if (s_axis_tvalid && s_axis_tready) begin
            debug_samples_seen <= debug_samples_seen + 1'b1;
          end
          if (core_out_valid && m_axis_tready) begin
            debug_samples_emitted <= debug_samples_emitted + 1'b1;
          end
        end
        if (core_done) begin
          done <= 1'b1;
          busy <= 1'b0;
        end
      end
    end
  end
endmodule

