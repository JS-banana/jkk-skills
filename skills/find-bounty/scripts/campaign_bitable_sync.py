#!/usr/bin/env python3
"""
Sync vendor campaign data from JSONL to Feishu Bitable.
Reads vendor_campaign_seen.jsonl, checks what's already in Bitable,
and creates records for new campaigns.

Usage:
  python3 campaign_bitable_sync.py --base-token "$AI_CAMPAIGN_BASE_TOKEN"
  python3 campaign_bitable_sync.py --dry --base-token "$AI_CAMPAIGN_BASE_TOKEN"
  python3 campaign_bitable_sync.py --write '{"vendor":"X","campaign":"Y",...}' --base-token "$AI_CAMPAIGN_BASE_TOKEN"

Dependencies: stdlib + lark-cli with user auth.
Config: Pass --base-token or set AI_CAMPAIGN_BASE_TOKEN. Override table with --table-id if needed.

Write contract and field defaults are defined in the find-bounty skill.
"""

from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

SEEN_FILE = os.path.expanduser(
    os.environ.get("AI_CAMPAIGN_SEEN_FILE", "~/.hermes/scripts/vendor_campaign_seen.jsonl")
)
BASE_TOKEN_ENV = "AI_CAMPAIGN_BASE_TOKEN"
TABLE_ID_ENV = "AI_CAMPAIGN_TABLE_ID"
DEFAULT_TABLE_ID = "tblYhMRh3fJ0FDfW"

# ─── lark-cli helpers ─────────────────────────────────────────────────


def resolve_target(base_token=None, table_id=None):
    base_token = (base_token or os.environ.get(BASE_TOKEN_ENV) or "").strip()
    table_id = (table_id or os.environ.get(TABLE_ID_ENV) or DEFAULT_TABLE_ID).strip()
    if not base_token:
        raise RuntimeError(f"Pass --base-token or set {BASE_TOKEN_ENV}")
    return base_token, table_id


def run_lark_cli(args):
    proc = subprocess.run(
        ["lark-cli", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode:
        raise RuntimeError(proc.stderr or proc.stdout)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"lark-cli did not return JSON: {proc.stdout[:500]}") from exc


def cell_text(value):
    if isinstance(value, dict):
        return str(value.get("text") or value.get("value") or value.get("name") or "")
    if isinstance(value, list):
        return ",".join(cell_text(item) for item in value)
    return str(value or "")


URL_RE = re.compile(r"https?://[^\s)\]]+")


def cell_url(value):
    """Extract the first URL from a cell (handles dict {link,text} and markdown [x](y))."""
    if isinstance(value, dict):
        candidate = str(value.get("link") or value.get("text") or "")
    else:
        candidate = cell_text(value)
    match = URL_RE.search(candidate)
    return match.group(0) if match else ""


def normalize_entry_url(url):
    """Dedup key for 报名入口: lowercase host + path without trailing slash + query.

    Cross-aggregator duplicates carry different titles/vendors but the same
    entry URL, so this is the primary duplicate signal.
    """
    parsed = urlparse(str(url or "").strip())
    if not parsed.netloc:
        return ""
    query = f"?{parsed.query}" if parsed.query else ""
    return f"{parsed.netloc.lower()}{parsed.path.rstrip('/')}{query}"


# ─── Bitable operations ───────────────────────────────────────────────

def list_existing_campaigns(base_token, table_id):
    """Get existing dedup keys from Bitable: {"names": vendor|campaign, "urls": normalized 报名入口}."""
    names = set()
    urls = set()
    offset = 0
    limit = 200
    while True:
        resp = run_lark_cli(
            [
                "base", "+record-list",
                "--base-token", base_token,
                "--table-id", table_id,
                "--field-id", "活动名称",
                "--field-id", "厂商",
                "--field-id", "报名入口",
                "--offset", str(offset),
                "--limit", str(limit),
                "--as", "user",
                "--format", "json",
            ]
        )
        data = resp.get("data", {})
        # lark-cli 1.0.5x returns columnar {fields: [名...], data: [[行]...]};
        # keep the items/records dict shape as fallback for other versions.
        rows = data.get("data")
        if isinstance(rows, list):
            columns = data.get("fields") or []
            batch = [dict(zip(columns, row)) for row in rows]
        else:
            batch = [item.get("fields", {})
                     for item in (data.get("items") or data.get("records") or [])]
        for fields in batch:
            name = cell_text(fields.get("活动名称"))
            vendor = cell_text(fields.get("厂商"))
            names.add(f"{vendor}|{name}".lower().strip())
            url_key = normalize_entry_url(cell_url(fields.get("报名入口")))
            if url_key:
                urls.add(url_key)
        if len(batch) < limit:
            break
        offset += len(batch)
    return {"names": names, "urls": urls}


def create_record(fields, base_token, table_id):
    """Create a single record in Bitable."""
    ordered_fields = list(fields)
    payload = {
        "fields": ordered_fields,
        "rows": [[fields[field] for field in ordered_fields]],
    }
    return run_lark_cli(
        [
            "base", "+record-batch-create",
            "--base-token", base_token,
            "--table-id", table_id,
            "--json", json.dumps(payload, ensure_ascii=False),
            "--as", "user",
            "--format", "json",
        ]
    )


# ─── Data mapping ─────────────────────────────────────────────────────

def normalize_score(score):
    """Normalize score to integer 1-5. Handles legacy 5-25 scale and star strings."""
    if isinstance(score, str) and '⭐' in score:
        return max(1, min(5, score.count('⭐')))
    s = int(score)
    if s > 5:  # legacy 5-25 scale
        if s >= 20: return 5
        if s >= 18: return 4
        if s >= 15: return 3
        if s >= 11: return 2
        return 1
    return max(1, min(5, s))


def score_to_advice(score):
    """Map normalized score (1-5) to advice text."""
    s = normalize_score(score)
    if s >= 5: return "立即行动"
    if s >= 4: return "值得做"
    if s >= 3: return "观望"
    return "跳过"


def date_to_ms(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    dt = dt.replace(tzinfo=timezone(timedelta(hours=8)))
    return int(dt.timestamp() * 1000)


def score_to_stars(score):
    """Convert score to the live Base select value."""
    return "⭐" * normalize_score(score)


def jsonl_record_to_bitable_fields(rec):
    """Convert a JSONL seen record to Bitable fields dict."""
    vendor = rec.get("vendor", "其他")
    campaign = rec.get("campaign", "")
    score = rec.get("score", 0)
    url = rec.get("url", "")
    seen_at = rec.get("seen_at", datetime.now().strftime("%Y-%m-%d"))
    # Clean vendor name (remove parenthetical)
    clean_vendor = vendor.split(" (")[0] if " (" in vendor else vendor
    return {
        "活动名称": campaign,
        "厂商": clean_vendor,
        "活动类型": "其他",          # Single-select, agent should override
        "难度评级": "⭐⭐⭐ 需花时间",  # Single-select, agent should override
        "难度说明": "",
        "奖励详情": campaign.split(" - ")[-1] if " - " in campaign else "",
        "活动形式": "",
        "参与方式": "",
        "获奖条件": "",
        "时间节点备注": "",
        "推荐指数": score_to_stars(score),  # Select type, star string
        "建议": score_to_advice(score),   # Single-select, derived from score
        "状态": "新发现",                  # Single-select
        "报名入口": url,
        "官方确认": "⚠️ 疑似",             # Single-select, agent should override
        "地区": "全球",                     # Single-select, agent should override
        "奖励类型": ["其他"],               # Multi-select, agent should override
        "来源渠道": "其他",                 # Single-select, agent should override
        "预计投入": "1-3天",                # Single-select, agent should override
        "发现日期": date_to_ms(seen_at),
    }


# ─── Main ─────────────────────────────────────────────────────────────

def load_seen():
    """Load all records from JSONL."""
    records = []
    if not os.path.exists(SEEN_FILE):
        return records
    with open(SEEN_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def sync_all(dry_run=False, base_token=None, table_id=None):
    """Sync all new JSONL records to Bitable."""
    seen = load_seen()
    if not seen:
        print("JSONL 文件为空，无记录可同步")
        return 0

    base_token, table_id = resolve_target(base_token, table_id)
    existing = list_existing_campaigns(base_token, table_id)

    new_records = []
    for rec in seen:
        vendor = rec.get("vendor", "")
        clean_v = vendor.split(" (")[0] if " (" in vendor else vendor
        key = f"{clean_v}|{rec.get('campaign', '')}".lower().strip()
        url_key = normalize_entry_url(rec.get("url", ""))
        if key in existing["names"] or (url_key and url_key in existing["urls"]):
            continue
        new_records.append(rec)
        # Guard against duplicates inside the same batch as well.
        existing["names"].add(key)
        if url_key:
            existing["urls"].add(url_key)

    if not new_records:
        print("所有记录已存在于多维表格中，无需同步")
        return 0

    print(f"发现 {len(new_records)} 条新记录待同步:")
    for rec in new_records:
        print(f"  - [{rec.get('vendor')}] {rec.get('campaign')}")

    if dry_run:
        print("\n[DRY RUN] 以上记录将被同步，但未实际写入")
        return len(new_records)

    created = 0
    for rec in new_records:
        fields = jsonl_record_to_bitable_fields(rec)
        try:
            create_record(fields, base_token, table_id)
            created += 1
            print(f"  ✅ 已写入: {rec.get('campaign', '')[:50]}")
        except Exception as e:
            print(f"  ❌ 写入失败: {e}")

    print(f"\n同步完成: {created}/{len(new_records)} 条新记录已写入多维表格")
    return created


# Fields that agent can override via --write JSON
OVERRIDE_FIELDS = (
    "活动类型", "难度评级", "难度说明", "奖励详情", "活动形式",
    "参与方式", "获奖条件", "时间节点备注", "官方确认", "状态",
    "地区", "奖励类型", "来源渠道", "预计投入", "截止时间",
    "开始时间", "建议",
)


def write_single(json_str, base_token=None, table_id=None):
    """Write a single record directly (used by agent after scanning)."""
    rec = json.loads(json_str)
    base_token, table_id = resolve_target(base_token, table_id)

    # Check dedup
    existing = list_existing_campaigns(base_token, table_id)
    vendor = rec.get("vendor", "")
    clean_v = vendor.split(" (")[0] if " (" in vendor else vendor
    key = f"{clean_v}|{rec.get('campaign', '')}".lower().strip()
    if key in existing["names"]:
        print(f"SKIP: 记录已存在 - {rec.get('campaign', '')}")
        return
    url_key = normalize_entry_url(rec.get("url", ""))
    if url_key and url_key in existing["urls"]:
        print(f"SKIP: 报名入口已存在（跨源重复） - {rec.get('campaign', '')} @ {url_key}")
        return

    # Build fields with defaults, then apply overrides
    fields = jsonl_record_to_bitable_fields(rec)
    for k in OVERRIDE_FIELDS:
        if k in rec and rec[k]:
            fields[k] = rec[k]
    if rec.get("推荐指数"):
        fields["推荐指数"] = score_to_stars(rec["推荐指数"])

    result = create_record(fields, base_token, table_id)
    rid = result.get("data", {}).get("records", [{}])[0].get("record_id", "")
    print(f"OK: {rid} - {rec.get('campaign', '')}")


def main():
    parser = argparse.ArgumentParser(description="Sync campaign data to Feishu Bitable")
    parser.add_argument("--dry", action="store_true", help="Dry run")
    parser.add_argument("--write", type=str, help="Write a single record (JSON)")
    parser.add_argument("--base-token", help=f"Feishu Base token, or {BASE_TOKEN_ENV}")
    parser.add_argument("--table-id", help=f"Feishu table ID/name, or {TABLE_ID_ENV}; defaults to bundled table")
    args = parser.parse_args()

    if args.write:
        write_single(args.write, args.base_token, args.table_id)
    else:
        sync_all(dry_run=args.dry, base_token=args.base_token, table_id=args.table_id)


if __name__ == "__main__":
    main()
