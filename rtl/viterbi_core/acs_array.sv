`timescale 1ns/1ps
import viterbi_pkg::*;

module acs_array (
  input  logic [METRIC_WIDTH-1:0] metric_in [0:NUM_STATES-1],
  input  logic [OUTPUT_BITS-1:0] rx_symbol,
  output logic [METRIC_WIDTH-1:0] metric_out [0:NUM_STATES-1],
  output logic survivor_bit [0:NUM_STATES-1],
  output logic [STATE_BITS-1:0] survivor_prev [0:NUM_STATES-1]
);
  always_comb begin
    for (int ns = 0; ns < NUM_STATES; ns++) begin
      metric_out[ns] = INF_METRIC;
      survivor_bit[ns] = 1'b0;
      survivor_prev[ns] = '0;
    end

    for (int state = 0; state < NUM_STATES; state++) begin
      if (metric_in[state] != INF_METRIC) begin
        for (int bit_idx = 0; bit_idx < 2; bit_idx++) begin
          logic [STATE_BITS-1:0] ns;
          logic [OUTPUT_BITS-1:0] expected;
          logic [METRIC_WIDTH-1:0] candidate;
          ns = next_state_fn(bit_idx[0], state[STATE_BITS-1:0]);
          expected = expected_output(bit_idx[0], state[STATE_BITS-1:0]);
          candidate = metric_in[state] + branch_metric_hard(rx_symbol, expected);
          if (candidate < metric_out[ns]) begin
            metric_out[ns] = candidate;
            survivor_bit[ns] = bit_idx[0];
            survivor_prev[ns] = state[STATE_BITS-1:0];
          end
        end
      end
    end
  end
endmodule
