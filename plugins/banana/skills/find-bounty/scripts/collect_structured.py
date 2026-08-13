#!/usr/bin/env python3
"""
find-bounty structured source collector — one call, all endpoints.

Fetches AgentDeadlines (JSON-LD), Devpost (JSON API, all pages),
CompeteHub (current + next month), and aihot.today (RSC → Jina fallback)
in parallel, then outputs unified JSON.

Usage:
  python3 scripts/collect_structured.py [--output /tmp/find-bounty-structured.json]
                                        [--current-month 2026-07]
                                        [--skip agentdeadlines|devpost|competehub|aihot]

Exit codes:
  0 — all sources OK or at least one source succeeded
  1 — all sources failed

Output JSON structure:
{
  "collected_at": "2026-07-30T...",
  "sources": {
    "agentdeadlines": {"ok": true, "count": 16, "candidates": [...]},
    "devpost":        {"ok": true, "count": 32, "candidates": [...]},
    "competehub":     {"ok": true, "count": 258, "candidates": [...], "months": ["2026-07","2026-08"]},
    "aihot":          {"ok": false, "error": "RSC extraction failed", "fallback_tried": "jina"}
  },
  "total_candidates": 306
}

Dependencies: stdlib + curl + existing parse scripts in the same skill directory.
No hermes_tools or execute_code imports — compatible with Hermes cron mode.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
CURL_TIMEOUT = 20
DDG_TIMEOUT = 15


# ─── helpers ──────────────────────────────────────────────────────────

def curl(url: str, output: str, headers: dict | None = None, timeout: int = CURL_TIMEOUT) -> bool:
    """Download a URL to a file. Returns True on success."""
    cmd = ["curl", "-sL", "--max-time", str(timeout), "-o", output]
    cmd.extend(["-H", f"User-Agent: {UA}"])
    if headers:
        for k, v in headers.items():
            cmd.extend(["-H", f"{k}: {v}"])
    cmd.append(url)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
    if result.returncode != 0:
        return False
    try:
        return os.path.getsize(output) > 500
    except OSError:
        return False


def run_script(script_name: str, *args) -> tuple[bool, str]:
    """Run a skill script. Returns (ok, stdout)."""
    script_path = SKILL_DIR / "scripts" / script_name
    cmd = ["python3", str(script_path), *args]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result.returncode == 0, result.stdout.strip()


# ─── AgentDeadlines ────────────────────────────────────────────────────

def collect_agentdeadlines(tmpdir: str) -> dict:
    """Fetch and parse AgentDeadlines JSON-LD."""
    html_path = os.path.join(tmpdir, "agentdeadlines.html")
    ok = curl("https://agentdeadlines.com", html_path)
    if not ok:
        return {"ok": False, "error": "curl failed", "candidates": [], "count": 0}

    ok, stdout = run_script("parse_agentdeadlines.py", "--html", html_path, "--json")
    if not ok:
        return {"ok": False, "error": f"parse failed: {stdout[:200]}", "candidates": [], "count": 0}

    try:
        candidates = json.loads(stdout)
    except json.JSONDecodeError:
        return {"ok": False, "error": "parse output not valid JSON", "candidates": [], "count": 0}

    # Tag source
    for c in candidates:
        c["_source"] = "AgentDeadlines"

    return {"ok": True, "candidates": candidates, "count": len(candidates)}


# ─── Devpost ──────────────────────────────────────────────────────────

def collect_devpost(tmpdir: str) -> dict:
    """Fetch all pages of Devpost open AI hackathons."""
    base_url = (
        "https://devpost.com/api/hackathons"
        "?challenge_type[]=online&status[]=open&themes[]=Machine%20Learning%2FAI"
    )
    all_candidates = []
    page = 1

    # Fetch page 1 to discover total count
    p1_path = os.path.join(tmpdir, f"devpost_p1.json")
    ok = curl(f"{base_url}&page=1", p1_path)
    if not ok:
        return {"ok": False, "error": "page 1 curl failed", "candidates": [], "count": 0}

    try:
        with open(p1_path) as f:
            d = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"ok": False, "error": "page 1 not valid JSON", "candidates": [], "count": 0}

    total = d.get("meta", {}).get("total_count", 0)
    per_page = len(d.get("hackathons", [])) or 9
    total_pages = max(1, -(-total // per_page))  # ceiling division

    for h in d.get("hackathons", []):
        all_candidates.append(_normalize_devpost(h))

    # Fetch remaining pages
    for p in range(2, total_pages + 1):
        p_path = os.path.join(tmpdir, f"devpost_p{p}.json")
        ok = curl(f"{base_url}&page={p}", p_path)
        if not ok:
            continue
        try:
            with open(p_path) as f:
                pd = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        for h in pd.get("hackathons", []):
            all_candidates.append(_normalize_devpost(h))

    return {"ok": True, "candidates": all_candidates, "count": len(all_candidates), "pages_fetched": total_pages}


def _normalize_devpost(h: dict) -> dict:
    """Extract key fields from a Devpost hackathon dict."""
    prize_html = h.get("prize_amount", "") or ""
    prize_usd = 0
    nums = re.findall(r"[\d,]+\.?\d*", prize_html.replace(",", ""))
    if nums:
        try:
            prize_usd = float(nums[0].replace(",", ""))
        except ValueError:
            pass

    deadline_text = h.get("submission_period_dates", "") or ""
    dl_parts = deadline_text.split(" - ")
    end_str = dl_parts[-1].strip() if len(dl_parts) >= 2 else deadline_text.strip()

    return {
        "_source": "Devpost",
        "title": h.get("title", ""),
        "url": h.get("url", ""),
        "prize_usd": prize_usd,
        "prize_text": re.sub(r"<[^>]+>", "", prize_html).strip(),
        "deadline_text": deadline_text,
        "deadline_end_str": end_str,
        "desc": (h.get("description", "") or "")[:300],
        "themes": [t.get("name", "") for t in (h.get("themes") or [])],
    }


# ─── CompeteHub ───────────────────────────────────────────────────────

def collect_competehub(tmpdir: str, current_month: str) -> dict:
    """Fetch CompeteHub monthly pages for current and next month."""
    candidates = []
    months_fetched = []

    # Parse YYYY-MM
    parts = current_month.split("-")
    year, month = int(parts[0]), int(parts[1])

    for offset in (0, 1):
        m = month + offset
        y = year
        if m > 12:
            m -= 12
            y += 1
        month_str = f"{y:04d}-{m:02d}"

        html_path = os.path.join(tmpdir, f"competehub_{month_str}.html")
        ok = curl(f"https://competehub.dev/zh/monthly/{month_str}", html_path)
        if not ok:
            continue

        ok, stdout = run_script("parse_competehub.py", "--html", html_path, "--json")
        if not ok:
            continue

        try:
            page_candidates = json.loads(stdout)
        except json.JSONDecodeError:
            continue

        for c in page_candidates:
            c["_source"] = "CompeteHub"
            c["_month"] = month_str
            # Normalize prize
            prize_str = c.get("prize", "") or ""
            c["_prize_usd"] = _parse_cny_prize(prize_str)

        candidates.extend(page_candidates)
        months_fetched.append(month_str)

    return {
        "ok": len(candidates) > 0,
        "candidates": candidates,
        "count": len(candidates),
        "months": months_fetched,
    }


def _parse_cny_prize(prize_str: str) -> int:
    """Rough CNY→USD conversion for sorting. Returns 0 on failure."""
    if not prize_str or "¥" not in prize_str:
        return 0
    nums = re.findall(r"[\d,]+\.?\d*", prize_str.replace(",", "").replace("¥", ""))
    if not nums:
        return 0
    try:
        return round(float(nums[0].replace(",", "")) / 7.2)
    except ValueError:
        return 0


# ─── aihot.today ──────────────────────────────────────────────────────

def collect_aihot(tmpdir: str) -> dict:
    """Fetch aihot.today with RSC extraction, fallback to Jina Reader."""
    html_path = os.path.join(tmpdir, "aihot.html")

    # Primary: direct curl
    ok = curl("https://aihot.today/ai-event", html_path)
    if not ok:
        return _aihot_jina_fallback()

    # Try RSC extraction
    try:
        with open(html_path) as f:
            content = f.read()
    except OSError:
        return _aihot_jina_fallback()

    candidates = _extract_aihot_rsc(content)
    if candidates:
        for c in candidates:
            c["_source"] = "aihot.today"
        return {"ok": True, "candidates": candidates, "count": len(candidates), "method": "rsc"}

    # Fallback: Jina Reader
    return _aihot_jina_fallback()


def _extract_aihot_rsc(content: str) -> list[dict]:
    """Try to extract events from aihot RSC payload."""
    # Look for self.__next_f.push patterns with event data
    candidates = []

    # Method 1: __NEXT_DATA__
    m = re.search(r"__NEXT_DATA__\s*=\s*(\{.*?\});", content, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(1))
            # Navigate to find event data
            props = data.get("props", {}).get("pageProps", {})
            events = props.get("events", props.get("data", []))
            if isinstance(events, list):
                for e in events:
                    if isinstance(e, dict):
                        candidates.append({
                            "title": e.get("title", e.get("name", "")),
                            "url": e.get("url", ""),
                            "date_start": e.get("startDate", e.get("start_date", "")),
                            "date_end": e.get("endDate", e.get("end_date", "")),
                            "city": e.get("city", ""),
                            "status": e.get("status", ""),
                            "desc": (e.get("description", "") or "")[:200],
                        })
                return candidates
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    # Method 2: self.__next_f.push arrays (RSC payload)
    # Try to find JSON arrays that look like event lists
    pushes = re.findall(r"self\.__next_f\.push\(\d+,\s*(\[.*?\])\s*\)", content)
    for push in pushes:
        try:
            data = json.loads(push)
            # Walk the array looking for objects with title/name fields
            _walk_for_events(data, candidates)
        except json.JSONDecodeError:
            continue

    return candidates


def _walk_for_events(obj, candidates: list, depth: int = 0):
    """Recursively walk a JSON structure looking for event-like objects."""
    if depth > 5:
        return
    if isinstance(obj, dict):
        title = obj.get("title") or obj.get("name") or obj.get("eventName")
        if title and isinstance(title, str) and len(title) > 2:
            candidates.append({
                "title": title,
                "url": obj.get("url", obj.get("link", "")),
                "date_start": str(obj.get("startDate", obj.get("start_date", ""))),
                "date_end": str(obj.get("endDate", obj.get("end_date", ""))),
                "city": obj.get("city", obj.get("location", "")),
                "status": obj.get("status", ""),
                "desc": str(obj.get("description", obj.get("desc", "")))[:200],
            })
        for v in obj.values():
            _walk_for_events(v, candidates, depth + 1)
    elif isinstance(obj, list):
        for item in obj[:200]:  # limit recursion
            _walk_for_events(item, candidates, depth + 1)


def _aihot_jina_fallback() -> dict:
    """Fallback: use Jina Reader to extract aihot content."""
    jina_path = "/tmp/aihot_jina.md"
    ok = curl(
        "https://r.jina.ai/https://aihot.today/ai-event",
        jina_path,
        headers={"Accept": "text/markdown"},
    )
    if not ok:
        return {"ok": False, "error": "RSC failed, Jina fallback also failed", "candidates": [], "count": 0, "method": "jina_failed"}

    try:
        with open(jina_path) as f:
            content = f.read()
    except OSError:
        return {"ok": False, "error": "Jina output unreadable", "candidates": [], "count": 0, "method": "jina_failed"}

    # Extract event-like entries from markdown
    candidates = []
    lines = content.split("\n")
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Look for date patterns + event descriptions
        if re.search(r"\d{4}[-/]\d{1,2}", line) and len(line) > 15:
            candidates.append({
                "title": line[:120],
                "url": "",
                "desc": line[:200],
                "_source": "aihot.today",
            })

    return {
        "ok": len(candidates) > 0,
        "candidates": candidates,
        "count": len(candidates),
        "method": "jina_fallback",
    }


# ─── main ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Batch collect structured AI campaign sources")
    parser.add_argument("--output", default="/tmp/find-bounty-structured.json", help="Output JSON path")
    parser.add_argument("--current-month", default=None, help="YYYY-MM for CompeteHub monthly page (default: current month)")
    parser.add_argument("--skip", default="", help="Comma-separated sources to skip: agentdeadlines,devpost,competehub,aihot")
    args = parser.parse_args()

    current_month = args.current_month or datetime.now(timezone.utc).strftime("%Y-%m")
    skip = set(s.strip().lower() for s in args.skip.split(",") if s.strip())
    tmpdir = "/tmp"

    collected_at = datetime.now(timezone.utc).isoformat()
    sources = {}

    # Define tasks
    tasks = {}
    if "agentdeadlines" not in skip:
        tasks["agentdeadlines"] = lambda: collect_agentdeadlines(tmpdir)
    if "devpost" not in skip:
        tasks["devpost"] = lambda: collect_devpost(tmpdir)
    if "competehub" not in skip:
        tasks["competehub"] = lambda: collect_competehub(tmpdir, current_month)
    if "aihot" not in skip:
        tasks["aihot"] = lambda: collect_aihot(tmpdir)

    # Parallel execution
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(fn): name for name, fn in tasks.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                sources[name] = future.result()
            except Exception as e:
                sources[name] = {"ok": False, "error": str(e), "candidates": [], "count": 0}

    # Compute total
    total = sum(s.get("count", 0) for s in sources.values())
    any_ok = any(s.get("ok") for s in sources.values())

    result = {
        "collected_at": collected_at,
        "current_month": current_month,
        "sources": sources,
        "total_candidates": total,
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Summary to stdout
    print(f"Collected {total} candidates from {len(sources)} sources:")
    for name, src in sources.items():
        status = "✅" if src.get("ok") else "❌"
        count = src.get("count", 0)
        extra = ""
        if name == "competehub":
            extra = f" (months: {src.get('months', [])})"
        elif name == "aihot" and not src.get("ok"):
            extra = f" (method: {src.get('method', '?')})"
        print(f"  {status} {name}: {count}{extra}")

    if not any_ok:
        print("\n❌ All sources failed.", file=sys.stderr)
        sys.exit(1)

    print(f"\n→ {args.output}")


if __name__ == "__main__":
    main()
