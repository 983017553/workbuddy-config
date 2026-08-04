---
name: courseware-pptx
description: 由导学案（docx/pdf/txt/图片）一键生成可编辑课堂教学 PPT 课件。严格按用户锁定的课件规范（16:9、蓝#4F81BD+红#FF0000、标题微软雅黑加粗居中36pt、正文黑体加粗≥24pt、数学符号Times斜体、单页≤5要点、行距1.5）。工作流：抽文本→出大纲(等确认)→生成→校验→交付。当用户要做课件/PPT、把导学案转幻灯片、或说"出课件/做PPT/转PPT/生成课堂教学PPT"时触发。
agent_created: true
---

# 课堂教学 PPT 课件生成器（courseware-pptx · 标准版 v2）

把一份**导学案**变成**标准可编辑 .pptx 课堂教学课件**。
完整规范与拆分/动画/校验规则见工作区 `课堂教学PPT课件生成工作流.md`（与本技能同步）。

## ⚠ 用户锁定的课件规范（勿凭记忆，以本段为准）
- **版式**：16:9（13.33×7.5），课堂投影简约风，浅色纯色背景，留白 ≥ 30%。
- **配色（锁定 HEX）**：主色蓝 `#4F81BD`、强调红 `#FF0000`、深蓝点缀 `#1F4F7D`。
- **字体**：标题=微软雅黑**加粗居中**36pt；正文=黑体**加粗**≥24pt；数学符号=`$...$`→**Times New Roman 斜体不加粗**。
  - 中文必须写 `a:ea/@typeface`（标题"微软雅黑"、正文"黑体"），否则回退宋体。
- **字号层级**：标题36–40 / 定义结论28–32 / 例题题目24–28 / 提示20–24；**单页要点 ≤ 5**。
- **行距 1.5**；红色【】标签标题居中。

## 标准页面结构（权威顺序 · 2026-07-25 起【导】情境导入固定在封面之前）
1. 预习提纲（导学案有则保留）
2. 【导】情境导入（1 情境 + 1 问题，可含演示动画）← **封面之前**
3. 封面
4. 学习目标（≤3 条，**全文引用导学案**）
5. 【学】任务一 … 任务 N（按任务数自适应；**主标题与内容均全文引用导学案原句**，每任务可拆"探究/归纳/应用"多页，重点习题单独分页）
6. 【练】对点训练（**不按基础C/综合B/拓展A 分层单独分页**；按内容灵活合并，单页 ≤ 3 题）
7. 【思】课堂小结

> 课型变体：概念课(定义/元素/分类/辨析)、性质定理课(探究/归纳/应用/分类讨论，常含稳定性)、复习课(可省情境)、专题冲刺(题型建模+压轴)。

## 工作流（6 阶段，阶段3未确认绝不生成）
0. **准备**：确认模板路径（默认用户桌面 `课件模板.pptx`；无则内置简约兜底）。
1. **抽取**：docx 二进制→zipfile 读 `word/document.xml` 遍历 `w:t`；pdf/txt 直读；图片 OCR。
2. **拆分出大纲**：按模块关键词（预习/情境/目标/任务N/例题/练习/小结）映射分页，重点习题单独页，输出 `XX_PPT大纲.md`。
3. **大纲确认（人工）**：呈现大纲，等用户增删/改标题/调页序。
4. **生成**：数据驱动读大纲 JSON → 套模板+规范 → 生成 pptx（含动画嵌入）。
5. **校验**：脚本自动核验（见下"校验清单"）。
6. **交付**：present 文件。

## 自动拆分规则
- 模块关键词识别见工作流文档第四节；任务数自适应；例题/压轴/易错单独分页；探究页保留"____"填空+`!!发现!!`红字。

## 演示动画/视频
- 情境含"拼摆/围不成/稳定性/运动/变化"→用 **PIL 逐帧+ffmpeg 编码 MP4**（几何精确，优于AI生图）；中文用 `√ ×` 非 `✓ ✗`。
- 嵌入：`add_movie(path, l, t, w, h, poster_frame_image=poster, mime_type='video/mp4')`；情境页视频居中下方，稳定性页左视频+右文字。

## 生成脚本（数据驱动）
`scripts/gen_courseware.py`（通用版，基于已验证的 13-2 实现）：继承模板、红标标题居中、正文黑体加粗、数学 Times 斜体、视频按 `kind` 嵌入。
```bash
python scripts/gen_courseware.py 大纲.json --out 课件.pptx --template 课件模板.pptx
```
大纲 JSON（每页 `kind`：cover / section / import / study / practice / stability / summary）：
```json
{"template":"课件模板.pptx","pages":[
  {"kind":"section","tag":"预习提纲","bullets":["回顾...","实验..."]},
 {"kind":"import","tag":"【导】情境导入","bullets":["情境...","!!问题!!..."],"video_path":"sticks_demo.mp4"},
 {"kind":"cover","title":"13.2 三角形的边","subtitle":"三边关系定理","info":"人教版八上"},
 {"kind":"section","tag":"学习目标","bullets":["1. ...","2. ...","3. ..."]},
 {"kind":"study","tag":"【学】任务一：探究三边关系","sub_tag":"探究","bullets":["拼摆...","比较..."]},
 {"kind":"practice","tag":"【练】对点训练","bullets":["基础...","综合..."]},
 {"kind":"summary","tag":"【思】课堂小结","bullets":["知识...","思想..."]}
]}
```
标记语法：数学 `$...$`（兼容 `$$...$$`）、红字 `!!...!!`、加粗 `**...**`。

## 校验清单（生成后脚本自动跑）
16:9 尺寸｜页数符合大纲｜标题微软雅黑加粗居中36pt且 `a:ea=="微软雅黑"`｜正文黑体加粗≥24pt且 `a:ea=="黑体"`｜数学 Times 斜体未加粗｜红标 `#FF0000`｜行距 1.5｜单页要点≤5｜视频已嵌入且坐标正确。

## 坑（务必避开）
- docx 是二进制，必须 zipfile 抽 `document.xml`，不能直接 Read。
- LaTeX 命令 `\subset`/`\Rightarrow` 会原样显示 → 用 Unicode `△ ⊂ ∠ ⇒` 或英文符号配 `$...$`。
- `✓ ✗` 在微软雅黑变方框 → 用 `√ ×`。
- 字体读取校验时 `a:latin`/`a:ea` 嵌套在 `a:rPr` 下，要从 `r._r.find(qn('a:rPr'))` 再找，直接 `r._r.find(qn('a:ea'))` 会返回 None（假阴性）。
- **`.potx` 模板读取/转换**：`Presentation(path)` 会因根部件 contentType=`presentationml.template.main+xml` 直接抛 `not a PowerPoint file`（这是 python-pptx 对模板的已知限制，文件本身没坏）。两种用法：
  ① 只读不生成 → 用 zipfile 直接解析 `ppt/presentation.xml` + `ppt/slides/slideN.xml`（同 docx 思路），可拿母版/版式/配色/文字；
  ② 当生成基版 → 先转 `.pptx`：把 `[Content_Types].xml` 里 `/ppt/presentation.xml` 的 Override `ContentType` 从 `template.main+xml` 改成 `presentation.main+xml` 再打包，python-pptx 即可打开。生成器会 `delete_all_slides(prs)` 清掉模板自带样例页，不污染输出；只要模板含 `Blank`/`空白` 版式即可正常套用（如学校「大姚新课堂.potx」即此类，16:9、accent1=#4F81BD 与规范蓝一致）。

## docx 抽取片段
```python
import zipfile
from xml.etree import ElementTree as ET
W="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
root=ET.fromstring(zipfile.ZipFile(path).read("word/document.xml").decode("utf-8"))
print("\n".join("".join(t.text or "" for t in p.iter(f"{{{W}}}t")) for p in root.iter(f"{{{W}}}p")))
```
