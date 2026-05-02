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
