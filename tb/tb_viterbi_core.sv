`timescale 1ns/1ps
import viterbi_pkg::*;

module tb_viterbi_core;
  logic clk;
  logic rst;
  logic start;
  logic in_valid;
  logic rx_bit;
  logic in_ready;
  logic out_valid;
  logic out_bit;
  logic [$clog2(PAYLOAD_BITS+1)-1:0] out_index;
  logic done;

  logic rx_bits [0:CODE_BITS-1];
  logic golden_bits [0:PAYLOAD_BITS-1];
  logic decoded_bits [0:PAYLOAD_BITS-1];
  string case_id;
  string case_dir;
  string rx_path;
  string golden_path;
  int out_count;
  int mismatch_count;
  int first_mismatch;
  int case_file;

  viterbi_decoder_core dut (
    .clk(clk),
    .rst(rst),
    .start(start),
    .in_valid(in_valid),
    .rx_bit(rx_bit),
    .in_ready(in_ready),
    .out_valid(out_valid),
    .out_bit(out_bit),
    .out_index(out_index),
    .done(done)
  );

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  task automatic drive_frame;
    begin
      @(posedge clk);
      start <= 1'b1;
      @(posedge clk);
      start <= 1'b0;

      wait (in_ready == 1'b1);
      for (int i = 0; i < CODE_BITS; i++) begin
        @(posedge clk);
        in_valid <= 1'b1;
        rx_bit <= rx_bits[i];
      end
      @(posedge clk);
      in_valid <= 1'b0;
      rx_bit <= 1'b0;
    end
  endtask

  task automatic collect_output;
    begin
      out_count = 0;
      mismatch_count = 0;
      first_mismatch = -1;
      while (out_count < PAYLOAD_BITS) begin
        @(negedge clk);
        if (out_valid) begin
          decoded_bits[out_count] = out_bit;
          if (out_bit !== golden_bits[out_count]) begin
            mismatch_count++;
            if (first_mismatch < 0) begin
              first_mismatch = out_count;
            end
          end
          out_count++;
        end
      end
      wait (done == 1'b1);
      @(negedge clk);
    end
  endtask

  initial begin
    case_file = $fopen("tb/current_case.txt", "r");
    if (case_file != 0) begin
      void'($fscanf(case_file, "%s", case_id));
      $fclose(case_file);
    end else begin
      case_id = "no_noise";
    end
    case_dir = {"vectors/", case_id};
    rx_path = {case_dir, "/rx_hard.hex"};
    golden_path = {case_dir, "/golden_decoded.hex"};
    $display("CASE_START case=%s", case_dir);
    $readmemh(rx_path, rx_bits);
    $readmemh(golden_path, golden_bits);

    rst = 1'b1;
    start = 1'b0;
    in_valid = 1'b0;
    rx_bit = 1'b0;
    repeat (5) @(posedge clk);
    rst = 1'b0;

    fork
      drive_frame();
      collect_output();
    join

    if (mismatch_count == 0) begin
      $display("CASE_PASS case=%s decoded_bits=%0d mismatch=0", case_dir, out_count);
      $finish;
    end else begin
      $display(
        "CASE_FAIL case=%s decoded_bits=%0d mismatch=%0d first_mismatch=%0d expected=%0d actual=%0d",
        case_dir,
        out_count,
        mismatch_count,
        first_mismatch,
        golden_bits[first_mismatch],
        decoded_bits[first_mismatch]
      );
      $fatal(1);
    end
  end
endmodule
