# Final Review

## Requirement compliance table

| Requirement | Status | Evidence |
| --- | --- | --- |
| README.md can orient the reader | PASS | README.md exists and M0-M7 structure is recorded |
| Report.md complete | PASS | 17 required chapters generated |
| Report.pdf opens | PASS | Generated from Report.md by scripts/build_final_report.py |
| spec/viterbi_spec.json is source of truth | PASS | M0-M7 scripts consume spec or derived package |
| model/vectors/rtl/tb/vivado/vitis/scripts complete | PASS | M1-M7 commits cover all required directories |
| data contains raw results | PASS | data/model, data/regression, data/analysis, data/impl, data/board_runs |
| docs/assets contains plots/diagram sources | PASS | docs/assets/diagrams and docs/assets/plots |
| WORKLOG/DECISIONS/EXPERIMENTS traceable | PASS | M0-M8 entries recorded |
| No private board docs committed | PASS | .gitignore excludes board_docs/private_docs |
| No non-volatile memory programming | PASS | M7 used JTAG temporary download only |

## Evidence table

| Evidence | Path or value |
| --- | --- |
| Latest M7 board run | m7_board_20260502_083547 |
| Board UART log | C:\Users\AIALRA-PORTABLE\Desktop\Vertebi\viterbi_startup_pack\src\data\board_runs\m7_board_20260502_083547\uart.log |
| Vivado summary | data/impl/vivado_summary.csv |
| Sweep summary | data/analysis/sweep_results.csv |
| Final report | Report.md and Report.pdf |

## Tests executed

- `python -m pytest tests -q` -> 6 passed.
- `python scripts\run_board_validation.py --skip-build --build-info C:\codex_stage\viterbi_zu4ev\hero_soft3\artifacts\build_info.json --port COM9 --baud 115200 --capture-timeout 180` -> PASS for 3 board cases.
- PDF text extraction and render preview performed in M8.

## Known limitations

- M6 hero implementation does not meet 100 MHz timing; routed WNS is -20.433 ns.
- M8 `ber_summary.csv` is a finite-vector mismatch-rate summary, not a statistically large BER campaign.
- Board validation uses OCM buffers; larger future vectors need DDR DMA debug or a larger staging design.

## Submission readiness

READY
