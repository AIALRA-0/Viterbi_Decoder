# WORKLOG

## Run YYYYMMDD-HHMMSS

### Goal

### Command

### Input

### Output

### Result

### Failure

### Next

## Bootstrap 2026-05-02T05:46:19

### Goal
Create initial Viterbi project skeleton from startup pack.

### Result
PASS: skeleton created. Fill config/local.env before running tools.

## M0 2026-05-02T06:23:12-04:00

### Plan
Initialize the Viterbi decoder project skeleton, fill local machine configuration, verify the startup package, and create the first reproducible git milestone.

### Edit
Filled `config/local.env` with the resolved local project root, FIR reference repository, board document root, GitHub SSH URL, Vivado settings path, Vitis settings path, serial port, board name, FPGA part, and disabled board/flash execution flags. Added `config/env.example` so the repository has a safe committed template. Updated `scripts/sanity_check_environment.py` so M0 checks `GITHUB_URL`, `VIVADO_SETTINGS`, and `VITIS_SETTINGS`.

### Run
`python scripts\sanity_check_environment.py --env config\local.env`

`python ..\scripts\package_self_check.py`

`git init`

`git remote add origin git@github.com:<your-github-owner>/Viterbi_Decoder.git`

`git status --short --ignored`

### Verify
PASS: required M0 directories exist, `spec/viterbi_spec.json` parses as JSON, startup pack self-check passed, local env sanity check passed, GitHub remote is configured, and `config/local.env` is ignored by git. The sanity check reported a pandas ABI warning and warned that Vivado/xsct are not currently in PATH; this is acceptable for M0 because the Vivado/Vitis settings files exist and are recorded.

### Record
M0 result recorded in `WORKLOG.md`, `DECISIONS.md`, and `EXPERIMENTS.yaml`.

### Commit
Pending at record time.

### Result
PASS: M0 gate satisfied.

## M1 2026-05-02T06:27:04-04:00

### Plan
Implement a spec-driven Python convolutional encoder, trellis generator, hard/soft golden Viterbi decoder, channel model, and pytest coverage. Use K=3 only as the spec-defined smoke test and K=7 as the formal design target.

### Edit
Added `model/trellis.py`, `model/conv_encoder.py`, `model/channel.py`, `model/viterbi_golden.py`, and `model/__init__.py`. Added `tests/conftest.py` to emit `data/model/model_unit_test_summary.json`. Added `tests/test_model.py` with K=3 smoke, K=7 no-noise, zero-tail, and single encoded-bit error checks. Added a `smoke_test` section to `spec/viterbi_spec.json` so all code parameters still come from spec.

### Run
`python -m pytest tests -q`

### Verify
PASS: 5 pytest cases passed. K=3 smoke no-noise mismatch count was 0. K=7 formal no-noise mismatch count was 0. No first mismatch was observed.

### Record
Model unit test summary written to `data/model/model_unit_test_summary.json`.

### Commit
Pending at record time.

### Result
PASS: M1 gate satisfied.

## M2 2026-05-02T06:30:33-04:00

### Plan
Generate the required vector cases from `spec/viterbi_spec.json`: no_noise, all_zero, impulse_one, single_bit_error, burst_error_short, random_hard, and soft_awgn at 0/1/2 dB. Each case must include metadata, input bits, encoded bits, hard received bits, soft3 received symbols, and golden decoded bits.

### Edit
Added `vector_generation` cases to `spec/viterbi_spec.json`. Added `scripts/gen_vectors.py` with one-value-per-line hex output, metadata generation, summary CSV output, and post-generation file verification.

### Run
First run:

`python scripts\gen_vectors.py --spec spec\viterbi_spec.json --out vectors`

Result: FAIL because Python started from `scripts/` and could not import `model`.

Fix: Added the project root to `sys.path` inside `scripts/gen_vectors.py`.

Second run:

`python scripts\gen_vectors.py --spec spec\viterbi_spec.json --out vectors`

Regression:

`python -m pytest tests -q`

### Verify
PASS: 9 vector cases generated. Each case contains `metadata.json`, `input_bits.hex`, `encoded_bits.hex`, `rx_hard.hex`, `rx_soft3.hex`, and `golden_decoded.hex`. `vectors/summary.csv` and `data/model/vector_summary.csv` were generated. Total mismatch count was 0 and first mismatch was null for every case. M1 pytest still passed with 5 tests.

### Record
M2 generation result recorded in `WORKLOG.md`, `DECISIONS.md`, and `EXPERIMENTS.yaml`.

### Commit
Pending at record time.

### Result
PASS: M2 gate satisfied after fixing the script import path.

## M3 2026-05-02T06:41:31-04:00

### Plan
Implement the hard-decision RTL baseline with a spec-generated package and verify it against M2 vectors using xsim. Required M3 cases: no_noise, all_zero, impulse_one, and single_bit_error.

### Edit
Added `scripts/gen_rtl_pkg.py` to generate `rtl/common/viterbi_pkg.sv` from `spec/viterbi_spec.json`. Added hard-decision RTL modules under `rtl/viterbi_core`: `bmu_hard.sv`, `acs_unit.sv`, `acs_array.sv`, `path_metric_bank.sv`, `survivor_ram.sv`, `traceback_engine.sv`, and `viterbi_decoder_core.sv`. Added `tb/tb_viterbi_core.sv` and `scripts/run_rtl_regression.py`. Updated `.gitignore` for simulator caches and generated runtime case selection.

### Run
Initial `python scripts\run_rtl_regression.py --env config\local.env --cases no_noise all_zero impulse_one single_bit_error` attempts exposed and fixed four execution issues: Windows Vivado settings quoting, SystemVerilog `bit` keyword used as a loop variable, missing package timescale, and xsim plusarg parsing. The final run was:

`python scripts\run_rtl_regression.py --env config\local.env --cases no_noise all_zero impulse_one single_bit_error`

Regression:

`python -m pytest tests -q`

### Verify
PASS: xsim compiled and elaborated the RTL. no_noise, all_zero, impulse_one, and single_bit_error all passed with mismatch count 0 and no first mismatch. Python model pytest still passed with 5 tests.

### Record
RTL summary written to `data/regression/rtl_regression_summary.csv`.

### Commit
Pending at record time.

### Result
PASS: M3 gate satisfied.

## M4 2026-05-02T06:47:01-04:00

### Plan
Add the 3-bit soft-decision hero path with finite-width path metrics and subtract-min normalization. Update Python golden behavior and verify soft AWGN cases against RTL output.

### Edit
Extended `model/viterbi_golden.py` with `path_metric_width` and `normalization` options. Added a finite-width subtract-min pytest. Extended `scripts/gen_rtl_pkg.py` to emit soft-width and hero metric constants plus `branch_metric_soft3`. Added `bmu_soft3.sv`, `path_metric_normalizer.sv`, `viterbi_decoder_core_soft3.sv`, `tb_viterbi_soft3.sv`, and `scripts/run_soft3_regression.py`.

### Run
`python -m pytest tests -q`

`python scripts\run_soft3_regression.py --env config\local.env --cases soft_awgn_0db soft_awgn_1db soft_awgn_2db`

`python scripts\run_rtl_regression.py --env config\local.env --cases no_noise all_zero impulse_one single_bit_error`

### Verify
PASS: pytest passed 6 tests. soft_awgn_0db, soft_awgn_1db, and soft_awgn_2db all passed soft3 xsim with mismatch count 0. Prior hard RTL regression still passed all 4 required M3 cases with mismatch count 0.

### Record
Soft3 RTL summary written to `data/regression/soft3_regression_summary.csv`.

### Commit
Pending at record time.

### Result
PASS: M4 gate satisfied.

## M5 2026-05-02T06:50:45-04:00

### Plan
Run the required parameter sweep over traceback depth 16/32/40/64, path metric width 8/10/12/16, and normalization none/subtract_min. Use real Python golden decoding with finite traceback behavior and generated M2 vectors.

### Edit
Extended `model/viterbi_golden.py` with finite traceback-depth decision behavior. Added `scripts/run_sweeps.py` to produce sweep CSV data and plots. Updated the soft3 finite-width pytest to exercise traceback depth 16.

### Run
`python -m pytest tests -q`

`python scripts\run_sweeps.py --spec spec\viterbi_spec.json --vectors vectors --out data\analysis\sweep_results.csv`

### Verify
PASS: pytest passed 6 tests. Sweep generated 288 rows and two plots: `docs/assets/plots/m5_soft3_mismatch_vs_traceback.png` and `docs/assets/plots/m5_soft3_subtract_min_heatmap.png`. Total mismatch count was 64. The nonzero mismatches all came from `soft_awgn_0db` at traceback depth 16; each affected metric-width/normalization combination had mismatch count 8 and first mismatch 3.

### Record
Sweep CSV written to `data/analysis/sweep_results.csv`; plots written to `docs/assets/plots/`.

### Commit
Pending at record time.

### Result
PASS: M5 gate satisfied.

## M6 2026-05-02T07:05:59-04:00

### Plan
Run Vivado synthesis for the hard baseline and soft3 hero, then run Vivado implementation for the selected soft3 hero. Parse utilization, timing, and power into a summary CSV. Record timing failure honestly if it occurs.

### Edit
Added `vivado/tcl/run_synth.tcl`, `vivado/tcl/run_impl.tcl`, and `scripts/run_vivado_reports.py`. Updated `.gitignore` to keep generated DCP checkpoints out of git. Added `data/impl/timing_analysis.md`.

### Run
`python scripts\run_vivado_reports.py --env config\local.env`

Parser fix after run:

The first summary parsed utilization and power but left WNS/TNS blank. I inspected `timing_summary.rpt`, fixed `parse_timing`, and re-parsed existing Vivado reports without rerunning implementation.

### Verify
PASS: baseline synthesis, hero synthesis, and hero implementation all completed with Vivado return code 0. `data/impl/vivado_summary.csv` contains utilization, WNS, TNS, and power. Timing is not met for the hero: routed WNS -20.433 ns and TNS -16272.939 ns. The critical setup path is from `compute_idx_reg[4]/C` to `metrics_reg[47][10]/D`, with 30.415 ns data path delay and 116 logic levels.

### Record
Vivado summary written to `data/impl/vivado_summary.csv`; critical path analysis written to `data/impl/timing_analysis.md`.

### Commit
Pending at record time.

### Result
PASS: M6 data-collection gate satisfied. Timing failure is recorded as a design limitation, not hidden.

## M7 2026-05-02T08:36:08-04:00

### Plan
Build the ZU4EV PS+DMA+PL board shell for the soft3 Viterbi decoder, create a Vitis bare-metal DMA test app, program by JTAG, and capture UART PASS/FAIL logs for `no_noise`, `single_bit_error`, and `soft_awgn_2db`.

### Edit
Added `rtl/system/viterbi_axis_wrapper.sv`, `rtl/system/viterbi_control_regs.v`, and `rtl/system/viterbi_zu4ev_shell.v`. Added `vivado/tcl/zu4ev/build_viterbi_system.tcl`. Added Vitis sources under `vitis/zu4ev_baremetal/`, generated `viterbi_vectors.c/h`, and added build/program/capture orchestration scripts. Fixed the board address map by including `SEG_ps_0_HPC0_LPS_OCM` for the DMA MM2S and S2MM address spaces.

### Run
`E:\Xilinx\Vivado\2024.1\bin\vivado.bat -mode batch -source vivado\tcl\zu4ev\build_viterbi_system.tcl`

`powershell -NoProfile -ExecutionPolicy Bypass -File scripts\build_zu4ev_app.ps1 -XsaPath %VITERBI_STAGE%\viterbi_zu4ev_shell.xsa -Arch hero_soft3 -StageRoot %VITERBI_STAGE%\viterbi_zu4ev`

`python scripts\run_board_validation.py --skip-build --build-info %VITERBI_STAGE%\viterbi_zu4ev\hero_soft3\artifacts\build_info.json --port COM9 --baud 115200 --capture-timeout 180`

`python -m pytest tests -q`

### Verify
PASS: Latest board run `m7_board_20260502_083547` captured `Completed 3 cases, failures=0`. `no_noise`, `single_bit_error`, and `soft_awgn_2db` each returned length 96, mismatch count 0, and status `0x00000001`. The board shell saw 204 input samples and emitted 96 output samples for each case. Vivado board implementation at 25 MHz completed with WNS 6.495 ns and TNS 0. Python pytest passed 6 tests.

### Debug notes
First board attempt with DDR buffers timed out before any stream input reached the core. Second attempt with OCM buffers reached 109 samples, then AXI DMA reported a decode error because the Vivado address map still excluded `SEG_ps_0_HPC0_LPS_OCM`. After matching the FIR reference shell and explicitly including the OCM segment, the third attempt passed all required cases.

### Record
Board summary written to `data/board_runs/board_summary.csv`. UART evidence written under `data/board_runs/m7_board_20260502_083547/`. Prior failed runs are retained in `data/board_runs/` as debug evidence.

### Commit
Pending at record time.

### Result
PASS: M7 board-validation gate satisfied with real UART evidence and no non-volatile memory programming.

## M8 2026-05-02T08:48:50-04:00

### Plan
Generate the final Chinese report from the real M0-M7 evidence, include required CSV-backed figures and tables, generate `Report.md` and `Report.pdf`, run the final checklist, and commit only after verification passes.

### Edit
Added `scripts/build_final_report.py`. The script reads committed model, sweep, Vivado, and board data; derives the required report CSVs without inventing data; and generates deterministic plot images.

### Run
`python scripts\build_final_report.py`

`python -m pytest tests -q`

`python -c "from pypdf import PdfReader; ..."`

`rg` artifact and forbidden-keyword scan over `Report.md`

### Verify
PASS: report build completed. Artifact and forbidden-keyword scan returned no matches. Pytest passed 6 tests. Visual preview rendered text, tables, and plots correctly.

### Record
Final report artifacts written to `Report.md`, `Report.pdf`, `docs/assets/plots/`, and `data/analysis/`.

### Commit
Pending at record time.

### Result
PASS: M8 final-report gate satisfied with a reproducible report generator, real source data, explicit limitations, and AI tool statement.
