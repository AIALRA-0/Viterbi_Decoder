`timescale 1ns/1ps

module viterbi_zu4ev_shell (
    input  wire         aclk,
    input  wire         aresetn,
    input  wire [5:0]   s_axi_ctrl_awaddr,
    input  wire         s_axi_ctrl_awvalid,
    output wire         s_axi_ctrl_awready,
    input  wire [31:0]  s_axi_ctrl_wdata,
    input  wire [3:0]   s_axi_ctrl_wstrb,
    input  wire         s_axi_ctrl_wvalid,
    output wire         s_axi_ctrl_wready,
    output wire [1:0]   s_axi_ctrl_bresp,
    output wire         s_axi_ctrl_bvalid,
    input  wire         s_axi_ctrl_bready,
    input  wire [5:0]   s_axi_ctrl_araddr,
    input  wire         s_axi_ctrl_arvalid,
    output wire         s_axi_ctrl_arready,
    output wire [31:0]  s_axi_ctrl_rdata,
    output wire [1:0]   s_axi_ctrl_rresp,
    output wire         s_axi_ctrl_rvalid,
    input  wire         s_axi_ctrl_rready,
    input  wire [15:0]  s_axis_in_tdata,
    input  wire         s_axis_in_tvalid,
    output wire         s_axis_in_tready,
    input  wire         s_axis_in_tlast,
    output wire [15:0]  m_axis_out_tdata,
    output wire         m_axis_out_tvalid,
    input  wire         m_axis_out_tready,
    output wire         m_axis_out_tlast,
    output wire         irq
);

wire start_pulse;
wire soft_reset;
wire [31:0] sample_count;
wire [31:0] mismatch_count;
wire done;
wire busy;
wire error;
wire [31:0] cycle_count;
wire [31:0] debug_samples_seen;
wire [31:0] debug_samples_emitted;
wire [31:0] debug_input_valid_cycles;
wire [31:0] debug_input_ready_cycles;

viterbi_control_regs u_ctrl (
    .clk(aclk),
    .rstn(aresetn),
    .s_axi_awaddr(s_axi_ctrl_awaddr),
    .s_axi_awvalid(s_axi_ctrl_awvalid),
    .s_axi_awready(s_axi_ctrl_awready),
    .s_axi_wdata(s_axi_ctrl_wdata),
    .s_axi_wstrb(s_axi_ctrl_wstrb),
    .s_axi_wvalid(s_axi_ctrl_wvalid),
    .s_axi_wready(s_axi_ctrl_wready),
    .s_axi_bresp(s_axi_ctrl_bresp),
    .s_axi_bvalid(s_axi_ctrl_bvalid),
    .s_axi_bready(s_axi_ctrl_bready),
    .s_axi_araddr(s_axi_ctrl_araddr),
    .s_axi_arvalid(s_axi_ctrl_arvalid),
    .s_axi_arready(s_axi_ctrl_arready),
    .s_axi_rdata(s_axi_ctrl_rdata),
    .s_axi_rresp(s_axi_ctrl_rresp),
    .s_axi_rvalid(s_axi_ctrl_rvalid),
    .s_axi_rready(s_axi_ctrl_rready),
    .start_pulse(start_pulse),
    .soft_reset(soft_reset),
    .sample_count(sample_count),
    .mismatch_count(mismatch_count),
    .done(done),
    .busy(busy),
    .error(error),
    .cycle_count(cycle_count),
    .dbg_samples_seen(debug_samples_seen),
    .dbg_samples_emitted(debug_samples_emitted),
    .dbg_input_valid_cycles(debug_input_valid_cycles),
    .dbg_input_ready_cycles(debug_input_ready_cycles)
);

viterbi_axis_wrapper u_axis (
    .clk(aclk),
    .rst(~aresetn),
    .start_pulse(start_pulse),
    .soft_reset(soft_reset),
    .sample_count(sample_count),
    .s_axis_tvalid(s_axis_in_tvalid),
    .s_axis_tready(s_axis_in_tready),
    .s_axis_tdata(s_axis_in_tdata),
    .m_axis_tvalid(m_axis_out_tvalid),
    .m_axis_tready(m_axis_out_tready),
    .m_axis_tdata(m_axis_out_tdata),
    .m_axis_tlast(m_axis_out_tlast),
    .done(done),
    .busy(busy),
    .error(error),
    .cycle_count(cycle_count),
    .debug_samples_seen(debug_samples_seen),
    .debug_samples_emitted(debug_samples_emitted),
    .debug_input_valid_cycles(debug_input_valid_cycles),
    .debug_input_ready_cycles(debug_input_ready_cycles)
);

assign irq = done;

endmodule
