# M6 Timing Analysis

Data source: `data/impl/vivado_summary.csv` and `data/impl/hero_impl/timing_summary.rpt`.

The baseline hard-decision synthesis run met the 10 ns clock target with WNS 6.956 ns and TNS 0.000 ns.

The soft3 hero synthesis run did not meet the 10 ns clock target. Vivado reported WNS -23.241 ns and TNS -17607.301 ns.

The soft3 hero implementation run completed placement and routing, but timing was still not met. Vivado reported WNS -20.433 ns and TNS -16272.939 ns.

The routed critical setup path starts at `compute_idx_reg[4]/C` and ends at `metrics_reg[47][10]/D`. Vivado reports 30.415 ns data path delay, split into 13.839 ns logic delay and 16.576 ns routing delay, with 116 logic levels. This points to the current one-cycle 64-state soft ACS update and subtract-min reduction as the critical path. M6 records this timing failure rather than hiding it; a later performance-focused revision should pipeline the ACS/reduction tree or process fewer states per cycle.
