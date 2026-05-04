# Resource-Aware Soft-Decision Viterbi Decoder on ZU4EV

This repository contains the ECSE 6680 Advanced VLSI Design open-ended final project.

## Project Summary

The project implements and evaluates a rate-1/2, K=7, [171,133] convolutional-code Viterbi decoder for FPGA validation on a ZU4EV board.

Core research question:

```text
How should hard/soft decision mode, traceback depth, path metric width, normalization, and ACS organization be selected for a practical error-correction and hardware-cost tradeoff on MZU04A-4EV / XCZU4EV?
```

## Directory Layout

```text
spec/        Design specification source of truth
config/      Toolchain and local environment templates
model/       Python golden model
vectors/     Test vectors
tb/          RTL testbenches
rtl/         SystemVerilog / Verilog RTL
vivado/      Vivado build scripts and outputs
vitis/       Board-level bare-metal application
scripts/     Automation scripts
data/        Experiment data
docs/        Figures and report assets
reports/     Review and PDF preview artifacts
```

## Reproduction

```bash
python scripts/sanity_check_environment.py --env config/local.env
python scripts/gen_vectors.py --spec spec/viterbi_spec.json
python scripts/run_rtl_regression.py
python scripts/run_soft3_regression.py
python scripts/run_sweeps.py
python scripts/run_vivado_reports.py
```

Board execution requires MZU04A-4EV, JTAG, and UART access:

```bash
python scripts/run_board_validation.py --skip-build --build-info <build_info.json> --port COM9 --baud 115200 --capture-timeout 180
```

## Reports

Primary deliverables:

- [Report.md](Report.md)
- [Report.pdf](Report.pdf)
