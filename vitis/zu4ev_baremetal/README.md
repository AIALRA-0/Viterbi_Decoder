# ZU4EV bare-metal board app

This folder contains the M7 board-validation app for the Viterbi decoder. It is intended to run from JTAG and UART only. It must not program any non-volatile memory.

Expected flow:

1. Build `vivado/tcl/zu4ev/build_viterbi_system.tcl` to create an XSA with bitstream.
2. Create a Vitis platform from the XSA.
3. Build `src/main.c` as a standalone application.
4. Download bitstream and ELF through JTAG.
5. Capture UART at 115200 baud and write logs under `data/board_runs/`.
