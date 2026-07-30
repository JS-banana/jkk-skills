#!/usr/bin/env python3
"""
AgentDeadlines JSON-LD Parser — Extract active/upcoming unseen AI campaigns.

Usage:
  python3 scripts/parse_agentdeadlines.py [--html /tmp/agentdeadlines.html] [--seen ~/.hermes/scripts/vendor_campaign_seen.jsonl]

Outputs JSON array of candidate campaigns sorted by urgency (days_left ascending).
Each item: {name, url, start, end, days_left, desc}

Designed to be called from cron agent sessions after fetching AgentDeadlines HTML via curl.
The HTML must already be downloaded — this script reads from disk (no network calls).

Workflow:
  1. curl -sL --max-time 20 "https://agentdeadlines.com" -H "User-Agent: Mozilla/5.0" -o /tmp/agentdeadlines.html
  2. python3 ~/.hermes/skills/research/find-bounty/scripts/parse_agentdeadlines.py
  3. Review JSON output for candidates worth investigating further
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone


def parse_args():
    p = argparse.ArgumentParser(description="Parse AgentDeadlines JSON-LD for unseen campaigns")
    p.add_argument("--html", default="/tmp/agentdeadlines.html", help="Path to downloaded HTML")
    p.add_argument("--seen",
                   default=os.path.expanduser(
                       os.environ.get("AI_CAMPAIGN_SEEN_FILE",
                                      "~/.hermes/scripts/vendor_campaign_seen.jsonl")),
                   help="Path to seen records JSONL (env: AI_CAMPAIGN_SEEN_FILE)")
    p.add_argument("--include-expired", action="store_true", help="Include expired campaigns")
    p.add_argument("--json", action="store_true", help="Output raw JSON (default: human-readable)")
    return p.parse_args()


def load_seen_urls(path):
    """Load already-seen campaign URLs from JSONL."""
    urls = set()
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    url = rec.get("url", "").rstrip("/")
                    if url:
                        urls.add(url)
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        pass
    return urls


def extract_jsonld(html_path):
    """Extract JSON-LD itemListElement from AgentDeadlines HTML."""
    with open(html_path) as f:
        html = f.read()

    jsonld_blocks = re.findall(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
        html, re.DOTALL
    )
    if not jsonld_blocks:
        print("ERROR: No JSON-LD found in HTML", file=sys.stderr)
        sys.exit(1)

    data = json.loads(jsonld_blocks[0])
    return data.get("itemListElement", [])


def parse_date(date_str):
    """Parse ISO date string to timezone-aware datetime, or None."""
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def main():
    args = parse_args()
    today = datetime.now(timezone.utc)
    seen_urls = load_seen_urls(args.seen)
    items = extract_jsonld(args.html)

    results = []
    for item in items:
        name = item.get("name", "")
        url = item.get("url", "").rstrip("/")
        start = item.get("startDate", "")
        end = item.get("endDate", "")
        desc = item.get("description", "")

        end_dt = parse_date(end)

        # Filter expired unless --include-expired
        if not args.include_expired and end_dt and end_dt < today:
            continue

        # Filter already seen
        if url in seen_urls:
            continue

        days_left = None
        if end_dt:
            days_left = (end_dt - today).days

        results.append({
            "name": name,
            "url": url,
            "start": start,
            "end": end,
            "days_left": days_left,
            "desc": desc[:300],
        })

    # Sort by urgency (fewest days first, None last)
    results.sort(key=lambda x: x["days_left"] if x["days_left"] is not None else 9999)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(f"Total items: {len(items)}, Active/upcoming & unseen: {len(results)}")
        print()
        for r in results:
            urgency = f"{r['days_left']}d left" if r['days_left'] is not None else "no end date"
            print(f"[{urgency}] {r['name']}")
            print(f"  URL: {r['url']}")
            print(f"  Start: {r['start']} | End: {r['end']}")
            if r['desc']:
                print(f"  Desc: {r['desc']}")
            print()


if __name__ == "__main__":
    main()
