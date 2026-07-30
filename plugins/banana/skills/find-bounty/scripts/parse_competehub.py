#!/usr/bin/env python3
"""
CompeteHub (AI赛事通) RSC Parser — Extract competitions from monthly page HTML.

Usage:
  python3 scripts/parse_competehub.py [--html /tmp/competehub-monthly.html] [--seen ~/.hermes/scripts/vendor_campaign_seen.jsonl]

Outputs competitions: {slug, title, url, prize, dates, status}, filtered to
进行中/即将开始 and unseen, sorted by prize descending.

Why this parser exists: competehub.dev/zh/competitions (the list page) renders
competition rows CLIENT-SIDE — curl of that page yields only UI strings, and no
regex will ever find competition data there. The monthly page
/zh/monthly/YYYY-MM DOES server-render all rows inside Next.js RSC payload
chunks (self.__next_f.push). This script reassembles those chunks and pairs
each /zh/competitions/{slug} href with its nearby title/prize/date/status.

Workflow:
  1. curl -s -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36" \
       "https://competehub.dev/zh/monthly/$(date +%Y-%m)" -o /tmp/competehub-monthly.html
  2. python3 scripts/parse_competehub.py --html /tmp/competehub-monthly.html
  3. Review output; fetch /zh/competitions/{slug} detail pages only for shortlisted candidates.
"""

import argparse
import json
import os
import re
import sys


def parse_args():
    p = argparse.ArgumentParser(description="Parse CompeteHub monthly page RSC for competitions")
    p.add_argument("--html", default="/tmp/competehub-monthly.html", help="Path to downloaded HTML")
    p.add_argument("--seen",
                   default=os.path.expanduser(
                       os.environ.get("AI_CAMPAIGN_SEEN_FILE",
                                      "~/.hermes/scripts/vendor_campaign_seen.jsonl")),
                   help="Path to seen records JSONL (env: AI_CAMPAIGN_SEEN_FILE)")
    p.add_argument("--include-ended", action="store_true", help="Include 已结束 competitions")
    p.add_argument("--json", action="store_true", help="Output raw JSON (default: human-readable)")
    return p.parse_args()


def load_seen_urls(path):
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


def reassemble_rsc(html_path):
    """Join and unescape all Next.js RSC payload chunks into one string."""
    with open(html_path, encoding="utf-8") as f:
        html = f.read()
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)', html)
    if not chunks:
        print("ERROR: No RSC chunks found — wrong page or blocked (need browser UA)", file=sys.stderr)
        sys.exit(1)
    return "".join(
        c.encode("utf-8").decode("unicode_escape").encode("latin-1", "ignore").decode("utf-8", "ignore")
        for c in chunks
    )


def prize_to_number(prize):
    """'¥144万' -> 1440000, '$10,800' -> 10800; None -> 0. For sorting only."""
    if not prize:
        return 0
    m = re.match(r"[¥$€£]([\d,.]+)([万kKMB]?)", prize)
    if not m:
        return 0
    num = float(m.group(1).replace(",", ""))
    mult = {"万": 10_000, "k": 1_000, "K": 1_000, "M": 1_000_000, "B": 1_000_000_000}
    return num * mult.get(m.group(2), 1)


def extract_competitions(blob):
    """Pair each competition href with nearby title/prize/dates/status."""
    hrefs = list(re.finditer(r'"href":"/zh/competitions/([a-z0-9_-]+)"', blob))
    comps = {}
    for i, m in enumerate(hrefs):
        slug = m.group(1)
        window = blob[m.end():hrefs[i + 1].start() if i + 1 < len(hrefs) else m.end() + 8000]
        alts = re.findall(r'"alt":"([^"]+)"', blob[max(0, m.start() - 1500):m.start()])
        money = re.findall(r"[¥$€£][\d,.]+[万kKMB]?", window)
        dates = ["{}-{:02d}-{:02d}".format(y, int(mo), int(d))
                 for y, mo, d in re.findall(r"(\d{4})年(\d{1,2})月(\d{1,2})日?", window)[:2]]
        status = next((w for w in ["进行中", "即将开始", "已结束"] if w in window), None)
        rec = {
            "slug": slug,
            "title": alts[-1] if alts else None,
            "url": f"https://competehub.dev/zh/competitions/{slug}",
            "prize": money[0] if money else None,
            "dates": dates,
            "status": status,
        }
        # The same competition appears in several interleaved views; keep the richest row.
        richness = lambda r: sum(1 for v in (r["title"], r["prize"], r["status"]) if v) + len(r["dates"])
        if slug not in comps or richness(rec) > richness(comps[slug]):
            comps[slug] = rec
    return list(comps.values())


def main():
    args = parse_args()
    seen_urls = load_seen_urls(args.seen)
    blob = reassemble_rsc(args.html)
    comps = extract_competitions(blob)
    total = len(comps)

    results = [
        c for c in comps
        if (args.include_ended or c["status"] != "已结束")
        and c["url"] not in seen_urls
    ]
    results.sort(key=lambda c: prize_to_number(c["prize"]), reverse=True)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(f"Total rows: {total}, Active/upcoming & unseen: {len(results)}")
        print()
        for r in results:
            prize = r["prize"] or "无奖金信息"
            dates = " ~ ".join(r["dates"]) if r["dates"] else "无日期"
            print(f"[{r['status'] or '状态未知'}] {r['title']} | {prize} | {dates}")
            print(f"  URL: {r['url']}")
            print()


if __name__ == "__main__":
    main()
