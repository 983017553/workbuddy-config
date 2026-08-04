# WorkBuddy 配置与技能备份 — 恢复指南

本仓库由 WorkBuddy 自动打包，用于**同一账号在多台电脑间同步配置与技能**。

## 包含内容
- `skills/` —— 你安装的全部用户级技能
- `experts/` —— 专家包
- `memory/` —— 项目记忆日志
- `mcp.json` / `.mcp.json` —— MCP / 连接器配置
- `SOUL.md` / `IDENTITY.md` / `USER.md` / `MEMORY.md` —— 身份与长期记忆

## 刻意排除（请勿手动补回）
- `settings.json` —— 含企业微信机器人 `botToken` 等明文密钥，且为设备相关配置
- `__pycache__/*.pyc` —— Python 编译缓存，可自动再生
- `binaries/`、`cache/`、`logs/`、`sessions/`、`blobs/`、`plugins/`、`app/` 等运行时/缓存目录

## 在另一台 Windows 电脑上恢复
1. 安装并登录 WorkBuddy，先打开一次让它生成 `C:\Users\<你的用户名>\.workbuddy\` 目录。
2. 把本仓库的内容 clone 或下载下来。
3. 将仓库里的 `skills/`、`experts/`、`memory/`、`mcp.json`、`.mcp.json`、`SOUL.md`、`IDENTITY.md`、`USER.md`、`MEMORY.md` **覆盖复制**到 `C:\Users\<你的用户名>\.workbuddy\` 对应位置。
4. 重启 WorkBuddy。

## 恢复后需手动处理
- 在「连接器」页重新连接并信任各连接器（baidu-netdisk、lexiang、tdx 等），因为 `settings.json` 未同步。
- 若技能脚本依赖外部 API Key（如 IMA），按各技能说明填入对应配置文件（通常在 `~/.config/` 下，不在此仓库内）。
- 自动化任务（`workbuddy.db` 中的本地任务）不随本仓库同步；如需迁移，请用 `automation_update` 接口导出/导入 JSON。
