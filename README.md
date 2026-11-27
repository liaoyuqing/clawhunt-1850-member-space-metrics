# clawhunt-1850-member-space-metrics

【S3-DASH-002】会员空间平台 · 首批指标口径条目编写（>= 30 条）。本仓库是订单 1850 的完整可运行交付物，**全部为虚构数据**，不含任何真实企业、人名或客户名称。

公开仓库，无需登录即可克隆：`https://github.com/liaoyuqing/clawhunt-1850-member-space-metrics`（PR #1：`/pull/1`，内含校验命令的逐字输出）。

## 一、拿到交付物（克隆）

```bash
git clone https://github.com/liaoyuqing/clawhunt-1850-member-space-metrics.git
cd clawhunt-1850-member-space-metrics
ls -R                     # 预期：README.md dash/ docs/ tools/ 四棵树
```

如果 `git clone` 走不通，可走 GitHub REST 逐文件下载（仓库内容与克隆完全一致）：

```bash
curl -sL https://api.github.com/repos/liaoyuqing/clawhunt-1850-member-space-metrics/git/trees/main?recursive=1
curl -sL "https://api.github.com/repos/liaoyuqing/clawhunt-1850-member-space-metrics/contents/dash/metrics/seed.yaml" | python -c "import sys,json,base64;print(base64.b64decode(json.load(sys.stdin)['content']).decode())"
```

## 二、目录结构

```
README.md                    # 本文件：克隆、依赖、运行与预期输出
dash/metrics/seed.yaml       # 指标口径库：32 条 / 8 个面板 / 32987 字节 / 932 行
docs/metric-dictionary.md    # 口径说明文档（Markdown，按面板分节，29963 字节；每条含分子/分母/过滤/粒度/维度/来源表/虚构演算）
docs/VERIFICATION.md         # 验证报告：校验命令逐字输出 + 四条 AC 逐条对照 + 反证结果
docs/CHECKSUMS.txt           # 全部交付文件的 SHA-256 与字节数
tools/build_seed.py          # 生成器：由内嵌定义表生成 seed.yaml 与字典文档（幂等可复跑）
tools/validate_metrics.py    # 格式校验脚本（13 项结构校验，含逐条算式复算）
tools/validate_metrics.out   # 校验脚本的原始输出文件（16 行）
tools/negative_test.py       # 双反证脚本：改坏定义 / 改错算式，校验应各自变红
tools/negative_summary.txt   # 反证结果快照（两条用例与恢复后的复跑）
tools/negative_def.out       # 反证一（IR-03 定义）的原始输出
tools/negative_math.out      # 反证二（OR-04 算式）的原始输出
```

## 三、依赖与运行环境

- 需要：Python 3.11+ 与 PyYAML。
- 不需要：Node、数据库、后端服务、任何 API 密钥、任何网络。全部为静态 YAML 结构与算术校验。
- 不引入向境外发送数据的第三方 SDK；仓库内无密钥、无账号、无客户名称。

```bash
python --version                      # 预期：Python 3.11.x
python -m pip install pyyaml          # 唯一第三方依赖
python -c "import yaml;print(yaml.__version__)"   # 预期：6.x
python tools/validate_metrics.py      # 预期：13 行 [PASS] + SUMMARY + RESULT
echo EXIT=$?                          # 预期：EXIT=0
```

## 四、实测输出（`python tools/validate_metrics.py`，退出码 0，16 行）

```text
[PASS] 1-yaml-parse[PASS] 1-yaml-parse                 文件 seed.yaml，32987 字节，932 行
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
[PASS] 12-example-math-recompute    复算 32 条示例全部对得上（覆盖全部条目）
[PASS] 13-definition-alignment      北极星/出租率/SOP/采纳率/签约额 定义与需求原文用词一致

[SUMMARY] metrics=32 panels=8 examples_recomputed=32 examples_without_arith=0
[RESULT] PASS 13/13 checks · 32 条口径 · 8 个面板 · 每面板 >= 2 条
```

任何人克隆同一份仓库、对同一份 `dash/metrics/seed.yaml` 复跑，结果与 `tools/validate_metrics.out` 逐字一致。

校验第 12 项做的是**逐条算式复算**：把每条示例的 `calc` 按分号分段、逐段求「算式 = 结果」，再复算 `result` 中的 `A ÷ B = C%`，并核对 `calc` 与 `result` 两边的分子分母是否一致；偏差超过 0.011 记 mismatch。32 条示例**全部**复算通过，包括中位数型（IR-02）的位次算式 `(27+1) ÷ 2 = 14`。

## 五、验收标准对照

| AC | 要求 | 产物 | 证据 |
| --- | --- | --- | --- |
| 1 | 条目数 >= 30，8 面板每面板 >= 2 | `dash/metrics/seed.yaml` | 校验 4/5/6 项：32 条，最少面板 3 条 |
| 2 | 每条有分子、分母（或计算方式）、过滤条件与虚构演算示例 | `dash/metrics/seed.yaml` 每条 14 字段（含 granularity / dimensions / source_tables） | 校验 8-12 项（32 条算式全部复算）；文档 32 小节逐条展开 |
| 3 | seed.yaml 通过口径库格式校验（命令输出附在 PR） | `tools/validate_metrics.py` + `tools/validate_metrics.out` + 本文件第四节 + PR #1 | 脚本、被校验文件、原始输出同处本仓库同一分支 |
| 4 | 北极星有效连接与出租率定义与需求文字一致 | `docs/metric-dictionary.md` 通用约定 | 校验 13 项关键词比对 |

## 六、关键定义（与需求原文一致）

- **北极星 · 有效连接数**：双方都在系统里确认愿意洽谈，同一对企业就同一条需求 90 天内只计一次。
- **出租率**：已租工位 / 可租工位，共享空间不计入。
- **签约额**：合同首年金额，多年合同按年拆分。
- **SOP 执行率**：按时完成的待办 / 全部到期待办。
- **匹配采纳率**：采纳的推荐 / 推荐总数。

## 七、反证测试（证明校验脚本不是空转）

`python tools/negative_test.py` 跑两条反证，各自应让校验变红：

```text
case1case1 定义反证（IR-03「首年」→「年度」）: exit=1 fails=1
  [FAIL] 13-definition-alignment      IR-03 缺「首年」
case2 算式反证（OR-04 分子 14400000→14400001）: exit=1 fails=1
  [FAIL] 12-example-math-recompute    复算 31 条示例全部对得上（覆盖全部条目）；不符: OR-04: 示例算式的分子/分母与结果等式不一致：(14400001.0, 18720000.0) vs (14400000.0, 18720000.0)
restored: exit=0
```

两条反证都验证了脚本会因「定义偏离需求」与「示例算式算错」而失败；原 `seed.yaml` 未被改动，脚本最后会复跑正常文件并返回 EXIT=0。

## 八、字节级核对

`docs/CHECKSUMS.txt` 列出仓库内每个交付文件的 SHA-256 与字节数，可在克隆后本地核对（`python -c` 或 `sha256sum`），用于确认拿到的文件与提交时的文件逐字节一致。