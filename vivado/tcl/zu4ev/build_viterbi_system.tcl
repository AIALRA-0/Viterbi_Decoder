set root [file normalize [pwd]]
set part_name "xczu4ev-sfvc784-2-i"
set system_top "viterbi_zu4ev_shell"
if {[info exists ::env(VITERBI_BOARD_BUILD_DIR)] && $::env(VITERBI_BOARD_BUILD_DIR) ne ""} {
    set build_dir $::env(VITERBI_BOARD_BUILD_DIR)
} else {
    set build_dir "C:/vbd_viterbi"
}

file mkdir $build_dir
create_project $system_top $build_dir -part $part_name -force

set rtl_files [list \
    [file join $root rtl common viterbi_pkg.sv] \
    [file join $root rtl viterbi_core bmu_soft3.sv] \
    [file join $root rtl viterbi_core path_metric_normalizer.sv] \
    [file join $root rtl viterbi_core viterbi_decoder_core_soft3.sv] \
    [file join $root rtl system viterbi_control_regs.v] \
    [file join $root rtl system viterbi_axis_wrapper.sv] \
    [file join $root rtl system viterbi_zu4ev_shell.v] \
]
add_files -norecurse $rtl_files
update_compile_order -fileset sources_1

create_bd_design viterbi_mpsoc_system

create_bd_cell -type ip -vlnv xilinx.com:ip:zynq_ultra_ps_e:* ps_0
set_property -dict [list \
    CONFIG.PSU__USE__M_AXI_GP0 {1} \
    CONFIG.PSU__USE__S_AXI_GP0 {1} \
    CONFIG.PSU__FPGA_PL0_ENABLE {1} \
    CONFIG.PSU__UART0__PERIPHERAL__ENABLE {1} \
    CONFIG.PSU__UART0__PERIPHERAL__IO {MIO 34 .. 35} \
    CONFIG.PSU__UART0__BAUD_RATE {115200} \
    CONFIG.PSU__CRL_APB__PL0_REF_CTRL__FREQMHZ {25} \
] [get_bd_cells ps_0]

create_bd_cell -type ip -vlnv xilinx.com:ip:proc_sys_reset:* rst_0
create_bd_cell -type ip -vlnv xilinx.com:ip:smartconnect:* ctrl_smc
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:* data_ic
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_dma:* axi_dma_0
create_bd_cell -type module -reference $system_top viterbi_shell_0

set_property -dict [list CONFIG.NUM_SI {2} CONFIG.NUM_MI {2}] [get_bd_cells ctrl_smc]
set_property -dict [list CONFIG.NUM_SI {2} CONFIG.NUM_MI {1}] [get_bd_cells data_ic]
set_property -dict [list \
    CONFIG.c_include_sg {0} \
    CONFIG.c_include_mm2s {1} \
    CONFIG.c_include_s2mm {1} \
    CONFIG.c_m_axis_mm2s_tdata_width {16} \
    CONFIG.c_s_axis_s2mm_tdata_width {16} \
    CONFIG.c_m_axi_mm2s_data_width {32} \
    CONFIG.c_m_axi_s2mm_data_width {32} \
    CONFIG.c_addr_width {32} \
] [get_bd_cells axi_dma_0]

connect_bd_net [get_bd_pins ps_0/pl_clk0] \
    [get_bd_pins ps_0/maxihpm0_fpd_aclk] \
    [get_bd_pins ps_0/maxihpm0_lpd_aclk] \
    [get_bd_pins ps_0/saxihpc0_fpd_aclk] \
    [get_bd_pins ctrl_smc/aclk] \
    [get_bd_pins data_ic/ACLK] \
    [get_bd_pins data_ic/M00_ACLK] \
    [get_bd_pins data_ic/S00_ACLK] \
    [get_bd_pins data_ic/S01_ACLK] \
    [get_bd_pins axi_dma_0/s_axi_lite_aclk] \
    [get_bd_pins axi_dma_0/m_axi_mm2s_aclk] \
    [get_bd_pins axi_dma_0/m_axi_s2mm_aclk] \
    [get_bd_pins viterbi_shell_0/aclk] \
    [get_bd_pins rst_0/slowest_sync_clk]

connect_bd_net [get_bd_pins ps_0/pl_resetn0] [get_bd_pins rst_0/ext_reset_in]
connect_bd_net [get_bd_pins rst_0/peripheral_aresetn] \
    [get_bd_pins ctrl_smc/aresetn] \
    [get_bd_pins data_ic/ARESETN] \
    [get_bd_pins data_ic/M00_ARESETN] \
    [get_bd_pins data_ic/S00_ARESETN] \
    [get_bd_pins data_ic/S01_ARESETN] \
    [get_bd_pins axi_dma_0/axi_resetn] \
    [get_bd_pins viterbi_shell_0/aresetn]

connect_bd_intf_net [get_bd_intf_pins ps_0/M_AXI_HPM0_FPD] [get_bd_intf_pins ctrl_smc/S01_AXI]
connect_bd_intf_net [get_bd_intf_pins ps_0/M_AXI_HPM0_LPD] [get_bd_intf_pins ctrl_smc/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins ctrl_smc/M00_AXI] [get_bd_intf_pins axi_dma_0/S_AXI_LITE]
connect_bd_intf_net [get_bd_intf_pins ctrl_smc/M01_AXI] [get_bd_intf_pins viterbi_shell_0/s_axi_ctrl]
connect_bd_intf_net [get_bd_intf_pins axi_dma_0/M_AXI_MM2S] [get_bd_intf_pins data_ic/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins axi_dma_0/M_AXI_S2MM] [get_bd_intf_pins data_ic/S01_AXI]
connect_bd_intf_net [get_bd_intf_pins data_ic/M00_AXI] [get_bd_intf_pins ps_0/S_AXI_HPC0_FPD]

connect_bd_intf_net [get_bd_intf_pins axi_dma_0/M_AXIS_MM2S] [get_bd_intf_pins viterbi_shell_0/s_axis_in]
connect_bd_intf_net [get_bd_intf_pins viterbi_shell_0/m_axis_out] [get_bd_intf_pins axi_dma_0/S_AXIS_S2MM]

assign_bd_address
foreach addr_space_name {/axi_dma_0/Data_MM2S /axi_dma_0/Data_S2MM} {
    set excluded_segs [get_bd_addr_segs -quiet -excluded -of_objects [get_bd_addr_spaces $addr_space_name]]
    foreach seg $excluded_segs {
        if {[get_property NAME $seg] eq "SEG_ps_0_HPC0_LPS_OCM"} {
            include_bd_addr_seg $seg
        }
    }
}
set shell_seg [get_bd_addr_segs -quiet -of_objects [get_bd_addr_spaces ps_0/Data] *viterbi_shell_0*]
if {[llength $shell_seg] > 0} {
    set_property offset 0xA0000000 [lindex $shell_seg 0]
}

save_bd_design
validate_bd_design
set bd_file [file normalize [file join $build_dir ${system_top}.srcs sources_1 bd viterbi_mpsoc_system viterbi_mpsoc_system.bd]]
generate_target all [get_files -quiet [list $bd_file]]
make_wrapper -files [get_files -quiet [list $bd_file]] -top
set wrapper_file [file normalize [file join $build_dir ${system_top}.gen sources_1 bd viterbi_mpsoc_system hdl viterbi_mpsoc_system_wrapper.v]]
add_files -norecurse [list $wrapper_file]
set_property top viterbi_mpsoc_system_wrapper [current_fileset]
update_compile_order -fileset sources_1

launch_runs impl_1 -to_step write_bitstream
wait_on_run impl_1

write_hw_platform -fixed -include_bit -force -file [file join $build_dir ${system_top}.xsa]
close_project
