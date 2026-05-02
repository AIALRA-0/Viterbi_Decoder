`timescale 1ns/1ps
import viterbi_pkg::*;

module path_metric_normalizer (
  input  logic [HERO_METRIC_WIDTH-1:0] metric_in [0:NUM_STATES-1],
  output logic [HERO_METRIC_WIDTH-1:0] metric_out [0:NUM_STATES-1],
  output logic [HERO_METRIC_WIDTH-1:0] min_metric
);
  always_comb begin
    min_metric = HERO_INF_METRIC;
    for (int i = 0; i < NUM_STATES; i++) begin
      if (metric_in[i] < min_metric) begin
        min_metric = metric_in[i];
      end
    end
    for (int i = 0; i < NUM_STATES; i++) begin
      if (metric_in[i] == HERO_INF_METRIC) begin
        metric_out[i] = HERO_INF_METRIC;
      end else begin
        metric_out[i] = metric_in[i] - min_metric;
      end
    end
  end
endmodule

