#!/usr/bin/env python3
"""dream skill 的信号采集器：扫描 ~/.claude/projects/ 下的 memory 与会话记录。

用法:
  gather.py --list [--days N]              列出各项目概况，按近期活跃度排序
  gather.py --extract=<project-dir> [--days N] [--max N]
                                           提取某项目近期 transcripts 中的用户输入
                                           （项目目录名以 - 开头，必须用 = 连接）
"""
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"


def recent_transcripts(project: Path, days: int):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    out = []
    for f in project.glob("*.jsonl"):
        mtime = datetime.fromtimestamp(f.stat().st_mtime, timezone.utc)
        if mtime >= cutoff:
            out.append((mtime, f))
    return sorted(out)


def project_cwd(transcripts):
    """从最近一份 transcript 里读出项目真实路径（jsonl 行内的 cwd 字段）。"""
    for _, f in reversed(transcripts):
        with open(f, errors="replace") as fh:
            for line in fh:
                try:
                    cwd = json.loads(line).get("cwd")
                except json.JSONDecodeError:
                    continue
                if cwd:
                    return cwd
    return "-"


def cmd_list(days: int):
    rows = []
    for project in sorted(PROJECTS.iterdir()):
        if not project.is_dir():
            continue
        memory = project / "memory"
        mem_files = len(list(memory.glob("*.md"))) if memory.is_dir() else 0
        recent = recent_transcripts(project, days)
        total = len(list(project.glob("*.jsonl")))
        if mem_files == 0 and not recent:
            continue
        latest = max((m for m, _ in recent), default=None)
        rows.append((latest, project.name, mem_files, len(recent), total,
                     project_cwd(recent)))
    rows.sort(key=lambda r: (r[0] is not None, r[0]), reverse=True)
    print(f"project\tmemory_files\trecent_{days}d\ttotal_transcripts\tlast_active\tpath")
    for latest, name, mem, rec, total, path in rows:
        ts = latest.strftime("%Y-%m-%d") if latest else "-"
        print(f"{name}\t{mem}\t{rec}\t{total}\t{ts}\t{path}")


def iter_user_prompts(path: Path):
    with open(path, errors="replace") as fh:
        for line in fh:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("type") != "user" or obj.get("isMeta") or obj.get("isSidechain"):
                continue
            content = (obj.get("message") or {}).get("content")
            if isinstance(content, str):
                texts = [content]
            elif isinstance(content, list):
                texts = [b.get("text", "") for b in content
                         if isinstance(b, dict) and b.get("type") == "text"]
            else:
                continue
            for t in texts:
                t = t.strip()
                # 跳过命令回显、caveat、system-reminder 等非人工输入
                if not t or t.startswith("<"):
                    continue
                yield obj.get("timestamp", ""), t


def cmd_extract(name: str, days: int, max_prompts: int, width: int):
    project = PROJECTS / name
    if not project.is_dir():
        sys.exit(f"error: no such project dir: {project}")
    count = 0
    for mtime, f in recent_transcripts(project, days):
        header_printed = False
        for ts, text in iter_user_prompts(f):
            if count >= max_prompts:
                print(f"\n[truncated: reached --max {max_prompts}]")
                return
            if not header_printed:
                print(f"\n## session {f.stem} ({mtime:%Y-%m-%d})")
                header_printed = True
            if len(text) > width:
                text = text[:width] + f"…[+{len(text) - width} chars]"
            print(f"- [{ts[:16]}] {text}")
            count += 1
    if count == 0:
        print(f"(no user prompts found in last {days} days)")


def main():
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--list", action="store_true")
    mode.add_argument("--extract", metavar="PROJECT_DIR")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--max", type=int, default=150, help="每项目最多输出的用户输入条数")
    ap.add_argument("--width", type=int, default=400, help="单条输入截断长度")
    args = ap.parse_args()
    if args.list:
        cmd_list(args.days)
    else:
        cmd_extract(args.extract, args.days, args.max, args.width)


if __name__ == "__main__":
    main()
