set top [lindex $argv 0]
set out_dir [lindex $argv 1]
set part [lindex $argv 2]
set root [file normalize [pwd]]

if {$top eq "" || $out_dir eq "" || $part eq ""} {
  error "Usage: run_impl.tcl <top> <out_dir> <part>"
}

file mkdir $out_dir

read_verilog -sv [file join $root rtl common viterbi_pkg.sv]
if {$top eq "viterbi_decoder_core_soft3"} {
  read_verilog -sv [file join $root rtl viterbi_core bmu_soft3.sv]
  read_verilog -sv [file join $root rtl viterbi_core path_metric_normalizer.sv]
  read_verilog -sv [file join $root rtl viterbi_core viterbi_decoder_core_soft3.sv]
} elseif {$top eq "viterbi_decoder_core"} {
  read_verilog -sv [file join $root rtl viterbi_core bmu_hard.sv]
  read_verilog -sv [file join $root rtl viterbi_core acs_unit.sv]
  read_verilog -sv [file join $root rtl viterbi_core acs_array.sv]
  read_verilog -sv [file join $root rtl viterbi_core path_metric_bank.sv]
  read_verilog -sv [file join $root rtl viterbi_core survivor_ram.sv]
  read_verilog -sv [file join $root rtl viterbi_core traceback_engine.sv]
  read_verilog -sv [file join $root rtl viterbi_core viterbi_decoder_core.sv]
} else {
  error "Unknown top: $top"
}

synth_design -top $top -part $part -mode out_of_context
create_clock -period 10.000 -name clk [get_ports clk]
opt_design
place_design
route_design
report_utilization -file [file join $out_dir utilization.rpt]
report_timing_summary -file [file join $out_dir timing_summary.rpt]
report_power -file [file join $out_dir power.rpt]
write_checkpoint -force [file join $out_dir post_route.dcp]

