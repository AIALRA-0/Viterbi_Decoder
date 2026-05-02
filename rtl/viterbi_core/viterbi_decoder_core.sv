`timescale 1ns/1ps
import viterbi_pkg::*;

module viterbi_decoder_core (
  input  logic clk,
  input  logic rst,
  input  logic start,
  input  logic in_valid,
  input  logic rx_bit,
  output logic in_ready,
  output logic out_valid,
  output logic out_bit,
  output logic [$clog2(PAYLOAD_BITS+1)-1:0] out_index,
  output logic done
);
  typedef enum logic [2:0] {
    S_IDLE,
    S_LOAD,
    S_INIT,
    S_COMPUTE,
    S_TRACE,
    S_OUTPUT
  } state_t;

  state_t state_q;
  logic rx_mem [0:CODE_BITS-1];
  logic decoded_mem [0:FRAME_BITS-1];
  logic survivor_bit [0:FRAME_BITS-1][0:NUM_STATES-1];
  logic [STATE_BITS-1:0] survivor_prev [0:FRAME_BITS-1][0:NUM_STATES-1];
  logic [METRIC_WIDTH-1:0] metrics [0:NUM_STATES-1];

  int load_idx;
  int compute_idx;
  int trace_idx;
  int output_idx;
  logic [STATE_BITS-1:0] trace_state;

  always_ff @(posedge clk) begin
    if (rst) begin
      state_q <= S_IDLE;
      in_ready <= 1'b0;
      out_valid <= 1'b0;
      out_bit <= 1'b0;
      out_index <= '0;
      done <= 1'b0;
      load_idx <= 0;
      compute_idx <= 0;
      trace_idx <= 0;
      output_idx <= 0;
      trace_state <= '0;
      for (int i = 0; i < NUM_STATES; i++) begin
        metrics[i] <= INF_METRIC;
      end
    end else begin
      out_valid <= 1'b0;
      done <= 1'b0;

      case (state_q)
        S_IDLE: begin
          in_ready <= 1'b0;
          if (start) begin
            load_idx <= 0;
            in_ready <= 1'b1;
            state_q <= S_LOAD;
          end
        end

        S_LOAD: begin
          if (in_valid && in_ready) begin
            rx_mem[load_idx] <= rx_bit;
            if (load_idx == CODE_BITS - 1) begin
              in_ready <= 1'b0;
              state_q <= S_INIT;
            end
            load_idx <= load_idx + 1;
          end
        end

        S_INIT: begin
          for (int i = 0; i < NUM_STATES; i++) begin
            metrics[i] <= (i == 0) ? '0 : INF_METRIC;
          end
          compute_idx <= 0;
          state_q <= S_COMPUTE;
        end

        S_COMPUTE: begin : compute_block
          logic [OUTPUT_BITS-1:0] rx_symbol;
          logic [METRIC_WIDTH-1:0] next_metrics [0:NUM_STATES-1];
          logic next_survivor_bit [0:NUM_STATES-1];
          logic [STATE_BITS-1:0] next_survivor_prev [0:NUM_STATES-1];

          for (int ob = 0; ob < OUTPUT_BITS; ob++) begin
            rx_symbol[ob] = rx_mem[compute_idx * OUTPUT_BITS + ob];
          end

          for (int ns_init = 0; ns_init < NUM_STATES; ns_init++) begin
            next_metrics[ns_init] = INF_METRIC;
            next_survivor_bit[ns_init] = 1'b0;
            next_survivor_prev[ns_init] = '0;
          end

          for (int state = 0; state < NUM_STATES; state++) begin
            if (metrics[state] != INF_METRIC) begin
              for (int bit_idx = 0; bit_idx < 2; bit_idx++) begin
                logic [STATE_BITS-1:0] ns;
                logic [OUTPUT_BITS-1:0] expected;
                logic [METRIC_WIDTH-1:0] candidate;
                ns = next_state_fn(bit_idx[0], state[STATE_BITS-1:0]);
                expected = expected_output(bit_idx[0], state[STATE_BITS-1:0]);
                candidate = metrics[state] + branch_metric_hard(rx_symbol, expected);
                if (candidate < next_metrics[ns]) begin
                  next_metrics[ns] = candidate;
                  next_survivor_bit[ns] = bit_idx[0];
                  next_survivor_prev[ns] = state[STATE_BITS-1:0];
                end
              end
            end
          end

          for (int ns = 0; ns < NUM_STATES; ns++) begin
            metrics[ns] <= next_metrics[ns];
            survivor_bit[compute_idx][ns] <= next_survivor_bit[ns];
            survivor_prev[compute_idx][ns] <= next_survivor_prev[ns];
          end

          if (compute_idx == FRAME_BITS - 1) begin
            trace_idx <= FRAME_BITS;
            trace_state <= '0;
            state_q <= S_TRACE;
          end else begin
            compute_idx <= compute_idx + 1;
          end
        end

        S_TRACE: begin
          int idx;
          idx = trace_idx - 1;
          decoded_mem[idx] <= survivor_bit[idx][trace_state];
          trace_state <= survivor_prev[idx][trace_state];
          trace_idx <= idx;
          if (trace_idx == 1) begin
            output_idx <= 0;
            state_q <= S_OUTPUT;
          end
        end

        S_OUTPUT: begin
          out_valid <= 1'b1;
          out_bit <= decoded_mem[output_idx];
          out_index <= output_idx[$bits(out_index)-1:0];
          if (output_idx == PAYLOAD_BITS - 1) begin
            done <= 1'b1;
            state_q <= S_IDLE;
          end else begin
            output_idx <= output_idx + 1;
          end
        end

        default: state_q <= S_IDLE;
      endcase
    end
  end
endmodule
