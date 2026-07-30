#!/usr/bin/env python3
"""Collect read-only Git-history evidence for codebase orientation."""

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import PurePosixPath


DEFAULT_FIX_PATTERN = r"\b(fix(e[ds])?|bugs?|bugfix|broken)\b|修复|故障"
DEFAULT_CRISIS_PATTERN = r"\b(revert(ed)?|hotfix|emergency|rollback)\b|回滚|热修"
RECORD = b"\x1e"
FIELD = b"\x1f"


def run_git(repo, *args, binary=False, allow_failure=False):
    result = subprocess.run(
        ["git", "-C", repo, *args], capture_output=True, text=not binary
    )
    if result.returncode and not allow_failure:
        error = result.stderr.decode(errors="replace") if binary else result.stderr
        raise SystemExit(error.strip() or f"git {' '.join(args)} failed")
    if result.returncode:
        return None
    return result.stdout


def decode(value):
    return value.decode("utf-8", errors="replace")


def parse_history(raw):
    commits = []
    for chunk in raw.split(RECORD)[1:]:
        fields = chunk.split(b"\0")
        metadata = fields[0].split(FIELD, 4)
        if len(metadata) != 5:
            raise SystemExit("unexpected git log record")
        paths = fields[1:]
        if paths and paths[0].startswith(b"\n"):
            paths[0] = paths[0][1:]
        commits.append(
            {
                "hash": decode(metadata[0]),
                "author_name": decode(metadata[1]),
                "author_email": decode(metadata[2]),
                "committed_at": decode(metadata[3]),
                "subject": decode(metadata[4]),
                "paths": [decode(path) for path in paths if path],
            }
        )
    return commits


def ranked(counter, limit, label="path"):
    return [
        {label: key, "touches": count}
        for key, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))[
            :limit
        ]
    ]


def directory_bucket(path):
    directories = PurePosixPath(path).parts[:-1]
    return "/".join(directories[:3]) if directories else "."


def looks_noisy(path):
    parts = tuple(part.lower() for part in PurePosixPath(path).parts)
    name = parts[-1] if parts else ""
    return (
        name in {"changelog", "changelog.md", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "cargo.lock", "composer.lock"}
        or name.endswith((".min.js", ".min.css", ".map", ".pb.go", ".generated.ts"))
        or any(part in {"dist", "generated", "vendor"} for part in parts[:-1])
    )


def compile_pattern(value, label):
    try:
        return re.compile(value, re.IGNORECASE)
    except re.error as error:
        raise SystemExit(f"invalid {label} regex: {error}") from error


def consolidate_contributors(rows, limit):
    by_email = {}
    for name, email, count in rows:
        bucket = by_email.setdefault(email.lower(), {"email": email, "names": Counter()})
        bucket["names"][name] += count

    contributors = []
    for bucket in by_email.values():
        names = bucket["names"]
        primary = min(names, key=lambda name: (-names[name], name))
        contributor = {
            "name": primary,
            "email": bucket["email"],
            "commits": sum(names.values()),
        }
        if len(names) > 1:
            contributor["aliases"] = sorted(names)
        contributors.append(contributor)
    return sorted(contributors, key=lambda item: (-item["commits"], item["email"]))[
        :limit
    ]


def shortlog_contributors(repo, paths, limit):
    args = ["shortlog", "-sne", "--no-merges", "HEAD"]
    if paths:
        args += ["--", *paths]
    output = run_git(repo, *args)
    rows = []
    pattern = re.compile(r"^\s*(\d+)\s+(.+)\s+<([^<>]+)>$")
    for line in output.splitlines():
        match = pattern.match(line)
        if match:
            rows.append(
                (match.group(2), match.group(3), int(match.group(1)))
            )
    return consolidate_contributors(rows, limit)


def analyze(args):
    root = run_git(args.repo, "rev-parse", "--show-toplevel").strip()
    head = run_git(root, "rev-parse", "HEAD").strip()
    branch = run_git(
        root, "symbolic-ref", "--short", "-q", "HEAD", allow_failure=True
    )
    branch = branch.strip() if branch else None
    shallow = run_git(root, "rev-parse", "--is-shallow-repository").strip() == "true"

    path_args = ["--", *args.path] if args.path else []
    tracked_raw = run_git(root, "ls-files", "-z", *path_args, binary=True)
    tracked = {decode(path) for path in tracked_raw.split(b"\0") if path}
    if not tracked:
        raise SystemExit("no tracked files matched the requested scope")

    log_args = [
        "log",
        "-z",
        "--no-merges",
        "--no-renames",
        f"--since={args.since}",
        "--format=%x1e%H%x1f%aN%x1f%aE%x1f%cI%x1f%s",
        "--name-only",
        "HEAD",
        *path_args,
    ]
    commits = parse_history(run_git(root, *log_args, binary=True))
    fix_pattern = compile_pattern(args.fix_pattern, "fix-pattern")
    crisis_pattern = compile_pattern(args.crisis_pattern, "crisis-pattern")

    changes = Counter()
    fixes = Counter()
    recent_contributors = Counter()
    months = Counter()
    crisis_commits = []
    excluded_touches = 0

    for commit in commits:
        current_paths = {path for path in commit["paths"] if path in tracked}
        excluded_touches += len(commit["paths"]) - len(current_paths)
        changes.update(current_paths)
        recent_contributors[(commit["author_name"], commit["author_email"])] += 1
        months[commit["committed_at"][:7]] += 1
        if fix_pattern.search(commit["subject"]):
            fixes.update(current_paths)
        if crisis_pattern.search(commit["subject"]):
            crisis_commits.append(
                {
                    "hash": commit["hash"][:12],
                    "date": commit["committed_at"][:10],
                    "subject": commit["subject"],
                }
            )

    directories = Counter()
    for path, count in changes.items():
        directories[directory_bucket(path)] += count

    change_top = ranked(changes, args.top)
    fix_top = ranked(fixes, args.top)
    overlap = sorted(
        set(item["path"] for item in change_top)
        & set(item["path"] for item in fix_top),
        key=lambda path: (-fixes[path], -changes[path], path),
    )
    noise = [item for item in change_top if looks_noisy(item["path"])]

    warnings = []
    if shallow:
        warnings.append({"code": "shallow_history", "detail": "Only fetched history was analyzed."})
    if excluded_touches:
        warnings.append(
            {
                "code": "historical_paths_excluded",
                "detail": f"{excluded_touches} touches referenced paths no longer tracked in this scope.",
            }
        )
    if not commits:
        warnings.append({"code": "empty_window", "detail": "No non-merge commits matched the window."})
    if commits and not fixes:
        warnings.append({"code": "no_fix_subjects", "detail": "No commit subjects matched the fix pattern."})
    if noise:
        warnings.append({"code": "noise_candidates", "detail": "Review noise_candidates before interpreting hotspots."})

    recent_people = consolidate_contributors(
        [(name, email, count) for (name, email), count in recent_contributors.items()],
        args.top,
    )
    reachable_args = ["rev-list", "--count", "HEAD", *path_args]
    dirty = bool(run_git(root, "status", "--porcelain", "-z", binary=True))

    return {
        "schema_version": 1,
        "repository": {
            "root": root,
            "branch": branch,
            "head": head,
            "shallow": shallow,
            "dirty": dirty,
        },
        "scope": {
            "revision": "HEAD",
            "since": args.since,
            "paths": args.path or ["."],
            "merges": "excluded",
            "date_basis": "committer",
            "ranking_limit": args.top,
            "touch_definition": "one touch per current tracked path per non-merge commit",
            "tracked_files": len(tracked),
        },
        "summary": {
            "reachable_commits": int(run_git(root, *reachable_args).strip()),
            "recent_non_merge_commits": len(commits),
            "historical_path_touches_excluded": excluded_touches,
        },
        "change_hotspots": change_top,
        "directory_hotspots": ranked(directories, args.top, "directory"),
        "contributors": {
            "recent": recent_people,
            "all_time": shortlog_contributors(root, args.path, args.top),
        },
        "fix_signal": {
            "subject_pattern": args.fix_pattern,
            "matching_commits": sum(
                bool(fix_pattern.search(commit["subject"])) for commit in commits
            ),
            "hotspots": fix_top,
            "overlap_with_change_hotspots": [
                {
                    "path": path,
                    "change_touches": changes[path],
                    "fix_touches": fixes[path],
                }
                for path in overlap
            ],
        },
        "activity_by_month": [
            {"month": month, "commits": months[month]} for month in sorted(months)
        ],
        "crisis_signal": {
            "subject_pattern": args.crisis_pattern,
            "matching_commits": len(crisis_commits),
            "commits": crisis_commits[: args.top],
        },
        "noise_candidates": noise,
        "warnings": warnings,
    }


def self_test():
    raw = (
        b"\x1eabc\x1fA\x1fa@example.com\x1f2026-01-02T03:04:05Z\x1ffix: bug\0"
        b"\nsrc/a.py\0odd\nname.py\0"
    )
    commit = parse_history(raw)[0]
    assert commit["paths"] == ["src/a.py", "odd\nname.py"]
    assert directory_bucket("src/a.py") == "src"
    assert directory_bucket("README.md") == "."
    assert looks_noisy("package-lock.json")
    assert consolidate_contributors(
        [("A", "same@example.com", 2), ("Alias", "same@example.com", 1)], 5
    )[0]["commits"] == 3
    print("self-test passed")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="target Git repository")
    parser.add_argument("--since", default="1 year ago", help="Git date expression")
    parser.add_argument("--path", action="append", default=[], help="repo-relative path scope; repeatable")
    parser.add_argument("--top", type=int, default=20, help="maximum rows per ranking")
    parser.add_argument("--fix-pattern", default=DEFAULT_FIX_PATTERN, help="regex matched against commit subjects")
    parser.add_argument("--crisis-pattern", default=DEFAULT_CRISIS_PATTERN, help="regex matched against commit subjects")
    parser.add_argument("--self-test", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.top < 1:
        parser.error("--top must be positive")
    return args


def main():
    args = parse_args()
    if args.self_test:
        self_test()
        return
    json.dump(analyze(args), sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
