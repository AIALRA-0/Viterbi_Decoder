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

`git remote add origin git@github.com:AIALRA-0/Viterbi_Decoder.git`

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
