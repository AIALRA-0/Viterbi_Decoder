# Resource-Aware Soft-Decision Viterbi Decoder on ZU4EV

本仓库是 ECSE 6680 Advanced VLSI Design（高级 VLSI 设计课程：研究算法如何高效落到硬件架构的课程）开放式期末项目。

## Project Summary（项目摘要）

本项目实现并评测一个 rate-1/2、K=7、[171,133] convolutional-code Viterbi decoder（卷积码维特比译码器：从带噪声的编码 bit 中恢复最可能原始 bit 的硬件）。

核心研究问题：

```text
如何选择 hard/soft decision、traceback depth、path metric width、normalization 和 ACS organization，才能在 MZU04A-4EV / XCZU4EV 上获得最佳纠错能力与硬件成本折中？
```

## Directory Layout（目录结构）

```text
spec/        设计规格事实源
config/      工具链和本地环境配置
model/       Python 黄金模型
vectors/     测试向量
tb/          RTL 测试平台
rtl/         SystemVerilog / Verilog RTL
vivado/      Vivado 构建脚本和输出
vitis/       板级裸机测试程序
scripts/     自动化脚本
data/        原始实验数据
docs/        图像和资料
reports/     阶段性分析
```

## Reproduction（复现方式）

```bash
python scripts/sanity_check_environment.py --env config/local.env
python scripts/gen_vectors.py --spec spec/viterbi_spec.json
python scripts/run_rtl_regression.py
python scripts/run_vivado_synth.py
python scripts/make_plots.py
```

Board run（板级运行：真实开发板上执行测试）需要 MZU04A-4EV、JTAG 和 UART：

```bash
python scripts/run_board_test.py --env config/local.env --case no_noise
```

## Reports（报告）

请阅读：

```text
Report.md
Report.pdf
```
