---
name: yingmi-portfolio-diagnosis
description: 当用户提供基金持仓组合（基金代码+持仓金额）并要求生成「基金组合健康诊断」HTML 报告时使用。基于盈米且慢 MCP 实时数据，输出包含组合评分、持仓明细、资产配置、风险体检、行业集中度、相关性预警与优化建议的单页 HTML，涨跌按 A 股红涨绿跌。
agent_created: true
---

# 盈米基金组合健康诊断

## 适用场景

- 用户提供 2 只及以上公募基金的代码与持仓金额，要求诊断组合合理性。
- 用户明确要求「组合健康诊断」「持仓诊断」「基金体检」「优化建议」等。
- 交付物为自包含单页 HTML，使用且慢统一视觉模板。

## 前置条件

1. 安装 `yingmi-skill-cli`（如未安装）：
   ```bash
   npm install -g yingmi-skill-cli@latest --registry=https://registry.npmmirror.com --prefer-online
   ```
2. 初始化并获取 API Key：
   ```bash
   yingmi-skill-cli init status
   yingmi-skill-cli init setup --phone <手机号>
   yingmi-skill-cli init setup --verify-code <验证码>
   ```
3. 如用户未提供每只基金的持仓金额，必须索要；组合诊断工具 `DiagnoseFundPortfolio` 的 `fundList` 必填 `fundCode` 与 `amount`。

## 关于 Windows 下的已知问题

`yingmi-skill-cli remote-skill enter portfolio-doctor` 在 Windows 环境可能因 `trash` 回收站操作失败而无法进入子技能目录。此时**直接调用 MCP 工具**，不依赖 `remote-skill enter`。

## 核心 MCP 工具

| 用途 | 工具 | 说明 |
|---|---|---|
| 组合总览 | `DiagnoseFundPortfolio` | 输入 `fundList`（含 amount），返回资产配置、相关性评分、5 年回测（年化收益/最大回撤/波动率/夏普）。 |
| 个基资料 | `BatchGetFundsDetail` | 输入 `fundCodes` 数组，返回每只基金的类型、风险等级、净值、近 1 年/日涨跌、规模等。 |
| 行业分布 | `getFundIndustryAllocation` | 输入单只基金代码，返回行业占比；仅对权益基金有意义。 |
| 相关性矩阵 | `GetFundsCorrelation` | 输入 `fundList`（含 amount），返回两两相关系数。 |
| 净值历史 | `BatchGetFundNavHistory` | 如需展示净值曲线，可调用获取对齐交易日数据。 |

## 执行流程

1. **确认持仓金额**：若用户只给总市值，向其索要每只基金市值或持有份额（份额需拉净值换算）。
2. **校正基金代码**：基金代码应为 6 位。如遇报错「无法找到基金代码」，用 `SearchFunds` 确认正确代码。
3. **调用组合诊断**：
   ```bash
   yingmi-skill-cli mcp call DiagnoseFundPortfolio --input '{"fundList":[{"fundCode":"...","fundName":"...","amount":...},...]}'
   ```
4. **获取个基数据**：调用 `BatchGetFundsDetail` 补充每只基金的名称、类型、风险、收益率。
5. **获取行业与相关性**：对权益基金调用 `getFundIndustryAllocation`；调用 `GetFundsCorrelation` 获取全矩阵。
6. **数据处理**：
   - 用持仓金额计算每只基金占比。
   - 对权益基金按金额加权计算组合行业集中度。
   - 提取相关系数 ≥0.7 或 ≥0.9 的预警对。
   - 综合雷达评分（资产配置/相关性/回测）换算为 0-100 分。
7. **生成 HTML**：使用 `yingmi-skill/references/demo-report.html` 作为视觉壳，不得自造 CSS/class；保留顶栏、水印、主题切换。
8. **报告必备模块**：
   - 组合评分与 KPI（评分/总市值/累计收益/风险等级）
   - 持仓明细（代码、名称、类型、风险、市值、占比、近 1 年收益率、日涨跌）
   - 资产配置环形图（股/债/货币）
   - 风险体检（波动率、最大回撤、5 年年化、夏普、子维度评分）
   - 行业集中度条形图
   - 相关性预警表格
   - 可执行优化建议（基于数据，不得臆造）
9. **免责声明**：明确标注数据截至日期、收益率为基金表现不代表个人持仓盈亏、不构成投资建议。

## 数据真实性要求

- 所有图表数值必须来自 MCP 返回值或用户输入。
- 不得估算持仓金额、占比、收益率。
- 若某只基金缺少相关性数据（如成立时间较短的 QDII），在报告中说明「未纳入矩阵」。

## 资源

- `references/workflow.md`：详细工具调用示例与常见报错处理。
- `scripts/generate_report_template.py`：数据解析与 HTML 生成的参考脚本。
