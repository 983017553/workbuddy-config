# 盈米组合诊断工作流参考

## 1. 初始化 CLI

```bash
npm install -g yingmi-skill-cli@latest --registry=https://registry.npmmirror.com --prefer-online
yingmi-skill-cli init status
yingmi-skill-cli init setup --phone <PHONE>
yingmi-skill-cli init setup --verify-code <CODE>
```

## 2. 常用 MCP 工具调用示例

### 账户诊断

```bash
yingmi-skill-cli mcp call DiagnoseFundPortfolio --input '{"fundList":[{"fundCode":"007339","fundName":"易方达沪深300ETF联接C","amount":15094.44},...]}'
```

返回字段：
- `assetAllocation.radarScore`：资产配置评分 1-5
- `assetAllocation.assetClassesDetail`：各资产类别占比
- `correlation.radarScore`：相关性评分 1-5
- `correlation.correlationDetails`：两两相关系数数组
- `backTest.backTestDetail`：5 年年化收益、最大回撤、波动率、夏普

### 个基详情

```bash
yingmi-skill-cli mcp call BatchGetFundsDetail --input '{"fundCodes":["007339","020466","000032"]}'
```

关注 `summary` 下的：
- `fundInvestType`、`risk5Level`
- `nav`、`navDate`
- `dailyReturn`、`oneYearReturn`
- `netAsset`

### 行业配置

```bash
yingmi-skill-cli mcp call getFundIndustryAllocation --input '{"fundCode":"007339"}'
```

返回 `data[0].industryAllocations`。

### 相关性矩阵

```bash
yingmi-skill-cli mcp call GetFundsCorrelation --input '{"fundList":[{"fundCode":"007339","amount":15094.44},...]}'
```

## 3. 常见报错处理

| 报错 | 原因 | 处理 |
|---|---|---|
| `无法找到基金代码 XXXXXXX 的基金信息` | 代码位数不对或不存在 | 用 `SearchFunds` 搜索正确代码 |
| `remote-skill enter ... trash operation` | Windows 回收站操作失败 | 直接调 MCP 工具，不进入子 skill |
| 相关性矩阵缺少某只基金 | 该基金历史太短 | 在报告中标注「未纳入相关性计算」 |

## 4. 报告数据计算

- 单只占比 = `amount / sum(amount)`
- 加权风险等级 = `Σ(风险等级 * amount) / 总市值`
- 组合评分 = `(资产配置评分 + 相关性评分 + 回测评分) / 3 / 5 * 100`
- 行业加权暴露 = `Σ(单只行业占比 * 该只权益金额 / 权益总金额)`
