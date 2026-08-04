# 跨会话备忘

## WorkBuddy 本机环境注意（重要）
- Bash 工具运行在沙箱镜像中：绝对路径 `/c/Users/...` 会被翻译成 `D:\c\Users`（镜像层），而 WorkBuddy 真实运行环境只读真实 `C:\Users`。因此通过 Bash 的 `pip install` / `python -m venv` 安装的依赖**无法进入真实环境**，WorkBuddy 启动的 MCP server 找不到它们。
- Write / Read / Edit 工具操作的是真实 `C:\Users` 文件系统。
- 结论：本机自建 MCP server 优先用**纯标准库**实现（urllib 手写 stdio JSON-RPC），避免依赖安装。若必须装第三方依赖，需写入真实路径（Write 工具无法直接跑 pip，需另想办法）。
- `python -m venv` 在本托管 Python 上返回 0 却零文件（venv 模块损坏），不可用；基础托管 Python 自带可用 pip（26.x）。

## 软件安装位置偏好
- 用户偏好将软件默认安装到 `D:\ProgramData`（手动指定方式，不动系统注册表/设置，最安全）。
- 该目录已存在且真实可用（内含 baidu、ima、Quark、Seewo、WorkBuddy 等程序文件夹）。

## IMA OpenAPI 写通道能力矩阵（2026-07-16 实测，api.md 未文档化，跨项目复用）
- 凭证：`~/.config/ima/{client_id,api_key}`（用户个人密钥，我拿不到，须用户从 ima.qq.com/agent-interface 生成后提供）。桥接脚本 `~/.workbuddy/skills/ima-skills/ima_api.cjs`（透传任意 openapi/wiki/v1/* path）+ `cos-upload.cjs`。写用 OpenAPI 侧 KB_ID（形如 `AFi0-...=`），与 ima-mcp 内部 ID（`0019...`）是同一库两套编码，folder_id 两通道通用。
- ✅ 可用：`create_folder`（⚠父目录参数是 `folder_id` 不是 `parent_folder_id`，传错静默建到 KB 根）、`add_knowledge`（带 folder_id 直投）、`rename_knowledge`（带 `media_id`）、create_media/check_repeated_names/get_knowledge_list/get_media_info/search_knowledge。
- ❌ `move_knowledge`：返回 code:0 success 但 move_results 恒空、文件不移动（no-op，别用）。
- ❌ `delete_knowledge`/delete_*/remove_*：全部 404，**OpenAPI 无删除端点，ima-mcp 也无 delete**。误传/残留只能用户在 IMA App 手动删；程序侧只能用 rename_knowledge 打「请删除」标记提示。
- ⚠陷阱：ima_api.cjs 对 404 返回空 body+退出码 0、move no-op 返回 code:0，都会被误判"成功"。删/移操作必须操作后回查 get_knowledge_list 的 parent_folder_id/current_path 确认。

## MCP 配置位置
- 用户自定义 server 写在 `~/.workbuddy/mcp.json`（key: mcpServers，stdio 用 command+args+env）。
- 实际生效的聚合配置是 `~/.workbuddy/.mcp.json`（含 connector-proxy：ima/lexiang/tdx）。自定义 server 两个文件都加更稳妥。
- 改完 mcp.json 后，需在 WorkBuddy 连接器页 → 自定义连接器 → 点 "Trust" 启用，不会自动生效。

## 课件设计规范（锁定，跨项目权威标准 · 2026-07-25 最终确认）
- 由导学案一键生成课堂教学 PPT 的**完整工作流与规范**见用户级技能 `courseware-pptx`（SKILL.md + scripts/gen_courseware.py，已闭环验证）。
- 锁定值：版式 16:9；配色 蓝 `#4F81BD` / 红 `#FF0000` / 深蓝 `#1F4F7D`；标题微软雅黑加粗居中36pt；正文黑体加粗≥24pt；数学符号 `$...$`（兼容 `$$...$$`）→ Times New Roman 斜体不加粗；行距1.5；单页要点≤5。
- 中文必须写 `a:ea/@typeface`（标题微软雅黑、正文黑体），否则回退宋体。
- 流程铁律：抽文本→出大纲(等用户确认)→生成→校验→交付；阶段3未确认绝不生成。
- 页面顺序铁律：【导】情境导入**一律放在封面之前**（预习提纲→【导】情境导入→封面→学习目标→【学】任务→【练】→【思】）；2026-07-25 老师明确确认，早期"封面在情境前"已废弃。
- 坑：docx 须 zipfile 抽 document.xml 再读；LaTeX 命令 `\subset`/`\Rightarrow` 会原样显示→用 Unicode `△⊂∠⇒`；`✓✗`在微软雅黑变方框→用 `√×`。
- **学校官方课件模板**：`E:\教学资料\大姚新课堂.potx`（大姚新课堂·学校统一母版）。它是 `.potx`（python-pptx 的 `Presentation()` 会因其 contentType=template.main 拒读，需转 `.pptx` 或 zipfile 直读）。已验证：16:9、accent1=#4F81BD（与规范蓝一致）、dk2=#1F497D（≈深蓝#1F4F7D）、含 FF0000 红标、含 `Blank` 版式、自带 10 页示例骨架（封面/预习/导入揭题/目标/任务一/任务二/练习/反思/小结，结构与我们锁定顺序高度吻合）。**应作为真实基版替代缺失的 `课件模板.pptx`**——转换后的可用副本在 `D:\workspace\2026-07-25-13-18-32\大姚新课堂.pptx`。生成器会 `delete_all_slides` 清掉样例页，不污染输出。之前 13–18 章用的是 `13-1三角形的概念_模板版.pptx` 作代理，如需与学校模板完全统一可重做。
