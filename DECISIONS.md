# DECISIONS

# Decision D-001: Use K=7 [171,133] as default formal target

## Context
K=7 [171,133] 是经典卷积码配置，状态数 64，足够体现 VLSI 架构复杂度。

## Options
K=3 toy design, K=5 medium design, K=7 formal design.

## Decision
Use K=7 [171,133] as the formal target, and optionally use K=3 only for debug smoke tests.

## Reason
K=7 有足够复杂度，适合课程 open-ended project；K=3 只能作为教学和 debug 工具。

## Consequence
RTL 和 traceback 复杂度更高，需要更严格的自动化验证。

# Decision D-002: Keep local machine configuration out of git

## Context
`config/local.env` contains absolute local paths for Vivado, Vitis, the FIR reference repository, and private board documents.

## Options
Commit `config/local.env`, commit only a safe template, or leave configuration undocumented.

## Decision
Keep `config/local.env` ignored by git and commit only `config/env.example`.

## Reason
The project must be reproducible without exposing private local paths or board document locations.

## Consequence
Every machine must create its own `config/local.env` from `config/env.example` before running local or board tools.

# Decision D-003: Do not enable board execution or flash programming in M0

## Context
The master prompt requires JTAG and UART board validation later, but default policy forbids flash writes unless explicitly authorized.

## Options
Enable board execution immediately, keep board execution disabled until M7, or skip board planning.

## Decision
Set `ALLOW_BOARD_RUN=0` and `ALLOW_FLASH_WRITE=0` in `config/local.env`.

## Reason
M0 only verifies paths and tool setup. Real board execution belongs to M7 and flash programming is not authorized.

## Consequence
M7 must explicitly record any board run command and must still avoid flash writes.

# Decision D-004: Use full-sequence Python Viterbi as the M1 golden model

## Context
M1 needs a bit-true reference before RTL work starts. The traceback-depth approximation belongs to later hardware architecture exploration.

## Options
Use a full-sequence dynamic-programming decoder, immediately model finite traceback depth, or rely on handwritten expected vectors.

## Decision
Use a full-sequence dynamic-programming Viterbi decoder as the M1 golden model.

## Reason
It is deterministic, simple to verify for no-noise and small error cases, and provides a stable software reference before introducing hardware traceback constraints.

## Consequence
M5 must add explicit traceback-depth behavior and compare any finite-depth loss against this full-sequence reference.
