---
name: windows-bsod-analyze
description: 在本机无界面跑通 WinDbg/cdb 的 !analyze -v 分析 Windows 蓝屏(BSOD) 转储(dmp)，定位崩溃驱动。适用于用户报告"电脑蓝屏/无故重启/关机后重启"，需要看 dump 的 bugcheck 与元凶驱动。已知坑：①WindowsApps 里的 cdb.exe 直接按路径执行被拒(ACL)，须复制到普通目录；②本机 ntoskrnl 可能与公共符号服务器 PDB 版本不符导致栈回溯失真(nt_wrong_symbols)，此时模块名列表(lm)仍可靠、但单一驱动精确归因需完整内核转储+符号已发布版本重抓；③转储可能是 PAGEDU64(分页内核转储)而非标准 MDMP minidump，Python 按 minidump 解析会失败，但 cdb 能正常读。
---

# 本机无界面分析 Windows 蓝屏转储

目标：用 WinDbg 的命令行版 `cdb.exe` 在 WorkBuddy 的 Bash 里无界面跑 `!analyze -v`，读出 bugcheck 码与崩溃驱动，不动图形界面、不麻烦用户操作。

## 前置：确认环境
- Bash 能访问真实 Windows 文件系统：`/c/Windows/Minidump/`、`/d/` 等可见。
- 符号服务器可达性自测：`curl -s -m 3 -o /dev/null -w "%{http_code}" https://msdl.microsoft.com/download/symbols` 应返回 200。
- dump 文件位置：`C:\Windows\Minidump\`（minidump）或 `C:\Windows\MEMORY.DMP`（完整内核转储）。

## 步骤 1：装 WinDbg（含 cdb）
```bash
MSYS_NO_PATHCONV=1 winget install --id Microsoft.WinDbg --accept-package-agreements --accept-source-agreements --disable-interactivity --silent
```
装完后 cdb.exe 在：
`C:\Program Files\WindowsApps\Microsoft.WinDbg_<ver>_x64__8wekyb3d8bbwe\amd64\cdb.exe`

## 步骤 2：绕过 WindowsApps ACL（关键坑①）
直接执行上面路径的 cdb.exe 会被拒（exit 126 权限拒绝，UWP 包二进制受 ACL 保护）。解决：把 `amd64` 目录整体复制出来：
```bash
MSYS_NO_PATHCONV=1 mkdir -p "/d/cdbtools"
MSYS_NO_PATHCONV=1 cp -r "/c/Program Files/WindowsApps/Microsoft.WinDbg_<ver>_x64__8wekyb3d8bbwe/amd64/." "/d/cdbtools/"
# 验证：应打印版本号
MSYS_NO_PATHCONV=1 "/d/cdbtools/cdb.exe" -version
```
之后一律用 `/d/cdbtools/cdb.exe`。

## 步骤 3：跑 !analyze -v（无界面）
```bash
CDB="/d/cdbtools/cdb.exe"
DMP="C:/Windows/Minidump/<文件名>.dmp"
SYM="srv*D:/symcache*https://msdl.microsoft.com/download/symbols"
MSYS_NO_PATHCONV=1 "$CDB" -y "$SYM" -z "$DMP" -c "!analyze -v; q" > /c/Users/<user>/analyze.log 2>&1
echo "EXIT=$?"
```
要点：
- `-y` 设符号路径（本地缓存 + 公共服务器）；首次会下载符号，可能要几分钟，给足超时（最多 540000ms）。
- `-c "!analyze -v; q"` 自动跑分析后退出。
- 用 `> log 2>&1` 落盘，再 `grep`/`Read` 提取关键行，避免大输出被截断。

## 步骤 4：提取关键结论
```bash
LOG="/c/Users/<user>/analyze.log"
grep -aE "BUGCHECK_CODE|BUGCHECK_STR|Probably caused by|MODULE_NAME|IMAGE_NAME|FAILURE_BUCKET_ID|PROCESS_NAME|DPC_WATCHDOG|DPC_QUEUE" "$LOG" | head -40
```
- `BUGCHECK_CODE` 是崩溃码（如 133=DPC 看门狗、1A=内存管理、50=ntfs、D1=驱动误访问等）。
- `Probably caused by : xxx.sys` 是元凶驱动（最理想的一行）。

## 坑②：nt_wrong_symbols（符号版本错乱）
若 `Probably caused by` 显示 `nt_wrong_symbols`，且栈里出现 `fffffb8f` 等**模块表里查不到归属**的假地址，说明本机 ntoskrnl 与公共符号服务器任何 PDB 都不匹配（常见于装了累积更新但对应公共符号未发布的版本）。此时：
- **模块名列表仍可靠**：`lm` 输出的驱动名来自 dump 本身，不受 PDB 影响。可单独跑 `cdb -y "D:/symcache" -z <dmp> -c "lm; q"` 拿完整驱动清单。
- 栈回溯失真，不能据此认驱动。
- 想精确归因单一驱动：让用户改抓**完整内核转储**（系统属性→高级→启动和故障恢复→写入调试信息=完全内存转储），并先 Windows Update 到符号已发布的版本，重抓后再 `!analyze -v` 即可精确指认。
- 试过但常无效的挽救：`-c ".symopt+0x40; .symfix D:/symcache; .reload; !analyze -v"`（强制加载不匹配符号），以及把 `-y` 指向本机 `C:/Windows/System32`——本机 ntoskrnl 与 dump 同版本时偶尔能匹配，但多数仍失败。

## 坑③：PAGEDU64 格式
若 `head -c 8 <dmp>` 是 `PAGEDU64`/`PAGEKD64`（分页/完整内核转储），**不是标准 MDMP minidump**。不要用 Python 按 minidump 格式解析（会 assert 失败），cdb 已能正常读它。模块表结构不同，解析需换 DUMP_HEADER64 布局。

## 常见 bugcheck 速查
- `0x133` DPC_WATCHDOG：某驱动 DPC 例程在 DISPATCH_LEVEL 霸占 CPU 超时。嫌疑：存储驱动(storahci/storport)、网卡(ndis/厂商)、显卡、USB、WDF 框架驱动(wdf01000)。结合事件日志里该设备的 Controller Error/重置(Event 11/51/153)交叉判断。
- `0x1A` MEMORY_MANAGEMENT：内存或内存管理器。建议 Windows 内存诊断。
- `0x50` / `0xD1`：驱动误访问内存/空指针，直接看 `Probably caused by` 的第三方 .sys。
- `0x1E`/`0x3B`：系统线程异常，多为第三方驱动。

## 配套：Windows 内存诊断（排查 0x1A / 硬件整体不稳）
当 bugcheck 含 `0x1A`(内存管理) 或一天内出现多种不同码（如 133+1A，提示可能硬件不稳）时，安排内存诊断。

**权限墙（实测）**：在 WorkBuddy 非提权 Bash 会话里，`bcdedit /bootsequence {memdiag} /addfirst`（改 BCD 引导存储）与 `reg add HKLM\...\Memory Management\RunMemoryDiagnostic`（写敏感键）都会返回**拒绝访问**。但**用户双击 `.reg` → UAC 批准 → 导入 HKLM** 以及**右键"以管理员身份运行"的 `.bat`** 都能拿到权限。

**做法**：生成一份 ASCII 内容的 `.bat`（避免中文乱码），让用户右键"以管理员身份运行"：
```bat
@echo off
net session >nul 2>&1 || (echo Need admin & pause & exit /b 1)
bcdedit /bootsequence {memdiag} /addfirst
set /p R=Reboot now? (Y/N): 
if /i "%R%"=="Y" shutdown /r /t 10 /c "Memory Diagnostic"
```
- `{memdiag}` 只影响**下一次**启动，跑完自动恢复正常引导，无需清理。
- 测试蓝屏界面按 **F1 → 选 Extended → F10** 做最彻底扫描（默认 Standard 漏检率高）。
- 结果在事件查看器：Windows 日志→系统，源 `MemoryDiagnostics-Results`（或 `wevtutil qe System "/q:*[System[Provider[@Name='MemoryDiagnostics-Results']]]"`）。Event ID 2001 / "未检测到问题"=健康；有报错=内存或内存控制器/插槽/XMP 不稳。
- 备选：用户直接 Win+R 输入 `mdsched` 回车，选"立即重新启动并检查问题"（自带提权，最稳）。

## 交付给用户的话术要点
1. 先给 bugcheck 码与中文含义（已实跑确认，非猜测）。
2. `Probably caused by` 能指认就直接给驱动名+处理建议（更新/回滚/卸载）。
3. 指认不了就说明"符号版本错乱导致栈失真"，改给：已加载驱动清单里的最可疑类（结合事件日志历史），并说明"抓完整内核转储+更新到符号已发布版本可一步锁定"。
4. 若一天内出现**不同** bugcheck 码（如 133 + 1A），提示可能指向硬件整体不稳（RAM 和/或 SSD），建议内存诊断+CrystalDiskInfo 查 SSD SMART(C5/C7)。
