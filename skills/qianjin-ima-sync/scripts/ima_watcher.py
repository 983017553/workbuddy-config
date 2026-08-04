#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
ima_watcher.py — WorkBuddy outputs 目录文件监听守护进程
监听 D:\workspace\outputs，出现新增/修改的文件或图片即增量同步到
IMA「尘风的知识库 → workBuddy库」文件夹（folder_id=folder_7458693620721317）。

特性：
- 轮询间隔 POLL 秒，空闲零 IMA 接口调用（不轮询时完全不访问 ima）。
- 复用 qianjin-ima-sync 的 ima_sync.py 做实际上传（--folder 落地到指定文件夹）。
- 与 hourly 自动化共用 state 文件去重，互不重复上传。
- 凭证从真实 C:\Users\hf770\.config\ima\* 读取并以环境变量注入子进程，
  不依赖沙箱家目录。
"""

import os
import sys
import time
import json
import subprocess

# ── 配置 ─────────────────────────────────────────────
WATCH = r"D:\workspace\outputs"
KB_ID = "AFi0-ITWj0mBtmemiWrt4wJqrqfDcDLNJTeOpxVCsd0="
FOLDER_ID = "folder_7458693620721317"
STATE_FILE = r"C:\Users\hf770\.config\ima-sync\state.json"
LOG_FILE = r"C:\Users\hf770\.config\ima-sync\watcher.log"
PY = r"C:\Users\hf770\.workbuddy\binaries\python\versions\3.13.12\python.exe"
SCRIPT = r"C:\Users\hf770\.workbuddy\skills\qianjin-ima-sync\scripts\ima_sync.py"
CID_FILE = r"C:\Users\hf770\.config\ima\client_id"
KEY_FILE = r"C:\Users\hf770\.config\ima\api_key"
POLL = 10  # 秒

# 复用 ima_sync 的支持类型集合与指纹函数
sys.path.insert(0, os.path.dirname(SCRIPT))
import ima_sync  # noqa: E402
SUPPORTED_EXTS = ima_sync.SUPPORTED_EXTS


def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def scan(watch):
    out = []
    for root, _, names in os.walk(watch):
        for n in names:
            p = os.path.join(root, n)
            ext = n.rsplit(".", 1)[-1].lower() if "." in n else ""
            if ext in SUPPORTED_EXTS:
                out.append(p)
    return out


def main():
    if not os.path.exists(CID_FILE) or not os.path.exists(KEY_FILE):
        log("❌ 缺少 IMA 凭证文件，守护进程退出")
        sys.exit(1)
    cid = open(CID_FILE, "r", encoding="utf-8").read().strip()
    key = open(KEY_FILE, "r", encoding="utf-8").read().strip()
    env = os.environ.copy()
    env["IMA_OPENAPI_CLIENTID"] = cid
    env["IMA_OPENAPI_APIKEY"] = key

    os.makedirs(WATCH, exist_ok=True)
    state = load_state()
    log(f"👀 开始监听 {WATCH}（间隔 {POLL}s）-> ima workBuddy库")

    while True:
        try:
            files = scan(WATCH)
            for f in files:
                rel = os.path.relpath(f, WATCH)
                fp = ima_sync._fingerprint(f)
                if state.get(rel) == fp:
                    continue  # 已同步且未改动
                r = subprocess.run(
                    [PY, SCRIPT, "upload-file", f, "--kb", KB_ID, "--folder", FOLDER_ID],
                    env=env, capture_output=True, text=True, timeout=120,
                )
                if r.returncode == 0 and "✅" in r.stdout:
                    state[rel] = fp
                    save_state(state)
                    log(f"⬆️ 已同步: {rel}")
                else:
                    log(f"⚠️ 同步失败: {rel} | {r.stdout.strip()[-200:] or r.stderr.strip()[-200:]}")
            time.sleep(POLL)
        except Exception as e:
            log(f"⚠️ 异常: {e}")
            time.sleep(POLL)


if __name__ == "__main__":
    main()
