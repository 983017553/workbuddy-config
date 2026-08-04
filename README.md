# WorkBuddy 配置与技能同步仓库

本仓库用于**同一账号在多台电脑之间同步 WorkBuddy 的本地配置与技能**。

它把本机 `~/.workbuddy/` 下的用户级技能、专家包、记忆、MCP/连接器配置、身份文件集中备份到这里，换电脑时一键恢复。由 WorkBuddy 的 `workbuddy-config-sync` 技能自动打包生成。

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

## 如何重新生成 / 更新本仓库
在已配置好的电脑上，让 WorkBuddy 运行 `workbuddy-config-sync` 技能，提供一把带 `repo` 权限的 GitHub Personal Access Token，即可把最新配置推送到本仓库。脚本使用 Git Data API（blob 并发 → 单树 → 单提交），幂等且支持中文路径文件名。
