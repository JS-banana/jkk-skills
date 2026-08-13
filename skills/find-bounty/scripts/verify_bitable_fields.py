#!/usr/bin/env python3
"""Verify the live Feishu Base fields used by campaign_bitable_sync.py.

This is read-only and uses the logged-in lark-cli user identity.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

BASE_TOKEN_ENV = "AI_CAMPAIGN_BASE_TOKEN"
TABLE_ID_ENV = "AI_CAMPAIGN_TABLE_ID"
DEFAULT_TABLE_ID = "tblYhMRh3fJ0FDfW"

REQUIRED = [
    "活动名称", "厂商", "活动类型", "难度评级", "推荐指数", "难度说明",
    "奖励详情", "活动形式", "参与方式", "获奖条件", "时间节点备注",
    "建议", "状态", "报名入口", "官方确认", "截止时间", "地区",
    "奖励类型", "发现日期", "来源渠道", "预计投入",
]


def resolve_target(base_token=None, table_id=None):
    base_token = (base_token or os.environ.get(BASE_TOKEN_ENV) or "").strip()
    table_id = (table_id or os.environ.get(TABLE_ID_ENV) or DEFAULT_TABLE_ID).strip()
    if not base_token:
        raise RuntimeError(f"Pass --base-token or set {BASE_TOKEN_ENV}")
    return base_token, table_id


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-token", help=f"Feishu Base token, or {BASE_TOKEN_ENV}")
    parser.add_argument("--table-id", help=f"Feishu table ID/name, or {TABLE_ID_ENV}; defaults to bundled table")
    args = parser.parse_args()

    try:
        base_token, table_id = resolve_target(args.base_token, args.table_id)
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 2

    cmd = [
        "lark-cli", "base", "+field-list",
        "--base-token", base_token,
        "--table-id", table_id,
        "--as", "user",
        "--format", "json",
    ]
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode:
        sys.stderr.write(proc.stderr or proc.stdout)
        return proc.returncode

    payload = json.loads(proc.stdout)
    fields = payload.get("data", {}).get("fields", [])

    print(f"=== Bitable Fields ({len(fields)}) ===")
    for field in fields:
        print(f"  {field.get('name', ''):20s} | {field.get('type', '')}")

    existing = {field.get("name", "") for field in fields}
    missing = [name for name in REQUIRED if name not in existing]
    if missing:
        print(f"\nMISSING FIELDS (will cause FieldNameNotFound): {missing}")
        return 1

    score = next((field for field in fields if field.get("name") == "推荐指数"), {})
    score_options = [opt.get("name") for opt in score.get("options", [])]
    if score.get("type") != "select" or "⭐⭐⭐⭐⭐" not in score_options:
        print("\n推荐指数字段不是预期的星级 select")
        return 1

    reward_type = next((field for field in fields if field.get("name") == "奖励类型"), {})
    if reward_type.get("type") != "select" or not reward_type.get("multiple"):
        print("\n奖励类型字段不是预期的多选 select")
        return 1

    if "活动详情链接" in existing:
        print("\n活动详情链接 exists; update the write contract before using it")
        return 1

    print(f"\nAll {len(REQUIRED)} required fields present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
