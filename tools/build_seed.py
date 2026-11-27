# -*- coding: utf-8 -*-
"""构建 dash/metrics/seed.yaml 与 docs/metric-dictionary.md。

仅使用虚构数据，无外部依赖（需要 PyYAML 写 YAML）。本脚本是一次性生成器，
产物即交付物；校验由 tools/validate_metrics.py 独立完成。
"""
import pathlib
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]

PANELS = [
    ("member_scale", "会员规模与状态", "会员企业的规模、认证状态、入会与流失，按统计日快照口径。"),
    ("profile_completeness", "资料完整度", "会员企业关键字段与能力卡（可提供资源/需求资源）的填写质量与新鲜度。"),
    ("sop_execution", "SOP 执行", "SOP 工作台到期待办的按时完成、超时、跳过与单步耗时。"),
    ("opportunity_funnel", "商机漏斗", "需求发布、推荐采纳、双向确认的有效连接（北极星）到成交的漏斗。"),
    ("miniapp_activity", "小程序活跃", "微信小程序会员端的认证覆盖、月活、资源大厅转化与活动到场。"),
    ("ai_adoption", "AI 采纳率", "AI 辅助工具的草稿采纳、人工修改幅度与转人工比例。"),
    ("investment_revenue", "招商与营收", "招商线索转化、签约周期与首年签约额。"),
    ("occupancy_renewal", "出租率与续约率", "工位出租率（共享空间不计入）、续约率与租金口径。"),
]

# 字段：id|panel|name|definition|numerator|denominator|expression|filters|granularity|dimensions|source_tables|given|calc|result
RAW = """
MS-01|member_scale|认证会员企业数|统计日处于认证有效状态（cert_status=certified 且 cert_expired_at 晚于统计日）的会员企业数量；代表可对外背书的会员规模|count(distinct org_id)，条件见过滤|1（计数型指标，分母固定为 1）|分子 ÷ 1，取整数（单位：家）|仅会员企业且 is_test=false；deleted_at is null；cert_status=certified；cert_expired_at > 统计日；同一企业多主体只保留主主体|日（快照）|site、member_tier、industry、city|dwd_member_enterprise、dim_org、dim_site|统计日 2026-04-30 有 120 家非测试会员企业，其中 97 家曾通过认证，5 家认证已过期|97 - 5 = 92|92 家
MS-02|member_scale|有效会员企业数|会员期覆盖统计日、未被冻结、且未标记流失的会员企业数；是绝大多数比率型指标的分母基数|count(distinct org_id)，条件见过滤|1（计数型指标，分母固定为 1）|分子 ÷ 1，取整数（单位：家）|is_test=false；deleted_at is null；member_start_at <= 统计日 <= member_end_at + 30 天宽限期；status != churned；status != frozen|日（快照）|site、member_tier、industry、city|dwd_member_enterprise、dim_org|120 家非测试会员企业中，冻结 5 家、会员期超过 30 天宽限仍未续 12 家、测试数据 3 家|120 - 5 - 12 - 3 = 100|100 家
MS-03|member_scale|新增入会数|统计期内首次签约入会的会员企业数，按首次合同生效日归属期间，撤销签约的剔除|count(distinct org_id) where first_signed_at in 统计期，且该合同 status=signed|1（计数型指标，分母固定为 1）|分子 ÷ 1，取整数（单位：家）|is_test=false；deleted_at is null；first_signed_at 落在统计期；合同 status=signed；签约后 3 日内撤单退款的不计；同一企业只计首次|月|site、channel、industry、sales_owner|dwd_member_enterprise、dwd_contract|2026 年 4 月有 7 家企业首次签约，其中 1 家在 3 日内撤单退款|7 - 1 = 6|6 家
MS-04|member_scale|流失数|会员期到期后 90 天内未续签、状态转为 churned 的会员企业数|count(distinct org_id) where status=churned and churn_at in 统计期|1（计数型指标，分母固定为 1）|分子 ÷ 1，取整数（单位：家）|is_test=false；deleted_at is null；churn_at 落在统计期；因场地调整换场且在新场地续签的不计流失；主动注销且退还全部费用的不计|月|site、member_tier、industry、churn_reason|dwd_member_enterprise、dwd_contract|2026 年 4 月会员期满 15 家，其中 9 家已续签、2 家仍在续约流程、4 家转入 churned|15 - 9 - 2 = 4|4 家
MS-05|member_scale|生命周期状态分布|统计日各生命周期状态的企业数占全部会员企业的比例，用于看结构而不看总量|各状态 count(distinct org_id)（onboarding/active/at_risk/frozen/churned）|统计日全部非测试会员企业数|单状态企业数 ÷ 全部会员企业数 × 100%（单位：%）|is_test=false；deleted_at is null；状态取统计日快照；同一企业只归一个状态（优先 churned > frozen > at_risk）|日（快照）|site、member_tier、lifecycle_status|dwd_member_enterprise、dim_date|统计日非测试会员企业 120 家：onboarding 9、active 71、at_risk 18、frozen 5、churned 17|9 + 71 + 18 + 5 + 17 = 120；active 占比 71 ÷ 120|71 ÷ 120 = 59.17%，五状态合计 100%
PF-01|profile_completeness|关键字段完整度|12 个关键字段在有效会员企业中的填写并通过格式校验的比例，衡量资料底座可用性|已填且通过格式校验的关键字段个数之和（每企业最多 12）|有效会员企业数 × 12|分子 ÷ 分母 × 100%（单位：%）|is_test=false；deleted_at is null；企业取自有效会员企业口径（MS-02）；12 个字段：企业名称、统一社会信用代码、行业、规模、城市、联系人、联系电话、主营产品、能力标签、合作诉求、LOGO、官网；空串与纯空格视为未填；统一社会信用代码校验位不通过视为未填|月|site、member_tier、industry、field_key|dwd_member_profile_field、dwd_member_enterprise|100 家有效会员企业，应填字段 1200 个，已填且校验通过 963 个|963 ÷ 1200|963 ÷ 1200 = 80.25%
PF-02|profile_completeness|能力卡完成率|能力卡已发布且 6 段必填内容全部非空的企业占有效会员企业的比例|能力卡 status=published 且六段必填全非空的企业数|有效会员企业数|分子 ÷ 分母 × 100%（单位：%）|is_test=false；deleted_at is null；能力卡 deleted_at is null；status=published；六段必填：可提供资源、需求资源、成功案例、报价区间、可服务区域、联系人；任一段为空或仅空白则不计|月|site、member_tier、industry、资源大类|dwd_capability_card、dwd_member_enterprise|100 家有效会员企业中，68 家能力卡已发布且六段必填全非空|68 ÷ 100|68.00%
PF-03|profile_completeness|能力卡新鲜度|已发布能力卡中最近 180 天内更新过的比例，防止能力卡长期失真|last_updated_at >= 统计日 - 180 天的已发布能力卡数|已发布能力卡数（status=published 且 deleted_at is null）|分子 ÷ 分母 × 100%（单位：%）|is_test=false；deleted_at is null；status=published；以 last_updated_at 为准，不看 created_at；内容仅为系统批量迁移写入的不计更新|月|site、industry、资源大类|dwd_capability_card|68 张已发布能力卡中，41 张在近 180 天内被人工更新|41 ÷ 68|41 ÷ 68 = 60.29%
SOP-01|sop_execution|SOP 执行率|按时完成的待办 ÷ 全部到期待办：到期待办中在到期时间前完成的比例，按待办条数计，不按步骤模板计|status=done 且 completed_at <= due_at 的到期待办数|全部到期待办数（due_at <= 统计日，排除 status=cancelled）|分子 ÷ 分母 × 100%（单位：%）|is_test=false；deleted_at is null；due_at <= 统计日；status != cancelled；因模板下线批量作废的不入分母（cancel_reason=template_retired）；同一待办多实例按 instance 计数|月|site、sop_template、owner_dept|dwd_sop_task、dim_sop_template|2026 年 4 月到期 420 条，其中 20 条因模板下线作废，按时完成 344 条|420 - 20 = 400；344 ÷ 400|344 ÷ 400 = 86.00%
SOP-02|sop_execution|SOP 超时率|到期待办中逾期完成或逾期未完成的比例，与执行率互补但不等于 1 减执行率（含作废剔除口径）|逾期完成数（completed_at > due_at）+ 逾期未完成数（未完成且 due_at < 统计日）|全部到期待办数（同 SOP-01 分母）|分子 ÷ 分母 × 100%（单位：%）|is_test=false；deleted_at is null；due_at <= 统计日；status 不为 cancelled；超时以系统 due_at 为准，不以人工改期后的时间为准|月|site、sop_template、owner_dept|dwd_sop_task|同上 400 条到期待办：40 条逾期完成、16 条超期仍未完成|40 + 16 = 56；56 ÷ 400|56 ÷ 400 = 14.00%
SOP-03|sop_execution|SOP 跳过率|到期待办中被人工标记跳过的比例，跳过必须填写原因|status=skipped 的到期待办数|全部到期待办数（同 SOP-01 分母）|分子 ÷ 分母 × 100%（单位：%）|is_test=false；deleted_at is null；due_at <= 统计日；status=skipped；skip_reason 为空的不计（视为未完成）；由系统自动跳过（如前置条件不满足）的单独打标 auto_skip，不入本指标|月|site、sop_template、skip_reason_code|dwd_sop_task|400 条到期待办中 9 条被人工跳过且填了原因|9 ÷ 400|9 ÷ 400 = 2.25%
SOP-04|sop_execution|平均步骤耗时|已完成待办从开始到完成的平均耗时，用于识别流程卡点|Σ（completed_at - started_at）折算小时|已完成且有 started_at 的待办数|分子 ÷ 分母（单位：小时）|is_test=false；deleted_at is null；status=done；started_at 与 completed_at 均非空；跨天待办按自然小时计，不扣非工作时段；超过 30 天的挂起实例剔除|月|site、sop_template、step_no|dwd_sop_task、dws_sop_step_duration|320 条待办有完整起止时间，耗时合计 1248 小时|1248 ÷ 320|1248 ÷ 320 = 3.90 小时/条
OF-01|opportunity_funnel|需求发布数|统计期内通过审核并正式发布到资源大厅的需求数|status 由 draft 变为 published 且 review_status=approved 的需求数|1（计数型指标，分母固定为 1）|分子 ÷ 1，取整数（单位：条）|is_test=false；deleted_at is null；published_at 落在统计期；review_status=approved；审核驳回仍在草稿的不计；发布后删除的不计|月|site、industry、demand_type、需求大类|dwd_demand|2026 年 4 月提交 96 条需求，4 条审核驳回、2 条发布后删除|96 - 4 - 2 = 90|90 条
OF-02|opportunity_funnel|匹配采纳率|已到反馈窗口的推荐中被人采纳的比例，衡量匹配质量而非推送量|recommendation 中 adopted_at 非空（企业点击采纳并生成跟进记录）的条数|当期推送且已满 7 天反馈窗口的推荐条数|分子 ÷ 分母 × 100%（单位：%）|is_test=false；deleted_at is null；pushed_at <= 统计日 - 7 天；同一推荐重复推送按最新一条计；系统自动采纳（api 直连）单独打标，不入分子|月|site、industry、match_rule_version|dwd_match_recommendation|统计期内累计推送 1200 条，其中 50 条推送不满 7 天窗口不计，已满窗口 1150 条中采纳 391 条、未采纳 759 条（391 + 759 = 1150）|391 采纳 ÷ 1150 已满窗口（= 391 + 759）|391 ÷ 1150 = 34.00%
OF-03|opportunity_funnel|有效连接数（北极星）|双方都在系统里确认愿意洽谈的配对数量：需求方 confirm 与资源方 confirm 均非空；同一对企业就同一需求 90 天内只计一次|去重后的有效连接数（按 企业对 + 需求 在 90 天窗口内取首次）|1（计数型指标，分母固定为 1）|分子 ÷ 1，取整数（单位：条）|is_test=false；deleted_at is null；demand_confirm_at 非空且 supply_confirm_at 非空；仅一方确认的不计；系统代确认（运营代点）打标 manual_assist 不计；去重键 = min(org_a,org_b) + max(org_a,org_b) + demand_id，窗口 90 天|月|site、industry、demand_type、连接来源|dwd_connection、dwd_demand|2026 年 4 月产生 58 条双方确认记录，其中 7 条与 90 天内既有连接属同企业同需求|58 - 7 = 51|51 条（北极星）
OF-04|opportunity_funnel|商机转化率|有效连接在统计期内转为成交的比例，成交以合同首签日落在期内为准|期内由有效连接转为 status=won 的商机数|期内新增有效连接数（OF-03 分子）|分子 ÷ 分母 × 100%（单位：%）|is_test=false；deleted_at is null；won_at 落在统计期；合同 status=signed；同一连接多次成交只计首次；退单（7 日内全额退款）不计|月|site、industry、sales_owner|dwd_connection、dwd_contract|期内 51 条有效连接中 9 条在期内成交|9 ÷ 51|9 ÷ 51 = 17.65%
OF-05|opportunity_funnel|需求首次响应时长中位数|需求发布到首次有效响应的小时数中位数，抗极端值|按响应时长升序排列后取中位样本的时长|1（中位数口径，分母为中位样本本身）|median(responded_at - published_at)，单位小时|is_test=false；deleted_at is null；published_at 落在统计期；有效响应 = 资源方首次提交洽谈意向或明确文字回复，系统自动问候不计；样本 n 为偶数时取中间两位均值|月|site、industry、demand_type|dwd_demand、dwd_demand_response|期内 90 条需求中 78 条有有效响应，升序第 39、40 位为 6.2 与 6.8 小时|(6.2 + 6.8) ÷ 2|6.50 小时
MA-01|miniapp_activity|认证覆盖率|有效会员企业中完成小程序账号绑定并通过企业实名审核的比例|小程序端绑定企业且实名审核通过的企业数|有效会员企业数（MS-02）|分子 ÷ 分母 × 100%（单位：%）|is_test=false；deleted_at is null；绑定关系 status=approved；同一企业多账号只计一次；仅关注公众号未绑定小程序的不计|月|site、member_tier、industry|dwd_miniapp_account、dwd_member_enterprise|100 家有效会员企业中 79 家完成小程序绑定并实名通过|79 ÷ 100|79.00%
MA-02|miniapp_activity|月活跃会员企业占比|自然月内在小程序产生至少一次有效会话事件的企业占比，有效事件排除小程序启动与后台心跳|当月有有效事件（页面浏览/搜索/收藏/洽谈/报名）的企业数|期初有效会员企业数|分子 ÷ 分母 × 100%（单位：%）|is_test=false；deleted_at is null；事件时间落在自然月；按 enterprise_id 去重（同一企业多账号算 1）；启动、心跳、推送到达不算有效事件；内部测试账号排除|月|site、member_tier、industry|dwd_miniapp_event、dwd_member_enterprise|4 月期初 100 家，其中 64 家产生有效会话事件|64 ÷ 100|64.00%
MA-03|miniapp_activity|资源大厅转化率|浏览资源大厅后 7 天内发起洽谈、收藏或预约看场的企业占比|浏览后 7 天内产生转化动作（洽谈/收藏/预约）的企业数|当期浏览过资源大厅的企业数|分子 ÷ 分母 × 100%（单位：%）|is_test=false；deleted_at is null；浏览事件 view 去重到企业；转化动作时间 - 首次浏览时间 <= 7 天；运营推送跳转带来的浏览单独打标 channel=push，保留在分母|月|site、industry、资源大类、channel|dwd_miniapp_event、dwd_demand|当期 180 家企业浏览资源大厅，其中 45 家在 7 天内产生转化动作|45 ÷ 180|45 ÷ 180 = 25.00%
MA-04|miniapp_activity|活动报名到场率|活动报名成功者中现场核销签到的比例|签到核销人数|报名成功人数|分子 ÷ 分母 × 100%（单位：%）|is_test=false；deleted_at is null；活动 end_at 落在统计期；报名 status=confirmed；重复报名按人去重；工作人员与嘉宾名单不计|场（按活动聚合，月度再汇总）|site、activity_type、活动场次|dwd_activity_signup、dwd_activity_checkin|4 月 3 场活动报名成功 260 人，现场签到 187 人|187 ÷ 260|187 ÷ 260 = 71.92%
AI-01|ai_adoption|草稿采纳率|AI 生成的草稿被人采纳（直接使用或轻微编辑后保存）的比例，衡量 AI 输出可用性|采纳草稿数（result=adopted，含 edit_then_adopt）|AI 草稿生成成功数（排除生成失败与超时）|分子 ÷ 分母 × 100%（单位：%）|is_test=false；deleted_at is null；generated_at 落在统计期；result 字段为 adopted 或 edit_then_adopt；生成失败/超时/被限流的不入分母；同一次生成只计一条|月|site、ai_scenario、model_version|dwd_ai_draft|4 月生成 800 次，失败 12 次，采纳 498 条|800 - 12 = 788；498 ÷ 788|498 ÷ 788 = 63.20%
AI-02|ai_adoption|修改幅度|采纳草稿被人工改动的字符占比均值，越小说明草稿越贴近可用|Σ 编辑距离（草稿原文 → 人工保存稿）|Σ 采纳草稿的字符数|分子 ÷ 分母 × 100%（单位：%）|is_test=false；deleted_at is null；只统计 adopted / edit_then_adopt；纯格式调整（空白、标点全半角）折算 0；草稿字符数按去空白后计|月|site、ai_scenario、model_version|dwd_ai_draft|498 条采纳草稿去空白后共 41200 字符，编辑距离合计 9880|9880 ÷ 41200|9880 ÷ 41200 = 23.98%
AI-03|ai_adoption|升级人工率|AI 会话中因低置信度、意图识别失败或用户主动要求而转人工的比例|转人工会话数（handoff_at 非空，按 session_id 去重）|AI 会话总数（按 session_id 去重）|分子 ÷ 分母 × 100%（单位：%）|is_test=false；deleted_at is null；session_start_at 落在统计期；handoff_at 非空；同一会话多次转人工只计 1；系统兜底提示不计转人工|月|site、ai_scenario、handoff_reason|dwd_ai_session|4 月 AI 会话 600 个，其中 87 个发生转人工|87 ÷ 600|87 ÷ 600 = 14.50%
IR-01|investment_revenue|线索转化率|已分配给业务员的招商线索中最终签约的比例|期内由线索转签约的合同数（合同 lead_id 命中线索）|期内新增且已分配业务员的线索数（剔除无效重复）|分子 ÷ 分母 × 100%（单位：%）|is_test=false；deleted_at is null；lead_created_at 落在统计期；assigned_at 非空；invalid_reason 非空（空号、重复、非目标行业）的不入分母；同一线索多次签约只计首次|月|site、channel、sales_owner、行业|dwd_sales_lead、dwd_contract|4 月新增线索 240 条，剔除无效 18 条，签约 27 单|240 - 18 = 222；27 ÷ 222|27 ÷ 222 = 12.16%
IR-02|investment_revenue|签约周期中位天数|线索创建到合同签署的自然日中位数，评估招商链路效率|按周期天数升序排列后取中位样本的天数|1（中位数口径，分母为中位样本本身）|median(signed_at - lead_created_at)，单位自然日|is_test=false；deleted_at is null；signed_at 落在统计期；同一线索多份合同取首份；退单不计；自然日含周末与节假日|月|site、channel、sales_owner|dwd_sales_lead、dwd_contract|4 月 27 单签约，周期天数升序第 14 位为 41 天|第 14 位样本（n=27，中位位次 (27+1)÷2 = 14）|41 天
IR-03|investment_revenue|签约额（首年）|统计期内签署合同的签约额合计，签约额 = 合同首年金额；多年合同按年拆分，本指标只取首年，不重复计入后续年度|Σ 合同首年金额（分）|1（金额型指标，分母固定为 1）|分子 ÷ 1，单位分；报表按 元 = 分 ÷ 100 展示|is_test=false；deleted_at is null；signed_at 落在统计期；合同 status=signed；多年合同按合同年度拆分，本指标只取第 1 年；退单（7 日内全额退款）冲减；押金、物业费不计入签约额|月|site、channel、sales_owner、合同年限|dwd_contract、dim_contract_term|4 月 27 单签约，首年金额合计 186400000 分|186400000 ÷ 100|186400000 分 = 1864000.00 元
IR-04|investment_revenue|业务员人均签约单数|期内签约合同数除以在职招商业务员数，用于产能对比而非考核排名|期内签约合同数（status=signed）|期内月末在职招商业务员数（role=sales 且在职日期覆盖月末）|分子 ÷ 分母（单位：单/人）|is_test=false；deleted_at is null；合同 signed_at 落在统计期；业务员按月末在职口径，月中离职按在职天数折算 0.5 人；兼职与外包不计|月|site、sales_owner、团队|dwd_contract、dim_sales_staff|4 月签约 27 单，月末在职招商业务员 6 人|27 ÷ 6|27 ÷ 6 = 4.50 单/人
OR-01|occupancy_renewal|出租率|已租工位占可租工位的比例；共享空间（shared_area=true）的工位不计入分子分母|期末已租工位数（租约 status=active 且覆盖统计日）|期末可租工位数（工位 status in available/rented，排除共享空间、维修中、自用）|分子 ÷ 分母 × 100%（单位：%）|is_test=false；deleted_at is null；统计日为期末快照；shared_area=true 的工位整体剔除；维修中（maintenance）与自用（internal）不计可租；同一工位多租约只计一条有效|日（快照）/月汇总|site、floor、工位类型、共享/独立|dwd_workstation、dwd_lease、dim_site|4 月末总工位 580 个，其中共享空间 60 个；已租 437 个|可租 = 580 - 60 = 520；437 ÷ 520|437 ÷ 520 = 84.04%
OR-02|occupancy_renewal|续约率|期内到期租约中已续签的工位占比，按工位计而非按合同计|到期后已续签的工位数（新租约 start_date 在原到期日或其后 7 天内）|期内到期的租约工位数（排除因场地调整换场且已在新场地签约的）|分子 ÷ 分母 × 100%（单位：%）|is_test=false；deleted_at is null；原租约 end_at 落在统计期；续签判定以新租约 start_date <= 原 end_at + 7 天为准；换场（site_changed=true）不计入分母；同一工位多次续签只计一次|月|site、floor、工位类型、租户行业|dwd_lease、dwd_workstation|4 月到期 52 个工位租约，其中 4 个因场地调整换场，续签 36 个|52 - 4 = 48；36 ÷ 48|36 ÷ 48 = 75.00%
OR-03|occupancy_renewal|平均出租单价|已租工位的月租金均值，只计租金不含物业费与押金|Σ 有效租约月租金（分）|期末已租工位数（OR-01 分子）|分子 ÷ 分母 ÷ 100（单位：元/工位/月）|is_test=false；deleted_at is null；租约 status=active 且覆盖统计日；免租期（rent_free）按实际应收折算；物业费、水电、押金不计；折扣按合同实收金额计|月|site、floor、工位类型|dwd_lease、dwd_workstation|437 个已租工位月租金合计 174800000 分|174800000 ÷ 437 ÷ 100|4000.00 元/工位/月
OR-04|occupancy_renewal|续约金额留存率|续签租约金额相对到期租约原金额的留存比例，衡量续约质量|续签租约首年月租金合计（分）|到期租约原月租金合计（分，剔除换场）|分子 ÷ 分母 × 100%（单位：%）|is_test=false；deleted_at is null；分母与 OR-02 同口径（剔除换场）；续签租金按新合同实收计，不含免租期；降租与增租都按实收，不做平滑|月|site、租户行业、租约年限|dwd_lease|到期 48 个工位原月租合计 18720000 分；续签 36 个工位新月租合计 14400000 分|14400000 ÷ 18720000|14400000 ÷ 18720000 = 76.92%
"""

FIELDS = ["id", "panel", "name", "definition", "numerator", "denominator",
          "expression", "filters", "granularity", "dimensions", "source_tables",
          "given", "calc", "result"]


def parse_metrics():
    out = []
    for line in RAW.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != len(FIELDS):
            raise SystemExit("bad field count %d in %s" % (len(parts), parts[0]))
        rec = dict(zip(FIELDS, parts))
        rec["filters"] = [x for x in rec["filters"].split("；") if x]
        rec["dimensions"] = [x for x in rec["dimensions"].split("、") if x]
        rec["source_tables"] = [x for x in rec["source_tables"].split("、") if x]
        rec["example"] = {
            "given": rec.pop("given"),
            "calc": rec.pop("calc"),
            "result": rec.pop("result"),
        }
        rec["formula"] = {
            "numerator": rec.pop("numerator"),
            "denominator": rec.pop("denominator"),
            "expression": rec.pop("expression"),
        }
        rec["unit_note"] = "金额单位：分；比率单位：%；时长单位见计算方式"
        out.append(rec)
    return out


def build_seed(metrics):
    doc = {
        "schema_version": "1.0",
        "library": "member-space-metrics",
        "owner": "S3-DASH-002",
        "data_policy": "全部为虚构数据；不含真实企业与人名；不出现客户名称",
        "timezone": "Asia/Shanghai",
        "currency_unit": "fen",
        "panels": [{"key": k, "name": n, "description": d,
                    "metric_count": sum(1 for m in metrics if m["panel"] == k)}
                   for k, n, d in PANELS],
        "metrics": metrics,
    }
    text = yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=120)
    head = "# 会员空间平台 · 指标口径库 seed（S3-DASH-002）\n"
    head += "# 由 tools/build_seed.py 生成；校验命令：python tools/validate_metrics.py\n"
    path = ROOT / "dash" / "metrics" / "seed.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(head + text, encoding="utf-8", newline="\n")
    return path, doc


def build_doc(doc):
    m = doc["metrics"]
    L = []
    L.append("# 会员空间平台 · 指标口径说明（S3-DASH-002 首批 %d 条）" % len(m))
    L.append("")
    L.append("版本 1.0 · 依据 S1-BP 业务蓝图指标口径编写 · 覆盖管理驾驶舱 8 个面板 · 全部演算使用虚构数据，不含真实企业与人名，不出现客户名称。")
    L.append("")
    L.append("## 通用约定")
    L.append("")
    L.append("1. 金额一律以「分」存整数，文档示例为便于阅读同时给出元（元 = 分 ÷ 100）。")
    L.append("2. 所有业务表均含 `id`、`org_id`、`site_id`、`created_at`、`created_by`、`updated_at`、`deleted_at`，除特别说明外一律按 `deleted_at is null` 过滤软删除。")
    L.append("3. 统计日 = 报表跑批日（Asia/Shanghai 00:00 快照）；比率类指标保留两位小数，分子分母均为去重后的整数。")
    L.append("4. 虚构测试数据统一打标 `is_test=false` 才进入统计；本单所有示例数字均为 mock，不对应任何真实企业。")
    L.append("5. 北极星「有效连接数」：双方都在系统里确认愿意洽谈，同一对企业就同一条需求 90 天内只计一次。")
    L.append("6. 出租率：已租工位 ÷ 可租工位，共享空间不计入。")
    L.append("7. 签约额 = 合同首年金额，多年合同按年拆分。SOP 执行率 = 按时完成的待办 ÷ 全部到期待办。匹配采纳率 = 采纳的推荐 ÷ 推荐总数。")
    L.append("")
    n = 0
    for key, name, desc in PANELS:
        n += 1
        rows = [x for x in m if x["panel"] == key]
        L.append("## %d. %s（%s，%d 条）" % (n, name, key, len(rows)))
        L.append("")
        L.append(desc)
        L.append("")
        for x in rows:
            f = x["formula"]
            e = x["example"]
            L.append("### %s %s" % (x["id"], x["name"]))
            L.append("")
            L.append("- **定义**：%s" % x["definition"])
            L.append("- **分子**：%s" % f["numerator"])
            L.append("- **分母**：%s" % f["denominator"])
            L.append("- **计算方式**：%s" % f["expression"])
            L.append("- **过滤条件**：%s" % "；".join(x["filters"]))
            L.append("- **粒度**：%s" % x["granularity"])
            L.append("- **维度**：%s" % "、".join(x["dimensions"]))
            L.append("- **数据来源表**：%s" % "、".join(x["source_tables"]))
            L.append("- **演算示例（虚构）**：%s；%s；**结果 %s**" % (e["given"], e["calc"], e["result"]))
            L.append("")
    L.append("## 附：校验方式")
    L.append("")
    L.append("`python tools/validate_metrics.py` 读取 `dash/metrics/seed.yaml`，校验 9 项结构与口径规则（YAML 可解析、8 面板齐全、条目数 ≥ 30、每面板 ≥ 2、字段齐全、公式三段非空、过滤条件非空、维度与来源表非空、示例含数字），通过打印 `[RESULT] PASS` 并退出码 0，失败打印缺陷清单并退出码 1。")
    L.append("")
    text = "\n".join(L)
    path = ROOT / "docs" / "metric-dictionary.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path, len(text)


def main():
    metrics = parse_metrics()
    sp, doc = build_seed(metrics)
    dp, chars = build_doc(doc)
    print("seed:", sp)
    print("doc :", dp, "chars=", chars)
    print("metrics=%d panels=%d" % (len(doc["metrics"]), len(doc["panels"])))
    for p in doc["panels"]:
        print("  %-22s %s" % (p["key"], p["metric_count"]))


if __name__ == "__main__":
    main()