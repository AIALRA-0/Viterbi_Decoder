#include <stdint.h>

#include "xaxidma.h"
#include "xaxidma_hw.h"
#include "xil_cache.h"
#include "xil_io.h"
#include "xil_mmu.h"
#include "xil_printf.h"
#include "xstatus.h"
#include "xtime_l.h"

#include "generated/viterbi_vectors.h"
#include "viterbi_zu4ev_hw.h"

static XAxiDma g_axi_dma;
static int16_t g_tx_buffer[VITERBI_MAX_INPUT_LENGTH] __attribute__((aligned(64)));
static int16_t g_rx_buffer[VITERBI_MAX_OUTPUT_LENGTH] __attribute__((aligned(64)));

#define VITERBI_DMA_TIMEOUT_TICKS  (COUNTS_PER_SECOND * 10ULL)
#define VITERBI_CORE_TIMEOUT_TICKS (COUNTS_PER_SECOND * 10ULL)

static inline void viterbi_reg_write(uint32_t offset, uint32_t value) {
    Xil_Out32(VITERBI_CTRL_BASEADDR + offset, value);
}

static inline uint32_t viterbi_reg_read(uint32_t offset) {
    return Xil_In32(VITERBI_CTRL_BASEADDR + offset);
}

static void viterbi_platform_init(void) {
    Xil_SetTlbAttributes((UINTPTR)VITERBI_CTRL_BASEADDR, DEVICE_MEMORY);
    Xil_DCacheDisable();

    xil_printf("DMA buffers tx=0x%016llx rx=0x%016llx\r\n",
               (unsigned long long)(UINTPTR)g_tx_buffer,
               (unsigned long long)(UINTPTR)g_rx_buffer);
}

static int viterbi_dma_init(void) {
    XAxiDma_Config *cfg = XAxiDma_LookupConfig(VITERBI_DMA_DEVICE_ID);
    if (cfg == NULL) {
        xil_printf("DMA lookup failed\r\n");
        return XST_FAILURE;
    }
    if (XAxiDma_CfgInitialize(&g_axi_dma, cfg) != XST_SUCCESS) {
        xil_printf("DMA init failed\r\n");
        return XST_FAILURE;
    }
    if (XAxiDma_HasSg(&g_axi_dma)) {
        xil_printf("Scatter-gather mode is not supported\r\n");
        return XST_FAILURE;
    }
    XAxiDma_Reset(&g_axi_dma);
    while (!XAxiDma_ResetIsDone(&g_axi_dma)) {
    }
    return XST_SUCCESS;
}

static void viterbi_dump_dma_state(const char *case_name, const char *phase) {
    uint32_t mm2s_sr = XAxiDma_ReadReg(g_axi_dma.RegBase, XAXIDMA_TX_OFFSET + XAXIDMA_SR_OFFSET);
    uint32_t s2mm_sr = XAxiDma_ReadReg(g_axi_dma.RegBase, XAXIDMA_RX_OFFSET + XAXIDMA_SR_OFFSET);
    uint32_t mm2s_cr = XAxiDma_ReadReg(g_axi_dma.RegBase, XAXIDMA_TX_OFFSET + XAXIDMA_CR_OFFSET);
    uint32_t s2mm_cr = XAxiDma_ReadReg(g_axi_dma.RegBase, XAXIDMA_RX_OFFSET + XAXIDMA_CR_OFFSET);

    xil_printf("[%s] dma_state@%s mm2s_cr=0x%08lx mm2s_sr=0x%08lx s2mm_cr=0x%08lx s2mm_sr=0x%08lx\r\n",
               case_name,
               phase,
               (unsigned long)mm2s_cr,
               (unsigned long)mm2s_sr,
               (unsigned long)s2mm_cr,
               (unsigned long)s2mm_sr);
}

static void viterbi_dump_shell_state(const char *case_name, const char *phase) {
    xil_printf("[%s] shell_state@%s status=0x%08lx cycles=%lu seen=%lu emitted=%lu svalid=%lu sready=%lu\r\n",
               case_name,
               phase,
               (unsigned long)viterbi_reg_read(VITERBI_REG_STATUS),
               (unsigned long)viterbi_reg_read(VITERBI_REG_CYCLE_COUNT),
               (unsigned long)viterbi_reg_read(VITERBI_REG_DEBUG_SEEN),
               (unsigned long)viterbi_reg_read(VITERBI_REG_DEBUG_EMITTED),
               (unsigned long)viterbi_reg_read(VITERBI_REG_DEBUG_SVALID),
               (unsigned long)viterbi_reg_read(VITERBI_REG_DEBUG_SREADY));
}

static void viterbi_dma_recover(const char *case_name) {
    XAxiDma_Reset(&g_axi_dma);
    while (!XAxiDma_ResetIsDone(&g_axi_dma)) {
    }
    viterbi_dump_dma_state(case_name, "after_reset");
}

static int viterbi_wait_dma_idle(const char *case_name) {
    XTime start = 0;
    XTime now = 0;

    XTime_GetTime(&start);
    while (XAxiDma_Busy(&g_axi_dma, XAXIDMA_DMA_TO_DEVICE) ||
           XAxiDma_Busy(&g_axi_dma, XAXIDMA_DEVICE_TO_DMA)) {
        XTime_GetTime(&now);
        if ((now - start) > VITERBI_DMA_TIMEOUT_TICKS) {
            xil_printf("[%s] DMA timeout\r\n", case_name);
            viterbi_dump_dma_state(case_name, "timeout");
            viterbi_dump_shell_state(case_name, "timeout");
            viterbi_dma_recover(case_name);
            return XST_FAILURE;
        }
    }

    return XST_SUCCESS;
}

static int viterbi_wait_core_done(const char *case_name) {
    XTime start = 0;
    XTime now = 0;
    uint32_t status;

    XTime_GetTime(&start);
    while (1) {
        status = viterbi_reg_read(VITERBI_REG_STATUS);
        if ((status & VITERBI_STATUS_DONE_MASK) != 0U) {
            if ((status & VITERBI_STATUS_ERROR_MASK) != 0U) {
                xil_printf("[%s] core reported error status=0x%08lx\r\n",
                           case_name,
                           (unsigned long)status);
                viterbi_dump_shell_state(case_name, "core_error");
                return XST_FAILURE;
            }
            return XST_SUCCESS;
        }

        XTime_GetTime(&now);
        if ((now - start) > VITERBI_CORE_TIMEOUT_TICKS) {
            xil_printf("[%s] core done timeout status=0x%08lx\r\n",
                       case_name,
                       (unsigned long)status);
            viterbi_dump_shell_state(case_name, "core_timeout");
            return XST_FAILURE;
        }
    }
}

static void viterbi_soft_reset(void) {
    viterbi_reg_write(VITERBI_REG_CONTROL, VITERBI_CTRL_SOFT_RESET_MASK);
    viterbi_reg_write(VITERBI_REG_CONTROL, 0U);
}

static int viterbi_run_case(const viterbi_vector_case_t *tc) {
    uint32_t idx;
    uint32_t mismatches = 0;
    uint32_t first_mismatch = 0xffffffffU;
    uint32_t input_byte_len = tc->input_length * sizeof(int16_t);
    uint32_t output_byte_len = tc->output_length * sizeof(int16_t);

    xil_printf("stage=%s:case_begin input_len=%lu output_len=%lu run_id=%s\r\n",
               tc->name,
               (unsigned long)tc->input_length,
               (unsigned long)tc->output_length,
               tc->run_id);

    for (idx = 0; idx < tc->input_length; ++idx) {
        g_tx_buffer[idx] = tc->input[idx];
    }
    for (idx = 0; idx < tc->output_length; ++idx) {
        g_rx_buffer[idx] = 0;
    }

    viterbi_soft_reset();
    viterbi_reg_write(VITERBI_REG_SAMPLE_COUNT, tc->input_length);
    viterbi_reg_write(VITERBI_REG_MISMATCH_COUNT, 0U);
    viterbi_reg_write(VITERBI_REG_CONTROL, VITERBI_CTRL_START_MASK);

    if (XAxiDma_SimpleTransfer(&g_axi_dma, (UINTPTR)g_rx_buffer, output_byte_len, XAXIDMA_DEVICE_TO_DMA) != XST_SUCCESS) {
        xil_printf("[%s] S2MM start failed\r\n", tc->name);
        viterbi_dump_dma_state(tc->name, "s2mm_start_failed");
        viterbi_dump_shell_state(tc->name, "s2mm_start_failed");
        viterbi_dma_recover(tc->name);
        return XST_FAILURE;
    }
    if (XAxiDma_SimpleTransfer(&g_axi_dma, (UINTPTR)g_tx_buffer, input_byte_len, XAXIDMA_DMA_TO_DEVICE) != XST_SUCCESS) {
        xil_printf("[%s] MM2S start failed\r\n", tc->name);
        viterbi_dump_dma_state(tc->name, "mm2s_start_failed");
        viterbi_dump_shell_state(tc->name, "mm2s_start_failed");
        viterbi_dma_recover(tc->name);
        return XST_FAILURE;
    }
    viterbi_dump_dma_state(tc->name, "after_start");
    viterbi_dump_shell_state(tc->name, "after_start");

    if (viterbi_wait_dma_idle(tc->name) != XST_SUCCESS) {
        return XST_FAILURE;
    }
    if (viterbi_wait_core_done(tc->name) != XST_SUCCESS) {
        return XST_FAILURE;
    }

    for (idx = 0; idx < tc->output_length; ++idx) {
        if (g_rx_buffer[idx] != tc->golden[idx]) {
            if (first_mismatch == 0xffffffffU) {
                first_mismatch = idx;
            }
            ++mismatches;
        }
    }

    viterbi_reg_write(VITERBI_REG_MISMATCH_COUNT, mismatches);
    if (mismatches != 0U) {
        xil_printf("[%s] first_mismatch index=%lu expected=%d observed=%d\r\n",
                   tc->name,
                   (unsigned long)first_mismatch,
                   (int)tc->golden[first_mismatch],
                   (int)g_rx_buffer[first_mismatch]);
    }

    xil_printf("[%s] len=%lu cycles=%lu mismatches=%lu status=0x%08lx\r\n",
               tc->name,
               (unsigned long)tc->output_length,
               (unsigned long)viterbi_reg_read(VITERBI_REG_CYCLE_COUNT),
               (unsigned long)mismatches,
               (unsigned long)viterbi_reg_read(VITERBI_REG_STATUS));

    return (mismatches == 0U) ? XST_SUCCESS : XST_FAILURE;
}

int main(void) {
    uint32_t idx;
    uint32_t arch_id;
    int failures = 0;

    xil_printf("ZU4EV Viterbi bare-metal harness\r\n");
    xil_printf("stage=platform_init_begin\r\n");
    viterbi_platform_init();
    xil_printf("stage=platform_init_done\r\n");

    xil_printf("stage=dma_init_begin\r\n");
    if (viterbi_dma_init() != XST_SUCCESS) {
        xil_printf("Completed 0 cases, failures=1\r\n");
        return XST_FAILURE;
    }
    xil_printf("stage=dma_init_done\r\n");

    arch_id = viterbi_reg_read(VITERBI_REG_ARCH_ID);
    xil_printf("Console=%s, arch_id=%lu\r\n", VITERBI_UART_CONSOLE, (unsigned long)arch_id);
    if (arch_id != VITERBI_EXPECTED_ARCH_ID) {
        xil_printf("Unexpected arch_id=%lu expected=%lu\r\n",
                   (unsigned long)arch_id,
                   (unsigned long)VITERBI_EXPECTED_ARCH_ID);
        xil_printf("Completed 0 cases, failures=1\r\n");
        return XST_FAILURE;
    }

    for (idx = 0; idx < g_viterbi_vector_case_count; ++idx) {
        if (viterbi_run_case(&g_viterbi_vector_cases[idx]) != XST_SUCCESS) {
            ++failures;
        }
    }

    xil_printf("Completed %lu cases, failures=%d\r\n",
               (unsigned long)g_viterbi_vector_case_count,
               failures);
    return (failures == 0) ? XST_SUCCESS : XST_FAILURE;
}
