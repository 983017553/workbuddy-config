---
name: a-share-limitboard-report
description: >
  每日收盘后自动整理 A 股涨跌停全景：连板梯队、主线题材、炸板统计与全量明细， 输出自包含 HTML 日报。适用：涨停复盘、连板天梯、炸板率分析、跌停扫描。

agent_created: true
version: 1.0.1
display_name: "A股涨跌停日报"
display_name_en: "A-Share Limit Board Report"
description_zh: "A股涨跌停日报，收盘后汇总涨停/跌停、连板梯队、板型分布、主线板块、炸板与全量列表。"
description_en: "A-share limit-up/down daily report with consecutive board ladder and theme sectors."
visibility: "public"
---

# 涨跌停复盘日报生成

## 能力说明

交易日收盘后，采集全市场涨跌停数据，经清洗归类后生成一份**自包含 HTML** 复盘日报，直接写入文件。

> **输出规范**：Agent 读取 `references/limitboard_report_template.html` 后直接写文件，对话中仅返回摘要与文件路径。配色与排版遵循 wb-finance 研报约束（浅底深字、结论前置、红涨绿跌），采用模板的朱红盘面风格突出涨停/炸板关键数字。

## 何时使用本技能

- 交易日下午 15:30 后，触发生成当日涨跌停复盘
- 需要连板梯队梳理、主线板块识别、炸板率统计、跌停一览

## 运行要求与外部依赖

| 依赖项 | 作用 |
|--------|------|
| `westock-tool` | 涨停/跌停排行榜查询（连板天数、封单量） |
| `westock-data` | 涨跌统计、个股行情、板块排行与成份 |
| `neodata-financial-search` | 涨停原因/题材/炸板补充信息（按需启用） |
| `wb-finance-skill` | HTML 研报格式与合规规范 |

## 数据获取：指令集

```bash
# 涨停排行（支持 --offset 翻页）
westock-tool ranking limitup_days --limit 200
westock-tool ranking limitup_seal_volume --limit 200

# 跌停排行
westock-tool ranking limitdn_days --limit 200
westock-tool ranking limitdn_seal_volume --limit 200

# 全市场涨跌汇总校验
westock-data market-overview --type updown
westock-data changedist

# 个股行情（每批 10–20 只）
westock-data quote <code1>,<code2>,...

# 板块归类：方式一
westock-data sector ranking
westock-data sector constituent <板块代码>

# 题材/原因：方式二（neodata skill 目录下）
python3 scripts/query.py --query "今日A股涨停板汇总，各股票涨停原因和所属板块题材"
python3 scripts/query.py --query "今日A股炸板股票明细，包括炸板股票代码、名称、开板次数、最终涨幅"
```

## 数据整理与口径定义

- 按代码去重；`limitup_days` 与 `limitup_seal_volume` 以代码为键合并
- 板型分类：首板 / 2连 / 3连 / 4连 / 5板+
- **炸板判定（两项条件缺一不可）**：
  1. 当日盘中曾触及涨停价位（或涨幅一度达到涨停幅度）；**且**
  2. 收盘未封涨停（`price` ≠ `price_ceiling`，或收盘涨幅未达涨停幅度）
  - 「盘中开板后回封」且收盘仍封板 → **归入涨停，不计入炸板**
  - 仅凭收盘价无法确认时，以 neodata 炸板明细做交叉校验
- **数据校验规则**：汇总卡片涨停数 = 全量涨停表行数；炸板数 = 炸板表行数；各板型档位之和 = 涨停总数；涨停/跌停总数与 `market-overview --type updown` 交叉比对，不一致时在报告中注明差异
- 主线板块：按题材聚合后取涨停数量 Top 8

## 报告生成：按模板填充

依照 `references/limitboard_report_template.html` 结构逐段填入：

1. Header 区 + `.tldr` 结论摘要（当日市场定性 + 涨停/炸板/跌停要点）
2. 统计卡片行（涨停、炸板、封板率、连板数、跌停）
3. 连板龙头明细（≥2 板）
4. 板型分布汇总
5. 主线板块 Top 8
6. 炸板个股明细
7. 跌停个股一览
8. 全量涨停股明细
9. 免责声明

**不含**龙虎榜内容。文件命名：`limitboard_report_YYYYMMDD_HHmm.html`。

## 使用须知

- 非交易日不生成报告（或明确提示休市）
- **本技能仅负责出报告**；定时调度由外部系统控制，不在技能内配置 crontab
- neodata 若返回 `TOKEN_EXPIRED` / `TOKEN_MISSING`，按其 SKILL.md 中的鉴权流程处理
- 报告脚注使用中性措辞「综合行情与资讯」，不写明具体数据源品牌

## 合规要求

- 金融场景下**先加载** `wb-finance-skill` 合规红线，再执行数据采集
- 报告末尾固定声明：「以上基于公开行情整理，仅供复盘参考，不构成投资建议。」

## 文件索引

| 用途 | 路径 |
|------|------|
| HTML 模板 | `references/limitboard_report_template.html` |
| HTML 风格规范 | `wb-finance-skill/references/html-report-style.md` |
