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
dash/metrics/seed.yaml       # 指标口径库：32 条 / 8 个面板 / 32747 字节 / 932 行
docs/metric-dictionary.md    # 口径说明文档（Markdown，按面板分节，29723 字节；每条含分子/分母/过滤/粒度/维度/来源表/虚构演算）
docs/VERIFICATION.md         # 验证报告：校验命令逐字输出 + 四条 AC 逐条对照
tools/build_seed.py          # 生成器：由内嵌定义表生成 seed.yaml 与字典文档（幂等可复跑）
tools/validate_metrics.py    # 格式校验脚本（13 项结构校验）
tools/validate_metrics.out   # 校验脚本的原始输出文件（16 行）
tools/negative_test.py       # 反证脚本：改坏一条定义后校验应变为 FAIL
tools/negative_summary.txt   # 反证结果快照
```

## 三、依赖与运行环境

- 需要：Python 3.11+ 与 PyYAML。
- 不需要：Node、数据库、后端服务、任何 API 密钥、任何网络。全部为静态 YAML 结构与算术校验。
- 不引入向境外发送数据的第三方 SDK。

```bash
python --version                      # 预期：Python 3.11.x
python -m pip install pyyaml          # 唯一第三方依赖
python -c "import yaml;print(yaml.__version__)"   # 预期：6.x
python tools/validate_metrics.py      # 预期：13 行 [PASS] + SUMMARY + RESULT
echo EXIT=$?                          # 预期：EXIT=0
```

## 四、实测输出（`python tools/validate_metrics.py`，退出码 0，16 行）

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
[PASS] 12-example-math-recompute    复算 9 条比率型演算全部对得上（另 23 条为计数/中位数型，不适用复算）
[PASS] 13-definition-alignment      北极星/出租率/SOP/采纳率/签约额 定义与需求原文用词一致

[SUMMARY] metrics=32 panels=8 ratio_examples_recomputed=9 non_ratio_examples=23
[RESULT] PASS 13/13 checks · 32 条口径 · 8 个面板 · 每面板 >= 2 条
```

任何人克隆同一份仓库、对同一份 `dash/metrics/seed.yaml` 复跑，结果与 `tools/validate_metrics.out` 逐字一致。

## 五、验收标准对照

| AC | 要求 | 产物 | 证据 |
| --- | --- | --- | --- |
| 1 | 条目数 >= 30，8 面板每面板 >= 2 | `dash/metrics/seed.yaml` | 校验 4/5/6 项：32 条，最少面板 3 条 |
| 2 | 每条有分子、分母（或计算方式）、过滤条件与虚构演算示例 | `dash/metrics/seed.yaml` 每条 14 字段（含 granularity / dimensions / source_tables） | 校验 8-12 项；文档 32 小节逐条展开 |
| 3 | seed.yaml 通过口径库格式校验（命令输出附在 PR） | `tools/validate_metrics.py` + `tools/validate_metrics.out` + 本文件第四节 + PR #1 | 脚本、被校验文件、原始输出同处本仓库同一分支 |
| 4 | 北极星有效连接与出租率定义与需求文字一致 | `docs/metric-dictionary.md` 通用约定 | 校验 13 项关键词比对 |

## 六、关键定义（与需求原文一致）

- **北极星 · 有效连接数**：双方都在系统里确认愿意洽谈，同一对企业就同一条需求 90 天内只计一次。
- **出租率**：已租工位 / 可租工位，共享空间不计入。
- **签约额**：合同首年金额，多年合同按年拆分。
- **SOP 执行率**：按时完成的待办 / 全部到期待办。
- **匹配采纳率**：采纳的推荐 / 推荐总数。

## 七、反证测试（证明校验脚本不是空转）

```bash
python tools/negative_test.py    # 把 IR-03 定义里的「首年」改成「年度」后重跑校验
# 预期：[FAIL] 13-definition-alignment …… IR-03 …… [RESULT] FAIL 1/13，退出码 1
```

校验脚本确实会因定义偏离需求而失败；原 `seed.yaml` 不受影响，重跑仍为 PASS 13/13。
