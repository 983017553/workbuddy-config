---
name: da-yao-guide-sheet
description: 导学案撰写系统 · 大姚「导—学—练—思」导学案生成（代码承载形态，挂在教务底座 /api/guide/*）。当用户要写/生成/撰写导学案、学案、课时导学案，或给定课题+年级册别+课型时触发。绑定 N1~N8 流水线（采集→解析→知识坐标→模板→生成→审阅→存档IMA→Word）。
agent_created: true
---

# da-yao-guide-sheet（导学案撰写系统 · 工作流）

> ## 📌 发布信息（3.5 上线版 · 2026-07-16）
> - **状态**：已上线发布，全组教师可调用（部署形态：本用户级 Skill + 专家中心「大姚导学案专家」独立入口）。
> - **版本**：v1.4（3.5 上线）。系统常量与《WorkBuddy_3.5上线发布指令》第一节**原样一致**：KB_ID=`AFi0-ITWj0mBtmemiWrt4wJqrqfDcDLNJTeOpxVCsd0=`、FOLDER_TPL=`folder_7483179980047597`、FOLDER_COMPILE=`folder_7471565503472369`、FOLDER_SAVE=`folder_7456957162087075`。
> - **技能绑定**：N5→`da-yao-guide-sheet`；N3/N4/N7→IMA 知识库连接器（`ima-skills`/`ima-mcp` 读 + OpenAPI 写）；N8→`minimax-docx`（本机未装 `ima-docx`，按 v3 权威指令用 minimax-docx，含 python-docx / 纯标准库 DOCX 回退）。
> - **4 课型冒烟测试**：概念/性质定理/复习/习题 全通过——导学案含知识坐标 4 字段、结构符合「导—学—练—思」、【练】区带【基础】【提升】【拓展】三层、Word 可下载、按 `{年级册别}/第{章节}章/` 归档 IMA 正确。

把「导学案撰写系统 v1.4」封装为可复用工作流。代码承载形态位于 `D:\workspace\导学案撰写系统\`，并已挂载到教务底座 `D:\workspace\app.py|api.py|db.py`（桥接层 `D:\workspace\guide_service.py` 提供 `/api/guide/*`）。本 SKILL.md 全文作为 N5 调 LLM 时的 system prompt。

## 何时用
- 用户说"写一份导学案""生成 XX 的导学案""八年级上册 三角形的概念 概念课"。
- 用户给课题名称 + 年级册别 + 课型（概念课/性质定理课/复习课/习题课）。
- 用户给"执行包"md 文件要求按 N7 覆盖上传 / 模板优化上传。

## 三种调用方式（注册为可用工作流后的入口）
- **用法 A（最简，推荐）**：在 WorkBuddy 对话里直接说课题 / 丢执行包给我。我跑 `main.py` 或专用脚本，产出 `.md/.docx` 并 N7 写回 IMA。无需用户启服务。
- **用法 B（自建服务）**：`cd D:\workspace && python app.py`（默认 `http://127.0.0.1:8765`），调接口：
  - `GET /api/guide/templates` 列模板
  - `POST /api/guide/run`（body `{raw_input, generated?, archive?, export?}`）跑全流程
  - `GET /api/guide/list` 查任务（`guide_sheets` 表）
  - `POST /api/guide/export` / `POST /api/guide/archive` 对已有任务重跑 N8 / N7
- **用法 C（命令行）**：`cd D:\workspace\导学案撰写系统 && python main.py --title "..." --grade 八年级上册 --ketype 概念课 [--special "..."]`；批量 `python main.py --batch cases.json`；`--render _gen_*.json` 直接渲染。

## 流程（N1→N8）
1. **N1 触发输入**：收集 课题名称（可含章节如 13.1）、年级册别、课型、特殊要求。
2. **N2 课题解析**：`n2_parse.parse_lesson` 提取 章节/小节、推断课型、清洗标题（`CHAPTER_HINTS` 维护课题→章节映射）。
3. **N3 知识坐标**：`n3_kb.retrieve_coords` 按 `config.COORD_FILE_KEYWORD` 关键词匹配本地 `kb_compiled/{年级册别}/` 下文件（如 `人教版八年级-知识图谱.md`）。`run_full` 章节以 generated 内容章节为准（修正"全等"hint 误判第12章→应为内容第14章）。
4. **N4 模板加载**：`n4_template.load_template` 按课型读 `templates/01~04`（已同步 IMA 权威优化模板）。剥离 `---` YAML 前导元信息，仅留「大姚新课堂导学设计」正文。
5. **N5 内容生成**：`n5_generate.generate`（本 SKILL.md 全文作为 system prompt）。设 `LLM_API_KEY`(+/`LLM_BASE_URL`/`LLM_MODEL`) 走 LLM 真实生成；未配则辅助模式（生成 `PROMPT.md`+空 `GENERATED.json` 等你补全再 render）。
6. **N6 人工审阅**：展示 `.md`，按修改指令局部重生成或确认（唯一需用户动手的环节）。
7. **N7 存档 IMA**：`kb_write.archive_file` / `guide_service._guide_archive` 按 `{年级册别}/第{章节}章/` 层级写回成稿夹 `folder_7456957162087075`（=教学设计与学案），命名 `{章节}-{课时标题}-{课型}-导学案.md/.docx`。覆盖上传：先 `rename_knowledge` 给旧件打 `_old`，再 `upload_to_folder` 直投干净名（执行包模式见 `_upload_v1.py`）。
8. **N8 Word 导出**：`gen_docx.export_docx` 三级回退——① minimax-docx（需 dotnet CLI，v3 指定引擎）；② python-docx；③ 纯标准库 DOCX 写出（zipfile+WordprocessingML，零依赖，本环境实际生效）。A4/宋体12pt/1.5倍行距。

## 模块映射（v3 抽象名 → 实际文件）
| v3 模块 | 实际文件 | 节点 |
|---|---|---|
| `lesson_parse.py` | `n2_parse.py` | N2 |
| `kb_read.py` | `n3_kb.py`+`n4_template.py` | N3+N4 |
| `skill_prompt.py` | `n5_generate.py`（本 SKILL 作 system prompt） | N5 |
| `kb_write.py` | `kb_write.py` | N7 |
| `gen_docx.py` | `gen_docx.py`（原 `n8_docx.py` 已 re-export） | N8 |
| `guide_flow.py`(总控) | `main.py`(`run_full`) | 编排 |
| 底座桥接 | `guide_service.py` + `api.py` 的 `module=='guide'` | HTTP 入口 |
- `config.py` 路径已改为基于 `__file__` 的**绝对路径**（修复从底座 CWD 调用时模板/坐标/输出错位 bug）。

## IMA 知识库（已接通）
- KB：`AFi0-ITWj0mBtmemiWrt4wJqrqfDcDLNJTeOpxVCsd0=`（OpenAPI 侧 ID；与 ima-mcp 内部 `0019f34ef5c04a68` 同库）。OpenAPI 凭证 `~/.config/ima/`。
- 三夹：模板 `folder_7483179980047597`、编译产物 `folder_7471565503472369`、成稿 `folder_7456957162087075`。
- 同步桥：MCP 仅主进程可用，Python 子进程只读本地 `templates/`+`kb_compiled/`。更新 IMA 后重跑同步（或用 `_upload_tpl_v1.py` 等脚本直传）。

### ⚠ IMA OpenAPI 写通道能力矩阵（2026-07-16 实测）
- ✅ `create_folder`（父目录参数是 `folder_id` 非 `parent_folder_id`）、`add_knowledge`(带 folder_id 直投)、`rename_knowledge`(带 media_id 打标记)。
- ❌ `move_knowledge`：no-op，返回 code:0 但 `move_results` 恒空、不移动。
- ❌ `delete_*`/`remove_*`：全部 404，OpenAPI 无删除端点。
- 陷阱：`ima_api.cjs` 对 404 返回空 body+退出码0，move no-op 返回 code:0，均会被误判成功。**删/移必须回查 `get_knowledge_list` 的 `parent_folder_id`/`current_path` 确认**。
- 残留清理：无删除端点，只能用户在 IMA App 手动删；本系统策略：旧件 `rename_knowledge` 打 `_old` 前缀供识别。

## 当前已落地状态（2026-07-16）
- ✅ 4 课型联调通过：概念课(13.1 三角形的概念)/性质定理课(三角形内角和定理)/复习课(第13章复习)/习题课(全等三角形判定讲评)；存档层级与命名正确；N8 均产出合法 .docx。
- ✅ 4 套优化模板（含【基础】【提升】【拓展】分层标签）已覆盖上传 IMA 模板库 `folder_7483179980047597`，旧版打 `_old`；本地 `templates/01~04` 同步。
- ✅ 底座桥接 `/api/guide/*` 已接线（lazy import 避免循环依赖），`db.py` 新增 `guide_sheets` 任务表。

## 注意
- 真实模板变量：`{{课题名称}}{{年级册别}}{{章节}}{{小节}}{{目标1..3}}{{重点}}{{难点}}{{预习任务}}{{情境导入}}{{任务一/二/三_标题/时间/活动}}{{练1_时间}}{{教师行为N}}{{反思N}}{{基础题}}{{提升题}}{{拓展题}}{{知识1/2}}{{思想方法}}{{板书}}` 等；分层题优化模板固定为【基础】【提升】【拓展】三层。习题课用 `{{专项或试卷名称}}`/`{{训练目标}}`；复习课用 `{{复习目标}}`；性质定理课任务带 (探究发现)/(证明归纳) 后缀。
- `基础题/提升题/拓展题` 内容不带前导序号（模板自带编号），避免双重编号。
- `kb_compiled` 当前含「八年级上册」真实产物；其他年级需放入对应命名文件或重跑 IMA 同步。
- `n2_parse.CHAPTER_HINTS` 维护"课题→章节"映射，按本校教材版本调整。
