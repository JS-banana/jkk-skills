#!/usr/bin/env python3
"""Validate the to-html skill package and rendered HTML."""

from __future__ import annotations

import argparse
import hashlib
import html as html_module
import json
import re
import sys
import tempfile
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

import render as report_render  # noqa: E402


REQUIRED_FILES = [
    "SKILL.md",
    "scripts/render.py",
    "scripts/validate.py",
    "scripts/vendor/mistune/__init__.py",
    "references/editorial-grammar.md",
    "references/visual-routing.md",
    "references/quality-gates.md",
    "assets/report.html",
    "assets/report.css",
    "assets/report.js",
    "assets/mermaid.min.js",
    "assets/licenses/THIRD_PARTY.txt",
    "assets/licenses/mistune-LICENSE.txt",
    "assets/licenses/mermaid-LICENSE.txt",
]


def validate_skill(skill_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for relative in REQUIRED_FILES:
        if not (skill_dir / relative).is_file():
            errors.append(f"missing required file: {relative}")

    skill_md = skill_dir / "SKILL.md"
    if skill_md.is_file():
        text = skill_md.read_text(encoding="utf-8")
        if not re.search(r"^name:\s*to-html\s*$", text, flags=re.MULTILINE):
            errors.append("SKILL.md name must be to-html")
        if "description:" not in text or "friendly, self-contained HTML" not in text:
            errors.append("SKILL.md description is missing its preview trigger")
        for required in (
            "references/editorial-grammar.md",
            "references/visual-routing.md",
            "references/quality-gates.md",
            "scripts/render.py",
            "scripts/validate.py",
        ):
            if required not in text:
                errors.append(f"SKILL.md does not route to {required}")
        if re.search(r"\b(?:TODO|FIXME)\b", text):
            errors.append("SKILL.md contains a placeholder")
        if len(text.splitlines()) > 150:
            warnings.append(f"SKILL.md is long: {len(text.splitlines())} lines")

    mistune_init = skill_dir / "scripts/vendor/mistune/__init__.py"
    if mistune_init.is_file():
        text = mistune_init.read_text(encoding="utf-8")
        if f'__version__ = "{report_render.MISTUNE_VERSION}"' not in text:
            errors.append("vendored Mistune version does not match renderer metadata")

    mermaid = skill_dir / "assets/mermaid.min.js"
    if mermaid.is_file():
        head = mermaid.read_text(encoding="utf-8")[:300]
        if f"Mermaid {report_render.MERMAID_VERSION}" not in head:
            errors.append("vendored Mermaid version does not match renderer metadata")
        if mermaid.stat().st_size < 1_000_000:
            warnings.append("Mermaid asset is unexpectedly small")

    return errors, warnings


def extract_manifest(content: str) -> dict:
    match = re.search(
        r'<script type="application/json" id="report-manifest">(.*?)</script>',
        content,
        flags=re.DOTALL,
    )
    if not match:
        raise ValueError("embedded report manifest not found")
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise ValueError(f"embedded report manifest is invalid: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("embedded report manifest must be an object")
    return payload


def extract_source_snapshot(content: str) -> str:
    match = re.search(
        r'<pre id="source-markdown"[^>]*>(.*?)</pre>',
        content,
        flags=re.DOTALL,
    )
    if not match:
        raise ValueError("source Markdown snapshot not found")
    return html_module.unescape(match.group(1))


def validate_html(html_path: Path, source_path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    html_path = html_path.expanduser().resolve()
    source_path = source_path.expanduser().resolve()

    if not html_path.is_file():
        return [f"HTML does not exist: {html_path}"], warnings
    if not source_path.is_file():
        return [f"source does not exist: {source_path}"], warnings

    content = html_path.read_text(encoding="utf-8")
    source_bytes = source_path.read_bytes()
    source_text = source_bytes.decode("utf-8")
    source_sha = hashlib.sha256(source_bytes).hexdigest()

    try:
        manifest = extract_manifest(content)
    except ValueError as exc:
        return [str(exc)], warnings

    source_meta = manifest.get("source", {})
    document_meta = manifest.get("document", {})
    if source_meta.get("path") != str(source_path):
        errors.append("manifest source path does not match")
    if source_meta.get("sha256") != source_sha:
        errors.append("manifest source SHA-256 is stale")
    if source_meta.get("bytes") != len(source_bytes):
        errors.append("manifest source byte count does not match")

    expected_headings = len(report_render.source_headings(source_text))
    if source_meta.get("heading_count") != expected_headings:
        errors.append("manifest source heading count does not match")
    if document_meta.get("rendered_heading_count") != expected_headings:
        errors.append("manifest rendered heading count does not match source")

    try:
        snapshot = extract_source_snapshot(content)
    except ValueError as exc:
        errors.append(str(exc))
    else:
        if snapshot != source_text:
            errors.append("embedded source Markdown differs from source file")

    requirements = {
        "doctype": r"^<!doctype html>",
        "language": r"<html lang=",
        "source hash metadata": rf'<meta name="report-source-sha256" content="{source_sha}">',
        "embedded favicon": r'<link rel="icon" href="data:,">',
        "skip link": r'class="skip-link"',
        "main landmark": r'<main id="main-content"',
        "labelled navigation": r'<nav class="toc-panel"[^>]+aria-label=',
        "source dialog": r'<dialog class="source-dialog"',
        "diagram dialog": r'<dialog class="diagram-dialog"',
        "print stylesheet": r"@media print",
        "reduced motion stylesheet": r"prefers-reduced-motion:\s*reduce",
        "strict Mermaid": r'securityLevel:\s*"strict"',
        "visible focus": r":focus-visible",
    }
    for label, pattern in requirements.items():
        if not re.search(pattern, content, flags=re.MULTILINE | re.IGNORECASE):
            errors.append(f"missing {label}")

    forbidden = {
        "external script": r"<script\b[^>]*\bsrc\s*=",
        "external stylesheet": r"<link\b[^>]*\brel=[\"']stylesheet",
        "remote image request": r"<img\b[^>]*\bsrc=[\"']https?://",
        "CSS network import": r"@import\s+(?:url\()?['\"]?https?://",
        "CSS remote URL": r"url\(['\"]?https?://",
    }
    for label, pattern in forbidden.items():
        if re.search(pattern, content, flags=re.IGNORECASE):
            errors.append(f"found {label}")
    if re.search(r"\{\{[A-Z_]+\}\}", content):
        errors.append("found unresolved template placeholder")

    if html_path.stat().st_size > 10 * 1024 * 1024:
        warnings.append(f"large self-contained HTML: {html_path.stat().st_size} bytes")
    degraded = manifest.get("assets", {}).get("degraded_remote_or_missing_images", [])
    if degraded:
        warnings.append(f"{len(degraded)} remote or missing image(s) rendered as links")
    if document_meta.get("diagram_count", 0) == 0:
        warnings.append("report contains no Mermaid diagrams")
    if expected_headings and document_meta.get("toc_heading_count", 0) == 0:
        errors.append("report has headings but no table of contents")
    if document_meta.get("archetype") == "field-guide":
        for marker in (
            'class="system-section"',
            'id="field-acceptance"',
            'id="field-decisions"',
            'id="field-workstreams"',
            'id="field-risks"',
            'class="source-dossier"',
        ):
            if marker not in content:
                errors.append(f"field-guide output is missing {marker}")
        minimum_bindings = sum(limit[0] for limit in report_render.FIELD_GUIDE_LIMITS.values())
        if manifest.get("presentation", {}).get("source_binding_count", 0) < minimum_bindings:
            errors.append("field-guide presentation has too few source bindings")

    return errors, warnings


def run_self_test() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    with tempfile.TemporaryDirectory(prefix="to-html-") as temp:
        root = Path(temp)
        source = root / "demo.md"
        brief = root / "brief.json"
        output = root / "demo.html"
        source.write_text(
            """# 安全渲染演示

> 状态：验证中
> 用途：验证完整渲染链路

## 先说结论

原始 HTML 必须被转义，结构化内容必须保留。

<script>alert("unsafe")</script>

| 能力 | 状态 |
| --- | --- |
| 离线 | 通过 |

```mermaid
flowchart LR
  Source --> Report
```

```python
print("safe")
```
""",
            encoding="utf-8",
        )
        brief.write_text(
            json.dumps(
                {
                    "archetype": "field-guide",
                    "design_read": {
                        "page_kind": "Technical field guide",
                        "audience": "Renderer maintainers",
                        "vibe": "Evidence-first test fixture",
                        "narrative_axis": "Source → safe rendering → validation",
                        "design_variance": 5,
                        "motion_intensity": 1,
                        "visual_density": 6,
                    },
                    "eyebrow": "Self test",
                    "deck": "验证渲染、转义、图表和离线产物。",
                    "summary": "原始 HTML 被转义，Markdown 内容完整保留。",
                    "next_move": "运行验证器并检查输出。",
                    "status": {"label": "验证中", "tone": "warning"},
                    "highlights": [],
                    "reading_path": ["先说结论"],
                    "system_flow": [
                        {
                            "label": "源文档",
                            "detail": "读取可信输入",
                            "source_section": "先说结论",
                        },
                        {
                            "label": "安全渲染",
                            "detail": "转义原始 HTML",
                            "source_section": "先说结论",
                        },
                        {
                            "label": "确定性校验",
                            "detail": "核对哈希与结构",
                            "source_section": "先说结论",
                        },
                    ],
                    "acceptance_lanes": [
                        {
                            "label": "内容",
                            "state": "完整保留",
                            "items": ["源标题存在", "源快照一致"],
                            "source_section": "先说结论",
                        },
                        {
                            "label": "安全",
                            "state": "无外部执行",
                            "items": ["HTML 被转义", "资源已内联"],
                            "source_section": "先说结论",
                        },
                    ],
                    "decisions": [
                        {
                            "id": "D1",
                            "title": "源文档是事实源",
                            "principle": "派生产物不反写源内容。",
                            "source_section": "先说结论",
                        },
                        {
                            "id": "D2",
                            "title": "原始 HTML 必须转义",
                            "principle": "渲染不能执行输入脚本。",
                            "source_section": "先说结论",
                        },
                        {
                            "id": "D3",
                            "title": "输出必须可追溯",
                            "principle": "哈希和源快照同时保留。",
                            "source_section": "先说结论",
                        },
                    ],
                    "workstreams": [
                        {
                            "id": "P1",
                            "title": "解析",
                            "phase": "M1",
                            "effort": "1 step",
                            "status": "已完成",
                            "depends_on": [],
                            "source_section": "先说结论",
                        },
                        {
                            "id": "P2",
                            "title": "渲染",
                            "phase": "M2",
                            "effort": "1 step",
                            "status": "已完成",
                            "depends_on": ["P1"],
                            "source_section": "先说结论",
                        },
                        {
                            "id": "P3",
                            "title": "校验",
                            "phase": "M3",
                            "effort": "1 step",
                            "status": "进行中",
                            "depends_on": ["P2"],
                            "source_section": "先说结论",
                        },
                    ],
                    "risks": [
                        {
                            "risk": "脚本注入",
                            "signal": "原始 script 出现在文章 DOM。",
                            "response": "验证失败。",
                            "source_section": "先说结论",
                        },
                        {
                            "risk": "源内容漂移",
                            "signal": "源哈希不一致。",
                            "response": "重新生成报告。",
                            "source_section": "先说结论",
                        },
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        try:
            report_render.render_report(source, output, brief)
        except Exception as exc:  # pragma: no cover - self-test boundary
            return [f"renderer self-test failed: {exc}"], warnings
        html = output.read_text(encoding="utf-8")
        article_match = re.search(
            r'<article class="report-article"[^>]*>(.*?)</article>',
            html,
            flags=re.DOTALL,
        )
        if not article_match:
            errors.append("self-test article not found")
        elif '<script>alert("unsafe")</script>' in article_match.group(1):
            errors.append("raw source HTML was executed instead of escaped")
        html_errors, html_warnings = validate_html(output, source)
        errors.extend(f"self-test: {error}" for error in html_errors)
        warnings.extend(f"self-test: {warning}" for warning in html_warnings)

        invalid = json.loads(brief.read_text(encoding="utf-8"))
        invalid["risks"][0]["source_section"] = "不存在的章节"
        brief.write_text(json.dumps(invalid, ensure_ascii=False), encoding="utf-8")
        try:
            report_render.render_report(source, root / "invalid.html", brief)
        except ValueError as exc:
            if "source_section does not match" not in str(exc):
                errors.append(f"self-test: unexpected source binding error: {exc}")
        else:
            errors.append("self-test: invalid source binding was accepted")
    return errors, warnings


def print_result(errors: list[str], warnings: list[str]) -> int:
    for warning in warnings:
        print(f"WARN {warning}")
    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1
    print("PASS to-html validation")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill", type=Path, help="skill directory; defaults to this skill")
    parser.add_argument("--html", type=Path, help="rendered HTML to validate")
    parser.add_argument("--source", type=Path, help="Markdown source for --html")
    parser.add_argument("--self-test", action="store_true", help="run an isolated render test")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    warnings: list[str] = []

    if args.html and not args.source:
        print("FAIL --html requires --source")
        return 2
    if args.source and not args.html:
        print("FAIL --source requires --html")
        return 2

    if not args.html and not args.self_test:
        args.skill = args.skill or SKILL_DIR
    if args.skill:
        new_errors, new_warnings = validate_skill(args.skill.expanduser().resolve())
        errors.extend(f"skill: {error}" for error in new_errors)
        warnings.extend(f"skill: {warning}" for warning in new_warnings)
    if args.html:
        new_errors, new_warnings = validate_html(args.html, args.source)
        errors.extend(f"html: {error}" for error in new_errors)
        warnings.extend(f"html: {warning}" for warning in new_warnings)
    if args.self_test:
        new_errors, new_warnings = run_self_test()
        errors.extend(new_errors)
        warnings.extend(new_warnings)
    return print_result(errors, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
