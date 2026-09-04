#!/usr/bin/env python3
"""Mechanical health check for a Markdown knowledge base.

Finds the drift that accumulates silently and that an agent should never burn
context re-deriving by reading every page: dead links, orphan pages, index and
filesystem disagreement, malformed or missing frontmatter, an index that has
outgrown its load budget, pages whose underlying code has moved on, expired
pages, and superseded pages that do not point forward.

It deliberately does not judge content. Contradictions between pages, redundant
coverage, and pages filed under the wrong type need a reader, and the skill's
Lint mode hands those to the agent using this report as the starting point.

Usage:
    wiki_lint.py <wiki-root> [--json] [--types t1,t2] [--stale-days N] [--limit N]
                            [--project-root DIR] [--index-max-lines N] [--index-max-bytes N]

<wiki-root> is the wiki directory, i.e. the one holding index.md.
Exit status is 0 when no findings, 1 when findings exist, 2 on usage error.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path

RESERVED_NAMES = {"index.md", "log.md"}
SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__", ".obsidian"}


def is_reserved(rel: str) -> bool:
    """Reserved at any depth, so per-directory indexes are not held to the
    page rules they exist to organize."""
    return rel.rsplit("/", 1)[-1] in RESERVED_NAMES


def is_index(rel: str) -> bool:
    return rel.rsplit("/", 1)[-1] == "index.md"

# An index is only useful if it survives being loaded in full every time the
# knowledge base is opened. These mirror the budget Claude Code enforces on its
# own always-loaded memory index; past it, entries silently stop being read.
INDEX_MAX_LINES = 200
INDEX_MAX_BYTES = 25 * 1024

# Long pages get previewed rather than read whole, so they need their own map.
TOC_THRESHOLD_LINES = 100

# Two different questions get tracked in `status`, and one vocabulary cannot
# answer both: whether a finding was checked, and whether a choice was adopted.
# Collapsing them is what lets a thorough investigation read as a commitment.
EVIDENCE_STATUS = {"draft", "verified", "stale", "superseded", "archived"}
ADOPTION_STATUS = {"proposed", "accepted", "rejected", "superseded", "archived"}
ADOPTION_TYPES = {"decision"}

# Statuses that take a page out of circulation, for every vocabulary.
RETIRED_STATUS = {"archived", "superseded", "rejected"}

FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\s*(?:\r?\n|\Z)", re.DOTALL)
# Markdown inline links and bare reference definitions, ignoring images.
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
LOG_ENTRY_RE = re.compile(r"^##\s+\[(\d{4}-\d{2}-\d{2})\]\s+(\S+)\s*\|", re.MULTILINE)


# --------------------------------------------------------------------------
# Minimal frontmatter parsing
# --------------------------------------------------------------------------
def _scalar(raw: str):
    """Coerce a YAML scalar without pulling in a YAML dependency."""
    v = raw.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        if not inner:
            return []
        return [_scalar(p) for p in inner.split(",")]
    if v in {"true", "True"}:
        return True
    if v in {"false", "False"}:
        return False
    return v


def parse_frontmatter(text: str):
    """Return (fields, error). Handles flat keys, inline lists, block lists and
    one level of nesting, which covers everything the skill's schema asks for."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, "no YAML frontmatter block"

    fields: dict = {}
    stack: list[tuple[int, dict]] = [(-1, fields)]
    pending_list_key: str | None = None
    pending_list_indent = 0

    for line in m.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()

        if stripped.startswith("- "):
            if pending_list_key is None or indent < pending_list_indent:
                return None, f"unexpected list item: {stripped[:40]!r}"
            target = stack[-1][1]
            target.setdefault(pending_list_key, [])
            if isinstance(target[pending_list_key], list):
                target[pending_list_key].append(_scalar(stripped[2:]))
            continue

        if ":" not in stripped:
            return None, f"malformed line: {stripped[:40]!r}"

        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()

        key, _, rest = stripped.partition(":")
        key = key.strip()
        rest = rest.strip()
        container = stack[-1][1]

        if rest == "":
            child: dict = {}
            container[key] = child
            stack.append((indent, child))
            pending_list_key = key
            pending_list_indent = indent
        else:
            container[key] = _scalar(rest)
            pending_list_key = None

    # A key opened as a nested dict but only ever received list items resolves
    # to that list; an empty dict means the value was simply blank.
    def collapse(d: dict) -> dict:
        for k, v in list(d.items()):
            if isinstance(v, dict):
                if not v:
                    d[k] = None
                else:
                    collapse(v)
        return d

    return collapse(fields), None


def as_date(value) -> dt.date | None:
    if value is None:
        return None
    if isinstance(value, dict):
        value = value.get("at")
    if not isinstance(value, str):
        return None
    m = DATE_RE.search(value)
    if not m:
        return None
    try:
        return dt.date.fromisoformat(m.group(0))
    except ValueError:
        return None


# --------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------
def git_last_change(project_root: Path, patterns: list[str]) -> tuple[dt.date | None, str | None]:
    """Date of the newest commit touching any watched path, or (None, reason).

    A page about a specific module goes stale when that module changes, not when
    a calendar interval elapses, so this is the invalidation signal that matters
    for notes written against source code.
    """
    if not patterns:
        return None, "no patterns"
    try:
        proc = subprocess.run(
            ["git", "-C", str(project_root), "log", "-1", "--format=%cI", "--", *patterns],
            capture_output=True, text=True, timeout=20, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return None, f"git unavailable: {exc}"
    if proc.returncode != 0:
        return None, (proc.stderr.strip().splitlines() or ["git log failed"])[0]
    stamp = proc.stdout.strip()
    if not stamp:
        return None, "no commits touch the watched paths"
    parsed = as_date(stamp)
    return parsed, None if parsed else f"unparseable commit date {stamp!r}"


def has_toc(text: str) -> bool:
    """True when the page opens with something that maps its own contents."""
    body = FRONTMATTER_RE.sub("", text, count=1)
    head = body.splitlines()[:40]
    links = sum(1 for line in head if re.match(r"\s*(?:[-*+]|\d+\.)\s+\[.+\]\(#", line))
    if links >= 3:
        return True
    return any(re.match(r"\s*#{2,}\s*(table of contents|contents|toc|目录)\s*$",
                        line, re.IGNORECASE) for line in head)


@dataclass
class Page:
    path: Path
    rel: str
    text: str
    fields: dict | None = None
    fm_error: str | None = None
    outgoing: set[str] = field(default_factory=set)
    incoming: set[str] = field(default_factory=set)
    broken: list[str] = field(default_factory=list)


@dataclass
class Finding:
    check: str
    severity: str
    page: str
    detail: str


def collect_pages(root: Path) -> dict[str, Page]:
    pages: dict[str, Page] = {}
    for p in sorted(root.rglob("*.md")):
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        rel = p.relative_to(root).as_posix()
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            text = ""
            page = Page(path=p, rel=rel, text=text, fm_error=f"unreadable: {exc}")
            pages[rel] = page
            continue
        page = Page(path=p, rel=rel, text=text)
        page.fields, page.fm_error = parse_frontmatter(text)
        pages[rel] = page
    return pages


def resolve_links(root: Path, pages: dict[str, Page]) -> None:
    for rel, page in pages.items():
        base = page.path.parent
        for raw in LINK_RE.findall(page.text):
            target = raw.split("#", 1)[0].strip()
            if not target:
                continue
            low = target.lower()
            if low.startswith(("http://", "https://", "mailto:", "tel:", "data:", "//")):
                continue
            target = urllib.parse.unquote(target)
            if target.startswith("/"):
                candidate = (root / target.lstrip("/")).resolve()
            else:
                candidate = (base / target).resolve()

            try:
                t_rel = candidate.relative_to(root.resolve()).as_posix()
            except ValueError:
                page.broken.append(f"{raw} (escapes the knowledge base)")
                continue

            if candidate.exists():
                if t_rel in pages:
                    page.outgoing.add(t_rel)
                    pages[t_rel].incoming.add(rel)
                continue

            # Tolerate extension-less wiki-style links to an existing page.
            if not target.endswith(".md") and f"{t_rel}.md" in pages:
                page.outgoing.add(f"{t_rel}.md")
                pages[f"{t_rel}.md"].incoming.add(rel)
                continue

            page.broken.append(raw)


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------
def run_checks(root: Path, pages: dict[str, Page], types: set[str], stale_days: int,
               today: dt.date, project_root: Path, index_max_lines: int,
               index_max_bytes: int) -> list[Finding]:
    out: list[Finding] = []
    index = pages.get("index.md")

    if index is None:
        out.append(Finding("reserved-file", "error", "index.md",
                           "missing; the knowledge base has no entry point"))
    if "log.md" not in pages:
        out.append(Finding("reserved-file", "error", "log.md",
                           "missing; changes are not being recorded"))

    for rel, page in sorted(pages.items()):
        if not is_index(rel):
            continue
        lines = len(page.text.splitlines())
        size = len(page.text.encode("utf-8"))
        if lines > index_max_lines or size > index_max_bytes:
            out.append(Finding(
                "index-budget", "warning", rel,
                f"{lines} lines / {size} bytes exceeds the {index_max_lines}-line / "
                f"{index_max_bytes}-byte load budget; compact to one routing line per "
                f"entry and split into per-directory indexes"))

    for rel, page in sorted(pages.items()):
        for target in page.broken:
            out.append(Finding("dead-link", "error", rel, f"link target not found: {target}"))

        if is_reserved(rel):
            continue

        if page.fm_error:
            out.append(Finding("frontmatter", "error", rel, page.fm_error))
            continue

        fm = page.fields or {}
        ftype = fm.get("type")
        if not ftype:
            out.append(Finding("frontmatter", "error", rel, "missing required field `type`"))
        elif types and isinstance(ftype, str) and ftype not in types:
            out.append(Finding("frontmatter", "warning", rel,
                               f"type `{ftype}` is not one of the declared types "
                               f"({', '.join(sorted(types))})"))

        status = fm.get("status")
        if status == "superseded" and not page.outgoing:
            out.append(Finding("lifecycle", "warning", rel,
                               "marked superseded but links to no replacement"))

        adoption = isinstance(ftype, str) and ftype in ADOPTION_TYPES
        allowed = ADOPTION_STATUS if adoption else EVIDENCE_STATUS
        if status is None:
            if adoption:
                out.append(Finding(
                    "lifecycle", "warning", rel,
                    "decision has no adoption status; a decision nobody marked accepted "
                    "cannot be distinguished from one that was only proposed"))
        elif isinstance(status, str) and status not in allowed:
            other = EVIDENCE_STATUS if adoption else ADOPTION_STATUS
            hint = (" — that word belongs to the "
                    f"{'evidence' if adoption else 'adoption'} vocabulary, which tracks a "
                    f"different question") if status in other else ""
            out.append(Finding(
                "lifecycle", "warning", rel,
                f"status `{status}` is not valid for type `{ftype}` "
                f"(expected one of {', '.join(sorted(allowed))}){hint}"))

        updated = as_date(fm.get("updated") or fm.get("timestamp") or fm.get("generated"))
        if updated is None:
            out.append(Finding("frontmatter", "warning", rel,
                               "no parseable update date (`updated`, `timestamp` or `generated.at`)"))

        # `reviewed` records a human confirming the page; `updated` only records
        # the last agent write. Code drift is measured against the human date
        # when one exists, because an agent rewrite does not re-verify anything.
        reviewed = as_date(fm.get("reviewed"))
        watch = fm.get("watch")
        if isinstance(watch, str):
            watch = [watch]
        if watch:
            changed, reason = git_last_change(project_root, [str(w) for w in watch])
            baseline = reviewed or updated
            if reason:
                out.append(Finding("watch", "info", rel,
                                   f"cannot check watched paths: {reason}"))
            elif changed and baseline and changed > baseline:
                out.append(Finding(
                    "code-drift", "warning", rel,
                    f"watched code changed {changed.isoformat()}, after this page was last "
                    f"{'reviewed' if reviewed else 'updated'} {baseline.isoformat()}"))
            elif changed and not baseline:
                out.append(Finding("code-drift", "info", rel,
                                   "watches code but carries no date to compare against"))

        if len(page.text.splitlines()) > TOC_THRESHOLD_LINES and not has_toc(page.text):
            out.append(Finding("toc", "info", rel,
                               f"over {TOC_THRESHOLD_LINES} lines with no table of contents; "
                               f"a partial read will miss its scope"))

        expiry = as_date(fm.get("stale_after"))
        if expiry and expiry < today and status not in RETIRED_STATUS:
            out.append(Finding("stale", "warning", rel,
                               f"stale_after {expiry.isoformat()} has passed and status is "
                               f"`{status or 'unset'}`"))
        elif (updated and stale_days > 0 and status not in RETIRED_STATUS
              and (today - updated).days > stale_days):
            out.append(Finding("stale", "info", rel,
                               f"not updated in {(today - updated).days} days "
                               f"(last {updated.isoformat()})"))

        if ftype == "research" and not fm.get("sources"):
            out.append(Finding("provenance", "warning", rel,
                               "research page has no `sources` field"))

        if not page.incoming and status not in RETIRED_STATUS:
            out.append(Finding("orphan", "warning", rel,
                               "no page links here; unreachable except by search"))

    if index is not None:
        listed = set(index.outgoing)
        for rel in sorted(pages):
            if is_reserved(rel):
                continue
            page = pages[rel]
            status = (page.fields or {}).get("status")
            if rel not in listed and status not in RETIRED_STATUS:
                # A page reachable from a sub-index is fine; the root index only
                # has to reach it transitively.
                reachable = any(is_index(src) for src in page.incoming)
                if not reachable:
                    out.append(Finding("index-drift", "warning", rel,
                                       "on disk but not reachable from index.md or any sub-index"))

        for rel in sorted(pages):
            if rel == "index.md" or not is_index(rel):
                continue
            if not any(is_index(src) for src in pages[rel].incoming):
                out.append(Finding("index-drift", "error", rel,
                                   "sub-index is not linked from the root index; everything "
                                   "it routes to is unreachable by navigation"))

    log = pages.get("log.md")
    if log is not None:
        entries = LOG_ENTRY_RE.findall(log.text)
        if not entries:
            out.append(Finding("log-format", "warning", "log.md",
                               "no entries match `## [YYYY-MM-DD] <op> | <title>`"))
        else:
            dates = [dt.date.fromisoformat(d) for d, _ in entries]
            if dates != sorted(dates) and dates != sorted(dates, reverse=True):
                out.append(Finding("log-format", "info", "log.md",
                                   "entries are not in a consistent chronological order"))

    return out


SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", type=Path, help="wiki directory (the one holding index.md)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--types", default="",
                    help="comma-separated list of allowed `type` values from the project schema")
    ap.add_argument("--stale-days", type=int, default=0,
                    help="flag pages not updated in this many days (0 disables)")
    ap.add_argument("--limit", type=int, default=40,
                    help="max findings to print per check in text mode (0 for all)")
    ap.add_argument("--project-root", type=Path, default=None,
                    help="root that `watch` globs resolve against (default: the KB root)")
    ap.add_argument("--index-max-lines", type=int, default=INDEX_MAX_LINES,
                    help=f"index load budget in lines (default {INDEX_MAX_LINES})")
    ap.add_argument("--index-max-bytes", type=int, default=INDEX_MAX_BYTES,
                    help=f"index load budget in bytes (default {INDEX_MAX_BYTES})")
    ap.add_argument("--today", default="", help="override today's date, YYYY-MM-DD (for tests)")
    args = ap.parse_args(argv)

    root = args.root.expanduser()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    project_root = (args.project_root or root).expanduser()

    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    types = {t.strip() for t in args.types.split(",") if t.strip()}

    pages = collect_pages(root)
    resolve_links(root, pages)
    findings = run_checks(root, pages, types, args.stale_days, today,
                          project_root, args.index_max_lines, args.index_max_bytes)
    findings.sort(key=lambda f: (SEVERITY_ORDER.get(f.severity, 9), f.check, f.page))

    if args.json:
        print(json.dumps({
            "root": str(root),
            "pages": len(pages),
            "findings": [f.__dict__ for f in findings],
            "counts": {
                s: sum(1 for f in findings if f.severity == s)
                for s in ("error", "warning", "info")
            },
        }, ensure_ascii=False, indent=2))
        return 1 if findings else 0

    print(f"knowledge base: {root}")
    print(f"pages scanned: {len(pages)}")
    if not findings:
        print("no mechanical findings")
        return 0

    by_check: dict[str, list[Finding]] = {}
    for f in findings:
        by_check.setdefault(f.check, []).append(f)

    counts = {s: sum(1 for f in findings if f.severity == s)
              for s in ("error", "warning", "info")}
    print(f"findings: {counts['error']} error, {counts['warning']} warning, {counts['info']} info")
    for check, items in by_check.items():
        print(f"\n## {check} ({len(items)})")
        shown = items if args.limit == 0 else items[:args.limit]
        for f in shown:
            print(f"  [{f.severity}] {f.page}: {f.detail}")
        if len(items) > len(shown):
            print(f"  ... and {len(items) - len(shown)} more")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
