# 交付验证报告（S3-DASH-002 · 订单 1850）

本文件随 PR 提交，内容是校验脚本的逐字真实输出与验收标准逐条对照。全部虚构数据，无客户名称、真实企业或人名。

## 1 运行环境

| 项 | 值 |
| --- | --- |
| Python | 3.11.9（实测 `python --version`） |
| 第三方依赖 | 仅 PyYAML（`python -m pip install pyyaml`，实测 6.0.4） |
| 不需要 | 数据库 / 后端服务 / 网络 / 任何 API 密钥 |
| 平台 | Windows 10，仓库内路径全部使用 `/`，Linux/macOS 同样可跑 |

## 2 复现步骤

```bash
git clone https://github.com/liaoyuqing/clawhunt-1850-member-space-metrics.git
cd clawhunt-1850-member-space-metrics
python -m pip install pyyaml
python tools/validate_metrics.py; echo EXIT=$?     # 预期 13 项 PASS，EXIT=0
python tools/negative_test.py;  echo EXIT=$?     # 反证：两条各 FAIL 1 项，EXIT=1，恢复后 EXIT=0
```

## 3 `python tools/validate_metrics.py` 逐字输出（退出码 0，16 行）

```text
[PASS] 1-yaml-parse                 文件 seed.yaml，32747 字节，932 行
[PASS] 2-top-level-fields           schema_version=1.0 library=member-space-metrics
[PASS] 3-panel-set                  8 个面板: member_scale,profile_completeness,sop_execution,opportunity_funnel,miniapp_activity,ai_adoption,investment_revenue,occupancy_renewal
[PASS] 4-metric-count>=30           实际 32 条
[PASS] 5-per-panel>=2               最少面板 profile_completeness=3 条；分布 member_scale:5 profile_completeness:3 sop_execution:4 opportunity_funnel:5 miniapp_activity:4 ai_adoption:3 investment_revenue:4 occupancy_renewal:4
[PASS] 6-panel-count-consistent     面板声明计数与条目实际数一致
[PASS] 7-id-unique-and-prefixed     32 个 id 唯一
[PASS] 8-required-text              缺 0 项
[PASS] 9-formula-complete           分子/分母/计算方式齐全
[PASS] 10-filters-dims-sources      过滤条件/维度/来源表非空
[PASS] 11-example-has-numbers       全部 32 条示例含虚拟数字
[PASS] 12-example-math-recompute    复算 31 条示例全部对得上；另 1 条为无算式型
[PASS] 13-definition-alignment      北极星/出租率/SOP/采纳率/签约额 定义与需求原文用词一致

[SUMMARY] metrics=32 panels=8 examples_recomputed=31 examples_without_arith=1
[RESULT] PASS 13/13 checks · 32 条口径 · 8 个面板 · 每面板 >= 2 条
```

## 4 验收标准逐条对照

| AC | 原文要求 | 实际产物 | 证据 |
| --- | --- | --- | --- |
| 1 | 条目数 >= 30，且 8 个面板每个至少有 2 条 | 32 条；面板 5/3/4/5/4/3/4/4，最少 3 条 | 校验项 4、5、6（见上） |
| 2 | 每条都有分子、分母（或计算方式）、过滤条件与虚构演算示例 | `dash/metrics/seed.yaml` 每条 14 字段，`formula.numerator/denominator/expression` + `filters[]` + `granularity` + `dimensions[]` + `source_tables[]` + `example.{given,calc,result}` | 校验项 8–12（31 条算式逐条复算） |
| 3 | seed.yaml 通过口径库格式校验（命令输出附在 PR） | `tools/validate_metrics.py` 13 项校验 | 本文件第 3 节逐字输出 + `tools/validate_metrics.out` + PR #1 描述 |
| 4 | 北极星有效连接与出租率的定义与本单文字一致 | OF-03 / OR-01 定义原文一致 | 校验项 13 关键词比对 + `docs/metric-dictionary.md` 通用约定 |

## 5 反证测试（证明校验不是空转）

`tools/negative_test.py` 跑两条反证，各自写入临时文件后重跑校验，两条都必须变红：

```text
case1 定义反证（IR-03「首年」→「年度」）: exit=1 fails=1
  [FAIL] 13-definition-alignment      IR-03 缺「首年」
case2 算式反证（OR-04 分子 14400000→14400001）: exit=1 fails=1
  [FAIL] 12-example-math-recompute    复算 30 条示例全部对得上；另 1 条为无算式型；不符: OR-04: 示例算式的分子/分母与结果等式不一致：(14400001.0, 18720000.0) vs (14400000.0, 18720000.0)
restored: exit=0
```

原始 `seed.yaml` 未被改动，脚本最后一步复跑正常文件仍为 PASS 13/13、EXIT=0。原始输出见 `tools/negative_def.out` 与 `tools/negative_math.out`。

## 6 字节级核对

`docs/CHECKSUMS.txt` 列出全部交付文件的 SHA-256 与字节数，可在克隆后本地核对，确认文件与提交时逐字节一致。
