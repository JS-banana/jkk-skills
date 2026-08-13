#!/usr/bin/env python3
"""Validate the write-readme skill package or a generated README."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_REFERENCES = [
    "references/method.md",
    "references/patterns.md",
    "references/presentation.md",
    "references/review-rubric.md",
    "references/badges.md",
    "references/examples.md",
]

FORBIDDEN_SKILL_FILES = [
    "references/README-anatomy.md",
    "references/badge-catalog.md",
    "references/project-patterns.md",
    "references/scoring-rubric.md",
    "references/writing-principles.md",
    "assets/templates/brand-focused.md",
    "assets/templates/complete-manual.md",
    "assets/templates/minimal-facade.md",
    "assets/templates/operation-manual.md",
    "assets/templates/standard-framework.md",
    "assets/templates/cli.md",
    "assets/templates/library.md",
    "assets/templates/web-app.md",
    "assets/templates/service.md",
    "assets/templates/personal-tool.md",
    "assets/templates/monorepo.md",
]

# Unresolved template syntax. Outside a code block these are always defects;
# inside one they may be documented template variables, so they only warn.
TEMPLATE_PLACEHOLDERS = [
    ("template variable", r"\{\{[^}]+\}\}"),
    ("owner placeholder", r"\{owner\}"),
    ("repo placeholder", r"\{repo\}"),
    ("sample repo slug", r"\buser/repo\b"),
    ("sample project name", r"Project Name"),
]

# Context-dependent markers: legitimate as environment variables, Roadmap
# headings, or documented substitutions. Always reported as warnings so the
# reviewer judges each hit instead of chasing a false failure.
AMBIGUOUS_MARKERS = [
    ("owner placeholder", r"\bOWNER\b"),
    ("repo placeholder", r"\bREPO\b"),
    ("unfinished marker", r"\bTODO\b"),
    ("unfinished marker", r"\bFIXME\b"),
]

# Badge URLs are the one place OWNER/REPO is never legitimate.
BADGE_PLACEHOLDER_PATTERNS = [
    r"img\.shields\.io/[^)\s\"']*(\{|\}|OWNER|REPO|user/repo)",
    r"github\.com/(OWNER|\{owner\}|user)/(REPO|\{repo\}|repo)/",
]

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_frontmatter(content: str) -> dict[str, str] | None:
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None
    data: dict[str, str] = {}
    key = None
    buffer: list[str] = []
    for line in match.group(1).splitlines():
        if re.match(r"^[a-zA-Z0-9_-]+:\s*", line):
            if key:
                data[key] = "\n".join(buffer).strip()
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value in {">", "|"}:
                buffer = []
            else:
                buffer = [value.strip('"')]
        elif key:
            buffer.append(line.strip())
    if key:
        data[key] = " ".join(part for part in buffer if part).strip()
    return data


def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return ["missing SKILL.md"]

    content = read(skill_md)
    frontmatter = extract_frontmatter(content)
    if not frontmatter:
        errors.append("SKILL.md frontmatter is missing or invalid")
    else:
        name = frontmatter.get("name", "")
        description = frontmatter.get("description", "")
        if name != "write-readme":
            errors.append("SKILL.md name must be write-readme")
        if "Use when" not in description:
            errors.append("description must include trigger wording")
        if len(description) > 1024:
            errors.append("description exceeds 1024 characters")
        if "<" in description or ">" in description:
            errors.append("description must not contain angle brackets")

    lines = content.splitlines()
    if len(lines) > 110:
        errors.append(f"SKILL.md is too long ({len(lines)} lines; target <= 110)")

    required_mentions = REQUIRED_REFERENCES + ["scripts/validate.py"]
    for rel in required_mentions:
        if rel not in content:
            errors.append(f"SKILL.md does not mention {rel}")

    for rel in REQUIRED_REFERENCES:
        if not (skill_dir / rel).exists():
            errors.append(f"missing required file: {rel}")

    for rel in FORBIDDEN_SKILL_FILES:
        if (skill_dir / rel).exists():
            errors.append(f"obsolete file still present: {rel}")

    return errors


def markdown_headings(content: str) -> list[tuple[int, str]]:
    headings: list[tuple[int, str]] = []
    in_block = False
    for line in content.splitlines():
        if re.match(r"^```", line):
            in_block = not in_block
            continue
        if in_block:
            continue
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            headings.append((len(match.group(1)), match.group(2)))
    html_h1 = re.findall(r"<h1[^>]*>(.*?)</h1>", content, flags=re.IGNORECASE | re.DOTALL)
    headings.extend((1, re.sub(r"<.*?>", "", h).strip()) for h in html_h1)
    return headings


def code_block_languages(content: str) -> tuple[int, int]:
    total = 0
    with_lang = 0
    in_block = False
    for line in content.splitlines():
        match = re.match(r"^```([^\s`]*)\s*$", line)
        if not match:
            continue
        if in_block:
            in_block = False
            continue
        total += 1
        if match.group(1):
            with_lang += 1
        in_block = True
    return total, with_lang


def iter_lines(content: str) -> list[tuple[int, str, bool]]:
    """Yield (line number, line, inside fenced code block)."""
    rows: list[tuple[int, str, bool]] = []
    in_block = False
    for number, line in enumerate(content.splitlines(), start=1):
        if re.match(r"^\s*```", line):
            in_block = not in_block
            rows.append((number, line, True))
            continue
        rows.append((number, line, in_block))
    return rows


REF_PATTERNS = [
    r"!\[[^\]]*\]\(([^)]+)\)",
    r"\[[^\]]+\]\(([^)]+)\)",
    r"src=[\"']([^\"']+)[\"']",
]


def relative_refs(content: str) -> list[tuple[int, str]]:
    seen: set[tuple[int, str]] = set()
    result: list[tuple[int, str]] = []
    for number, line, in_block in iter_lines(content):
        if in_block:
            continue
        for pattern in REF_PATTERNS:
            for ref in re.findall(pattern, line):
                clean = ref.split()[0].strip("<>")
                if re.match(r"^(https?:|mailto:|#|data:)", clean):
                    continue
                clean = clean.split("#", 1)[0]
                if clean and (number, clean) not in seen:
                    seen.add((number, clean))
                    result.append((number, clean))
    return result


def repo_root(start: Path) -> Path:
    """Nearest ancestor holding .git, which is how a host resolves /abs links."""
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    return start


def resolve_ref(readme: Path, ref: str) -> Path:
    # A leading slash resolves from the repository root on GitHub and friends.
    # Joining it onto the README's directory would discard that directory and
    # probe the filesystem root instead.
    if ref.startswith("/"):
        return repo_root(readme.parent) / ref.lstrip("/")
    return readme.parent / ref


def validate_readme(readme: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    content = read(readme)
    headings = markdown_headings(content)
    h1_count = sum(1 for level, _ in headings if level == 1)
    if h1_count != 1:
        errors.append(f"expected exactly one H1, found {h1_count}")

    total_blocks, with_lang = code_block_languages(content)
    if total_blocks and with_lang < total_blocks:
        errors.append("some fenced code blocks lack language identifiers")

    for number, line, in_block in iter_lines(content):
        for label, pattern in TEMPLATE_PLACEHOLDERS:
            for hit in re.findall(pattern, line):
                text = hit if isinstance(hit, str) else hit[0]
                where = errors if not in_block else warnings
                suffix = "" if not in_block else " (inside a code block; confirm it documents a template)"
                where.append(f"line {number}: unresolved {label} {text!r}{suffix}")
        for label, pattern in AMBIGUOUS_MARKERS:
            if re.search(pattern, line):
                warnings.append(
                    f"line {number}: possible {label} in {line.strip()[:70]!r}"
                )

    for number, ref in relative_refs(content):
        if not resolve_ref(readme, ref).exists():
            errors.append(f"line {number}: broken relative reference {ref!r}")

    for pattern in BADGE_PLACEHOLDER_PATTERNS:
        for number, line, _ in iter_lines(content):
            if re.search(pattern, line):
                errors.append(f"line {number}: badge has an unresolved owner/repo")

    styles = set(re.findall(r"img\.shields\.io/[^)\s\"']*[?&]style=([a-z-]+)", content))
    if len(styles) > 1:
        errors.append("mixed shields.io badge styles: " + ", ".join(sorted(styles)))

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill", type=Path, help="Skill directory to validate")
    parser.add_argument("--readme", type=Path, help="README file to validate")
    args = parser.parse_args()

    if not args.skill and not args.readme:
        args.skill = Path(__file__).resolve().parents[1]

    errors: list[str] = []
    warnings: list[str] = []
    if args.skill:
        errors.extend(f"skill: {e}" for e in validate_skill(args.skill.resolve()))
    if args.readme:
        readme_errors, readme_warnings = validate_readme(args.readme.resolve())
        errors.extend(f"readme: {e}" for e in readme_errors)
        warnings.extend(f"readme: {w}" for w in readme_warnings)

    for warning in warnings:
        print(f"WARN {warning}")

    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1

    target = []
    if args.skill:
        target.append("skill")
    if args.readme:
        target.append("readme")
    print("PASS " + " and ".join(target))
    return 0


if __name__ == "__main__":
    sys.exit(main())
