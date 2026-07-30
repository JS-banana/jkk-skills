#!/usr/bin/env python3
"""Render Markdown research into a self-contained editorial HTML report."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import mimetypes
import re
import sys
import tempfile
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


SKILL_DIR = Path(__file__).resolve().parents[1]
ASSETS_DIR = SKILL_DIR / "assets"
VENDOR_DIR = Path(__file__).resolve().parent / "vendor"
sys.path.insert(0, str(VENDOR_DIR))

import mistune  # noqa: E402
from mistune.toc import add_toc_hook  # noqa: E402
from mistune.util import striptags  # noqa: E402


VERSION = "0.2.0"
MISTUNE_VERSION = "3.3.4"
MERMAID_VERSION = "11.16.0"
STATUS_TONES = {"neutral", "info", "warning", "success", "danger"}
MAX_HIGHLIGHTS = 4
MAX_READING_PATH = 6
FIELD_GUIDE_LIMITS = {
    "system_flow": (3, 8),
    "acceptance_lanes": (2, 4),
    "decisions": (3, 8),
    "workstreams": (3, 12),
    "risks": (2, 8),
}


class ReportRenderer(mistune.HTMLRenderer):
    """Safe renderer with report-specific code, links, images and diagrams."""

    def __init__(self, source_dir: Path) -> None:
        super().__init__(escape=True)
        self.source_dir = source_dir
        self.diagram_count = 0
        self.code_count = 0
        self.local_images: list[str] = []
        self.degraded_images: list[str] = []

    def heading(self, text: str, level: int, **attrs: Any) -> str:
        heading_id = str(attrs.get("id") or "")
        anchor = ""
        if heading_id:
            label = escape(striptags(text), quote=True)
            anchor = (
                f'<a class="heading-anchor" href="#{escape(heading_id, quote=True)}" '
                f'aria-label="链接到“{label}”">#</a>'
            )
        return (
            f'<h{level} id="{escape(heading_id, quote=True)}" data-heading-level="{level}">'
            f'<span>{text}</span>{anchor}</h{level}>\n'
        )

    def block_code(self, code: str, info: str | None = None) -> str:
        language = ""
        if info:
            language = info.strip().split(None, 1)[0].lower()
        if language == "mermaid":
            return self.render_diagram(code)

        self.code_count += 1
        label = language.upper() if language else "TEXT"
        code_id = f"code-{self.code_count}"
        class_name = f' class="language-{escape(language, quote=True)}"' if language else ""
        return (
            f'<div class="code-shell" data-code-block="{code_id}">'
            '<div class="code-toolbar">'
            f'<span>{escape(label)}</span>'
            f'<button type="button" class="quiet-button copy-code" data-copy-target="{code_id}">'
            '<span aria-hidden="true">⧉</span> 复制</button>'
            "</div>"
            f'<pre id="{code_id}"><code{class_name}>{escape(code)}</code></pre>'
            "</div>\n"
        )

    def render_diagram(
        self,
        source: str,
        title: str = "结构图",
        caption: str = "",
        featured: bool = False,
    ) -> str:
        self.diagram_count += 1
        diagram_id = f"diagram-{self.diagram_count}"
        figure_class = "diagram-card featured-diagram" if featured else "diagram-card"
        caption_html = f"<p>{escape(caption)}</p>" if caption else ""
        return (
            f'<figure class="{figure_class}" data-diagram="{diagram_id}">'
            '<div class="diagram-toolbar">'
            f'<figcaption>{escape(title)}</figcaption>'
            f'<button type="button" class="quiet-button expand-diagram" '
            f'data-diagram-target="{diagram_id}">'
            '<span aria-hidden="true">⤢</span> 放大</button>'
            "</div>"
            f'<template class="mermaid-source">{escape(source)}</template>'
            f'<div class="mermaid-canvas" id="{diagram_id}" role="img" '
            f'aria-label="{escape(title, quote=True)}"></div>'
            f"{caption_html}"
            "<details class=\"diagram-source\"><summary>查看 Mermaid 源码</summary>"
            f"<pre><code>{escape(source)}</code></pre></details>"
            "</figure>\n"
        )

    def link(self, text: str, url: str, title: str | None = None) -> str:
        safe_url, external = self._resolve_link(url)
        title_attr = f' title="{escape(title, quote=True)}"' if title else ""
        target_attr = ' target="_blank" rel="noopener noreferrer"' if external else ""
        return f'<a href="{safe_url}"{title_attr}{target_attr}>{text}</a>'

    def image(self, text: str, url: str, title: str | None = None) -> str:
        alt = striptags(text).strip() or "文档图片"
        parsed = urlparse(url)
        if parsed.scheme in {"http", "https"}:
            self.degraded_images.append(url)
            safe_url = escape(url, quote=True)
            return (
                '<span class="remote-image">'
                f'<a href="{safe_url}" target="_blank" rel="noopener noreferrer">'
                f'远程图片：{escape(alt)}</a>'
                '<small>为保持离线与安全，未自动抓取</small>'
                "</span>"
            )

        image_path = self._resolve_local_path(url)
        if not image_path or not image_path.is_file():
            self.degraded_images.append(url)
            return (
                '<span class="missing-image" role="note">'
                f"图片不可用：{escape(alt)}"
                f"<small>{escape(url)}</small>"
                "</span>"
            )

        data_url = data_uri(image_path)
        self.local_images.append(str(image_path))
        title_attr = f' title="{escape(title, quote=True)}"' if title else ""
        return (
            '<figure class="inline-image">'
            f'<img src="{data_url}" alt="{escape(alt, quote=True)}" loading="lazy"{title_attr}>'
            f"<figcaption>{escape(title or alt)}</figcaption>"
            "</figure>"
        )

    def _resolve_link(self, url: str) -> tuple[str, bool]:
        decoded = unquote(url).strip()
        parsed = urlparse(decoded)
        if parsed.scheme in {"http", "https"}:
            return escape(decoded, quote=True), True
        if parsed.scheme in {"mailto", "tel"} or decoded.startswith("#"):
            return escape(decoded, quote=True), False
        if parsed.scheme:
            return "#harmful-link", False

        path_part, marker, fragment = decoded.partition("#")
        resolved = (self.source_dir / path_part).resolve()
        try:
            uri = resolved.as_uri()
        except ValueError:
            return "#invalid-local-link", False
        if marker:
            uri += "#" + fragment
        return escape(uri, quote=True), False

    def _resolve_local_path(self, url: str) -> Path | None:
        parsed = urlparse(unquote(url))
        if parsed.scheme == "file":
            return Path(parsed.path).resolve()
        if parsed.scheme:
            return None
        return (self.source_dir / parsed.path).resolve()


def report_table(renderer: Any, text: str) -> str:
    return (
        '<div class="table-scroll" role="region" aria-label="可横向滚动的数据表" tabindex="0">'
        f"<table>{text}</table></div>\n"
    )


def report_table_cell(
    renderer: Any,
    text: str,
    align: str | None = None,
    head: bool = False,
) -> str:
    tag = "th" if head else "td"
    scope = ' scope="col"' if head else ""
    align_attr = f' style="text-align:{align}"' if align else ""
    return f"<{tag}{scope}{align_attr}>{text}</{tag}>\n"


def slug_heading(token: dict[str, Any], index: int) -> str:
    raw = str(token.get("text") or "")
    text = re.sub(r"[`*_~\[\]()]+", " ", raw)
    text = re.sub(r"[^\w\u3400-\u9fff-]+", "-", text, flags=re.UNICODE)
    slug = re.sub(r"-+", "-", text).strip("-").lower()
    if not slug:
        slug = "section"
    return f"s{index + 1}-{slug[:72]}"


def create_markdown_renderer(source_dir: Path) -> tuple[Any, ReportRenderer]:
    renderer = ReportRenderer(source_dir)
    md = mistune.create_markdown(
        renderer=renderer,
        plugins=[
            "table",
            "strikethrough",
            "task_lists",
            "footnotes",
            "url",
            "def_list",
        ],
    )
    renderer.register("table", report_table)
    renderer.register("table_cell", report_table_cell)
    add_toc_hook(md, min_level=2, max_level=3, heading_id=slug_heading)
    return md, renderer


def source_title(markdown: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+?)\s*$", markdown, flags=re.MULTILINE)
    return strip_inline_markdown(match.group(1)) if match else fallback


def strip_front_matter(markdown: str) -> tuple[str, dict[str, str]]:
    """Remove the first H1 and a metadata-like leading blockquote from article."""
    lines = markdown.splitlines()
    if not lines:
        return markdown, {}

    cursor = 0
    while cursor < len(lines) and not lines[cursor].strip():
        cursor += 1
    if cursor < len(lines) and re.match(r"^#\s+", lines[cursor]):
        cursor += 1
    while cursor < len(lines) and not lines[cursor].strip():
        cursor += 1

    quote_start = cursor
    quote_lines: list[str] = []
    while cursor < len(lines) and lines[cursor].lstrip().startswith(">"):
        quote_lines.append(re.sub(r"^\s*>\s?", "", lines[cursor]))
        cursor += 1

    metadata: dict[str, str] = {}
    for line in quote_lines:
        match = re.match(r"^([^：:]{1,24})[：:]\s*(.+)$", line.strip())
        if match:
            metadata[strip_inline_markdown(match.group(1))] = strip_inline_markdown(match.group(2))

    if len(metadata) < 2:
        cursor = quote_start
        metadata = {}
    while cursor < len(lines) and not lines[cursor].strip():
        cursor += 1
    return "\n".join(lines[cursor:]).strip() + "\n", metadata


def strip_inline_markdown(text: str) -> str:
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[`*_~]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_section(markdown: str, heading_pattern: str) -> str:
    pattern = re.compile(
        rf"^##\s+[^\n]*(?:{heading_pattern})[^\n]*$\n(?P<body>.*?)(?=^##\s+|\Z)",
        flags=re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(markdown)
    if not match:
        return ""
    body = match.group("body")
    body = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
    body = re.sub(r"^\|.*$", "", body, flags=re.MULTILINE)
    body = re.sub(r"^\s*[-*+]\s+", "", body, flags=re.MULTILINE)
    body = re.sub(r"^\s*\d+\.\s+", "", body, flags=re.MULTILINE)
    return strip_inline_markdown(body)[:600]


def initial_brief(markdown: str, title: str, metadata: dict[str, str]) -> dict[str, Any]:
    headings = source_headings(markdown)
    reading_path = [text for level, text in headings if level == 2][:5]
    status_value = next((value for key, value in metadata.items() if "状态" in key), "")
    scope_value = next((value for key, value in metadata.items() if "范围" in key), "")
    return {
        "archetype": "document",
        "eyebrow": "Research field guide",
        "deck": scope_value or f"{title}的结构化阅读版本。",
        "summary": extract_section(markdown, r"结论|summary|overview"),
        "status": {
            "label": status_value or "Research report",
            "tone": "warning" if any(word in status_value for word in ("实施", "进行", "待")) else "neutral",
        },
        "highlights": [],
        "reading_path": reading_path,
    }


def initial_presentation(markdown: str, title: str, metadata: dict[str, str]) -> dict[str, Any]:
    payload = initial_brief(markdown, title, metadata)
    payload.update(
        {
            "archetype": "field-guide",
            "design_read": {
                "page_kind": "Technical implementation field guide",
                "audience": "",
                "vibe": "",
                "narrative_axis": "",
                "design_variance": 5,
                "motion_intensity": 2,
                "visual_density": 7,
            },
            "next_move": "",
            "system_flow": [],
            "acceptance_lanes": [],
            "decisions": [],
            "workstreams": [],
            "risks": [],
        }
    )
    return payload


def load_brief(path: Path | None, fallback: dict[str, Any]) -> dict[str, Any]:
    if path is None:
        return fallback
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"brief cannot be read: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("brief must be a JSON object")
    merged = dict(fallback)
    merged.update(payload)
    validate_brief(merged)
    return merged


def validate_brief(brief: dict[str, Any]) -> None:
    archetype = brief.get("archetype", "document")
    if archetype not in {"document", "field-guide"}:
        raise ValueError("presentation.archetype must be document or field-guide")
    for field in ("eyebrow", "deck", "summary"):
        value = brief.get(field, "")
        if not isinstance(value, str):
            raise ValueError(f"presentation.{field} must be a string")
    status = brief.get("status", {})
    if not isinstance(status, dict):
        raise ValueError("brief.status must be an object")
    tone = status.get("tone", "neutral")
    if tone not in STATUS_TONES:
        raise ValueError(f"brief.status.tone must be one of {sorted(STATUS_TONES)}")
    highlights = brief.get("highlights", [])
    if not isinstance(highlights, list) or len(highlights) > MAX_HIGHLIGHTS:
        raise ValueError(f"brief.highlights must contain at most {MAX_HIGHLIGHTS} items")
    for item in highlights:
        if not isinstance(item, dict):
            raise ValueError("each highlight must be an object")
        for field in ("kicker", "value", "detail"):
            if not isinstance(item.get(field, ""), str):
                raise ValueError(f"highlight.{field} must be a string")
    reading_path = brief.get("reading_path", [])
    if not isinstance(reading_path, list) or len(reading_path) > MAX_READING_PATH:
        raise ValueError(f"brief.reading_path must contain at most {MAX_READING_PATH} items")
    if not all(isinstance(item, str) for item in reading_path):
        raise ValueError("brief.reading_path items must be strings")
    featured = brief.get("featured_diagram")
    if featured is not None:
        if not isinstance(featured, dict) or not isinstance(featured.get("source"), str):
            raise ValueError("brief.featured_diagram requires a Mermaid source string")
        if not looks_like_mermaid(featured["source"]):
            raise ValueError("brief.featured_diagram does not look like Mermaid")
    hero_image = brief.get("hero_image")
    if hero_image is not None:
        if not isinstance(hero_image, dict):
            raise ValueError("brief.hero_image must be an object")
        for field in ("path", "alt"):
            if not isinstance(hero_image.get(field), str) or not hero_image[field].strip():
                raise ValueError(f"brief.hero_image.{field} is required")
    if archetype == "field-guide":
        validate_field_guide(brief)


def validate_field_guide(presentation: dict[str, Any]) -> None:
    design_read = presentation.get("design_read")
    if not isinstance(design_read, dict):
        raise ValueError("presentation.design_read must be an object")
    for field in ("page_kind", "audience", "vibe", "narrative_axis"):
        if not isinstance(design_read.get(field), str) or not design_read[field].strip():
            raise ValueError(f"presentation.design_read.{field} is required")
    for field in ("design_variance", "motion_intensity", "visual_density"):
        value = design_read.get(field)
        if not isinstance(value, int) or not 1 <= value <= 10:
            raise ValueError(f"presentation.design_read.{field} must be an integer from 1 to 10")
    if not isinstance(presentation.get("next_move"), str) or not presentation["next_move"].strip():
        raise ValueError("presentation.next_move is required")

    for field, (minimum, maximum) in FIELD_GUIDE_LIMITS.items():
        items = presentation.get(field)
        if not isinstance(items, list) or not minimum <= len(items) <= maximum:
            raise ValueError(
                f"presentation.{field} must contain {minimum}–{maximum} source-backed items"
            )
        for item in items:
            if not isinstance(item, dict):
                raise ValueError(f"presentation.{field} items must be objects")
            if not isinstance(item.get("source_section"), str) or not item["source_section"].strip():
                raise ValueError(f"presentation.{field} items require source_section")

    for item in presentation["system_flow"]:
        require_strings(item, "system_flow", ("label", "detail"))
    for item in presentation["acceptance_lanes"]:
        require_strings(item, "acceptance_lanes", ("label", "state"))
        points = item.get("items")
        if not isinstance(points, list) or not 2 <= len(points) <= 5:
            raise ValueError("acceptance_lanes.items must contain 2–5 strings")
        if not all(isinstance(point, str) and point.strip() for point in points):
            raise ValueError("acceptance_lanes.items must contain non-empty strings")
    for item in presentation["decisions"]:
        require_strings(item, "decisions", ("id", "title", "principle"))
    for item in presentation["workstreams"]:
        require_strings(item, "workstreams", ("id", "title", "phase", "effort", "status"))
        dependencies = item.get("depends_on", [])
        if not isinstance(dependencies, list) or not all(
            isinstance(dependency, str) for dependency in dependencies
        ):
            raise ValueError("workstreams.depends_on must be a list of strings")
    for item in presentation["risks"]:
        require_strings(item, "risks", ("risk", "signal", "response"))


def require_strings(item: dict[str, Any], group: str, fields: tuple[str, ...]) -> None:
    for field in fields:
        if not isinstance(item.get(field), str) or not item[field].strip():
            raise ValueError(f"presentation.{group}.{field} is required")


def looks_like_mermaid(source: str) -> bool:
    first = source.strip().splitlines()[0].lower() if source.strip() else ""
    return first.startswith(
        (
            "flowchart",
            "graph",
            "sequencediagram",
            "statediagram",
            "classdiagram",
            "erdiagram",
            "gantt",
            "journey",
            "timeline",
            "mindmap",
            "pie",
            "gitgraph",
            "requirementdiagram",
            "quadrantchart",
            "sankey",
            "xychart",
            "architecture",
            "block",
            "packet",
            "kanban",
            "radar",
            "treemap",
            "zenuml",
        )
    )


def source_headings(markdown: str) -> list[tuple[int, str]]:
    headings: list[tuple[int, str]] = []
    in_fence = False
    fence = ""
    for line in markdown.splitlines():
        fence_match = re.match(r"^\s*(```+|~~~+)", line)
        if fence_match:
            marker = fence_match.group(1)[0]
            if not in_fence:
                in_fence = True
                fence = marker
            elif marker == fence:
                in_fence = False
            continue
        if in_fence:
            continue
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            headings.append((len(match.group(1)), strip_inline_markdown(match.group(2))))
    return headings


def source_stats(markdown: str) -> dict[str, int]:
    headings = source_headings(markdown)
    cjk_chars = len(re.findall(r"[\u3400-\u9fff]", markdown))
    latin_words = len(re.findall(r"\b[A-Za-z0-9][A-Za-z0-9_-]*\b", markdown))
    reading_minutes = max(1, math.ceil(cjk_chars / 550 + latin_words / 220))
    code_fences = len(re.findall(r"^\s*```", markdown, flags=re.MULTILINE)) // 2
    diagrams = len(re.findall(r"^\s*```mermaid\b", markdown, flags=re.MULTILINE | re.IGNORECASE))
    tables = len(
        re.findall(
            r"^\s*\|?.+\|.+\|?\s*$\n^\s*\|?\s*:?-{3,}",
            markdown,
            flags=re.MULTILINE,
        )
    )
    return {
        "headings": len(headings),
        "sections": sum(1 for level, _ in headings if level == 2),
        "code_blocks": code_fences,
        "diagrams": diagrams,
        "tables": tables,
        "reading_minutes": reading_minutes,
    }


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def render_toc(
    toc_items: list[tuple[int, str, str]],
    field_items: list[tuple[str, str]] | None = None,
) -> str:
    parts: list[str] = []
    for target, label in field_items or []:
        parts.append(
            '<li class="toc-section toc-field">'
            f'<a href="#{escape(target, quote=True)}">{escape(label)}</a></li>'
        )
    if field_items:
        parts.append('<li class="toc-divider" aria-hidden="true">完整资料</li>')
    open_nested = False
    for level, heading_id, text in toc_items:
        if level == 2:
            if open_nested:
                parts.append("</ol></li>")
            parts.append(
                f'<li class="toc-section"><a href="#{escape(heading_id, quote=True)}">'
                f"{escape(text)}</a><ol>"
            )
            open_nested = True
        elif open_nested:
            parts.append(
                f'<li><a href="#{escape(heading_id, quote=True)}">{escape(text)}</a></li>'
            )
    if open_nested:
        parts.append("</ol></li>")
    return '<ol class="toc-list">' + "".join(parts) + "</ol>"


def resolve_heading_id(
    source_section: str,
    toc_items: list[tuple[int, str, str]],
) -> str | None:
    needle = source_section.strip().casefold()
    exact = next(
        (heading_id for _, heading_id, text in toc_items if text.strip().casefold() == needle),
        None,
    )
    if exact:
        return exact
    return next(
        (
            heading_id
            for _, heading_id, text in toc_items
            if needle in text.casefold() or text.casefold() in needle
        ),
        None,
    )


def validate_source_bindings(
    presentation: dict[str, Any],
    toc_items: list[tuple[int, str, str]],
) -> None:
    if presentation.get("archetype") != "field-guide":
        return
    for group in FIELD_GUIDE_LIMITS:
        for item in presentation[group]:
            source_section = item["source_section"]
            if not resolve_heading_id(source_section, toc_items):
                raise ValueError(
                    f"presentation.{group} source_section does not match a source heading: "
                    f"{source_section}"
                )


def evidence_link(
    source_section: str,
    toc_items: list[tuple[int, str, str]],
) -> str:
    target = resolve_heading_id(source_section, toc_items)
    if not target:
        return ""
    return (
        f'<a class="evidence-link" href="#{escape(target, quote=True)}">'
        '<span aria-hidden="true">↘</span>'
        f"<span>{escape(source_section)}</span></a>"
    )


def render_field_toc(presentation: dict[str, Any]) -> list[tuple[str, str]]:
    if presentation.get("archetype") != "field-guide":
        return []
    return [
        ("field-system", "系统路径"),
        ("field-acceptance", "三类验收门"),
        ("field-decisions", "关键决策"),
        ("field-workstreams", "实施路径"),
        ("field-risks", "风险雷达"),
    ]


def render_reading_path(items: list[str], toc_items: list[tuple[int, str, str]]) -> str:
    links: list[str] = []
    for item in items:
        target = next(
            (
                heading_id
                for _, heading_id, text in toc_items
                if item.casefold() in text.casefold() or text.casefold() in item.casefold()
            ),
            "",
        )
        if target:
            links.append(
                f'<li><a href="#{escape(target, quote=True)}">{escape(item)}</a></li>'
            )
        else:
            links.append(f"<li><span>{escape(item)}</span></li>")
    return "".join(links)


def render_highlights(items: list[dict[str, str]]) -> str:
    if not items:
        return ""
    parts = []
    for item in items:
        parts.append(
            '<article class="highlight">'
            f'<p class="highlight-kicker">{escape(item.get("kicker", ""))}</p>'
            f'<p class="highlight-value">{escape(item.get("value", ""))}</p>'
            f'<p class="highlight-detail">{escape(item.get("detail", ""))}</p>'
            "</article>"
        )
    return '<section class="highlights" aria-label="关键要点">' + "".join(parts) + "</section>"


def render_meta(metadata: dict[str, str]) -> str:
    if not metadata:
        return ""
    cells = []
    for key, value in list(metadata.items())[:5]:
        cells.append(
            "<div>"
            f"<dt>{escape(key)}</dt>"
            f"<dd>{escape(value)}</dd>"
            "</div>"
        )
    return '<dl class="source-meta">' + "".join(cells) + "</dl>"


def render_status(status: dict[str, Any]) -> str:
    label = str(status.get("label") or "").strip()
    if not label:
        return ""
    tone = status.get("tone", "neutral")
    return (
        f'<span class="status status-{escape(str(tone), quote=True)}">'
        '<span class="status-dot" aria-hidden="true"></span>'
        f"{escape(label)}</span>"
    )


def render_system_flow(
    items: list[dict[str, Any]],
    toc_items: list[tuple[int, str, str]],
) -> str:
    if not items:
        return ""
    steps = []
    for index, item in enumerate(items, start=1):
        kind = re.sub(r"[^a-z0-9-]", "", str(item.get("kind", "node")).lower()) or "node"
        steps.append(
            f'<li class="system-step" data-kind="{escape(kind, quote=True)}">'
            f'<span class="step-index">{index:02d}</span>'
            '<div class="step-copy">'
            f'<p>{escape(str(item["label"]))}</p>'
            f'<strong>{escape(str(item["detail"]))}</strong>'
            f'{evidence_link(str(item["source_section"]), toc_items)}'
            "</div></li>"
        )
    return (
        '<section class="system-section" id="field-system" aria-labelledby="field-system-title">'
        '<div class="section-heading compact-heading">'
        '<div><p class="section-index">01 / SYSTEM PATH</p>'
        '<h2 id="field-system-title">从终端信号到可验收能力</h2></div>'
        '<p>主路径只保留决定成败的五个交接点；细节回到原文章节。</p>'
        "</div>"
        f'<ol class="system-path">{"".join(steps)}</ol>'
        "</section>"
    )


def render_acceptance_lanes(
    items: list[dict[str, Any]],
    toc_items: list[tuple[int, str, str]],
) -> str:
    if not items:
        return ""
    lanes = []
    for index, item in enumerate(items, start=1):
        points = "".join(f"<li>{escape(str(point))}</li>" for point in item["items"])
        lanes.append(
            '<article class="acceptance-lane">'
            '<header>'
            f'<span>{index:02d}</span><div><h3>{escape(str(item["label"]))}</h3>'
            f'<p>{escape(str(item["state"]))}</p></div>'
            "</header>"
            f"<ul>{points}</ul>"
            f'{evidence_link(str(item["source_section"]), toc_items)}'
            "</article>"
        )
    return (
        '<section class="field-section" id="field-acceptance" '
        'aria-labelledby="field-acceptance-title">'
        '<div class="section-heading">'
        '<div><p class="section-index">02 / ACCEPTANCE GATES</p>'
        '<h2 id="field-acceptance-title">不是“代码合并”，而是三类证据同时闭环</h2></div>'
        '<p>每一门都来自原文的成功标准；缺一门就不能宣布一期完成。</p>'
        "</div>"
        f'<div class="acceptance-grid">{"".join(lanes)}</div>'
        "</section>"
    )


def render_decisions(
    items: list[dict[str, Any]],
    toc_items: list[tuple[int, str, str]],
) -> str:
    if not items:
        return ""
    decisions = []
    for item in items:
        decisions.append(
            "<li>"
            f'<span class="decision-id">{escape(str(item["id"]))}</span>'
            '<div class="decision-copy">'
            f'<h3>{escape(str(item["title"]))}</h3>'
            f'<p>{escape(str(item["principle"]))}</p>'
            f'{evidence_link(str(item["source_section"]), toc_items)}'
            "</div></li>"
        )
    return (
        '<section class="field-section decisions-section" id="field-decisions" '
        'aria-labelledby="field-decisions-title">'
        '<div class="section-heading">'
        '<div><p class="section-index">03 / DECISION LEDGER</p>'
        '<h2 id="field-decisions-title">六个不该在实施中重新争论的决定</h2></div>'
        '<p>把边界写成操作原则，减少开发过程中的架构漂移。</p>'
        "</div>"
        f'<ol class="decision-ledger">{"".join(decisions)}</ol>'
        "</section>"
    )


def status_class(value: str) -> str:
    if any(word in value for word in ("完成", "通过")):
        return "done"
    if any(word in value for word in ("阻塞", "暂停")):
        return "blocked"
    if any(word in value for word in ("进行", "待验收")):
        return "active"
    return "queued"


def render_workstreams(
    items: list[dict[str, Any]],
    toc_items: list[tuple[int, str, str]],
) -> str:
    if not items:
        return ""
    rows = []
    for item in items:
        dependencies = " · ".join(item.get("depends_on", [])) or "可独立启动"
        state = str(item["status"])
        rows.append(
            f'<li class="workstream-row" data-state="{status_class(state)}">'
            f'<span class="phase">{escape(str(item["phase"]))}</span>'
            '<div class="workstream-title">'
            f'<span>{escape(str(item["id"]))}</span><strong>{escape(str(item["title"]))}</strong>'
            f'{evidence_link(str(item["source_section"]), toc_items)}'
            "</div>"
            f'<span class="dependency">{escape(dependencies)}</span>'
            f'<span class="effort">{escape(str(item["effort"]))}</span>'
            f'<span class="workstream-state"><i aria-hidden="true"></i>{escape(state)}</span>'
            "</li>"
        )
    return (
        '<section class="field-section workstreams-section" id="field-workstreams" '
        'aria-labelledby="field-workstreams-title">'
        '<div class="section-heading">'
        '<div><p class="section-index">04 / DELIVERY SPINE</p>'
        '<h2 id="field-workstreams-title">先冻结事实，再让三条开发线并行</h2></div>'
        '<p>依赖和状态直接暴露；完整 DoD 与命令仍以原文任务包为准。</p>'
        "</div>"
        '<div class="workstream-head" aria-hidden="true">'
        "<span>阶段</span><span>任务</span><span>依赖</span><span>估算</span><span>状态</span>"
        "</div>"
        f'<ol class="workstream-board">{"".join(rows)}</ol>'
        "</section>"
    )


def render_risks(
    items: list[dict[str, Any]],
    toc_items: list[tuple[int, str, str]],
) -> str:
    if not items:
        return ""
    rows = []
    for index, item in enumerate(items, start=1):
        rows.append(
            '<article class="risk-row">'
            f'<span class="risk-index">R{index:02d}</span>'
            f'<h3>{escape(str(item["risk"]))}</h3>'
            '<div><span>EARLY SIGNAL</span>'
            f'<p>{escape(str(item["signal"]))}</p></div>'
            '<div><span>RESPONSE</span>'
            f'<p>{escape(str(item["response"]))}</p></div>'
            f'{evidence_link(str(item["source_section"]), toc_items)}'
            "</article>"
        )
    return (
        '<section class="field-section risks-section" id="field-risks" '
        'aria-labelledby="field-risks-title">'
        '<div class="section-heading">'
        '<div><p class="section-index">05 / RISK RADAR</p>'
        '<h2 id="field-risks-title">看见早期信号，就在成本扩散前止损</h2></div>'
        '<p>风险不是脚注；每项都绑定可观察信号和明确动作。</p>'
        "</div>"
        f'<div class="risk-ledger">{"".join(rows)}</div>'
        "</section>"
    )


def render_field_presentation(
    presentation: dict[str, Any],
    toc_items: list[tuple[int, str, str]],
) -> str:
    if presentation.get("archetype") != "field-guide":
        return ""
    return "".join(
        (
            render_acceptance_lanes(presentation["acceptance_lanes"], toc_items),
            render_decisions(presentation["decisions"], toc_items),
            render_workstreams(presentation["workstreams"], toc_items),
            render_risks(presentation["risks"], toc_items),
        )
    )


def render_hero_image(hero_image: dict[str, Any] | None) -> str:
    if not hero_image:
        return ""
    path = Path(hero_image["path"]).expanduser().resolve()
    if not path.is_file():
        raise ValueError(f"brief.hero_image.path does not exist: {path}")
    alt = str(hero_image["alt"])
    caption = str(hero_image.get("caption") or "")
    caption_html = f"<figcaption>{escape(caption)}</figcaption>" if caption else ""
    return (
        '<figure class="hero-image">'
        f'<img src="{data_uri(path)}" alt="{escape(alt, quote=True)}">'
        f"{caption_html}</figure>"
    )


def json_for_script(payload: dict[str, Any]) -> str:
    return (
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def inline_script(text: str) -> str:
    return re.sub(r"</script", r"<\\/script", text, flags=re.IGNORECASE)


def render_report(
    source_path: Path,
    output_path: Path,
    presentation_path: Path | None = None,
    lang: str = "zh-CN",
) -> dict[str, Any]:
    source_path = source_path.expanduser().resolve()
    output_path = output_path.expanduser().resolve()
    if not source_path.is_file():
        raise ValueError(f"source does not exist: {source_path}")

    source_bytes = source_path.read_bytes()
    try:
        markdown = source_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("source must be UTF-8 Markdown") from exc

    title = source_title(markdown, source_path.stem)
    article_markdown, metadata = strip_front_matter(markdown)
    fallback_brief = initial_brief(markdown, title, metadata)
    presentation = load_brief(presentation_path, fallback_brief)
    validate_brief(presentation)

    md, renderer = create_markdown_renderer(source_path.parent)
    article_html, state = md.parse(article_markdown)
    if not isinstance(article_html, str):
        raise ValueError("Markdown renderer did not return HTML")
    toc_items = list(state.env.get("toc_items", []))
    validate_source_bindings(presentation, toc_items)

    featured_html = ""
    featured = presentation.get("featured_diagram")
    if isinstance(featured, dict):
        featured_html = renderer.render_diagram(
            str(featured["source"]),
            title=str(featured.get("title") or "结构总览"),
            caption=str(featured.get("caption") or ""),
            featured=True,
        )

    stats = source_stats(markdown)
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    rendered_at = datetime.now().astimezone().isoformat(timespec="seconds")
    manifest = {
        "schema_version": "2.0",
        "renderer_version": VERSION,
        "generated_at": rendered_at,
        "source": {
            "path": str(source_path),
            "sha256": source_sha256,
            "bytes": len(source_bytes),
            "modified_at": datetime.fromtimestamp(source_path.stat().st_mtime)
            .astimezone()
            .isoformat(timespec="seconds"),
            "heading_count": stats["headings"],
        },
        "document": {
            "title": title,
            "lang": lang,
            "archetype": presentation.get("archetype", "document"),
            "rendered_heading_count": len(source_headings(markdown)),
            "toc_heading_count": len(toc_items),
            "table_count": stats["tables"],
            "diagram_count": renderer.diagram_count,
            "code_block_count": renderer.code_count + renderer.diagram_count,
            "reading_minutes": stats["reading_minutes"],
        },
        "presentation": {
            "design_read": presentation.get("design_read"),
            "source_binding_count": sum(
                len(presentation.get(group, [])) for group in FIELD_GUIDE_LIMITS
            ),
        },
        "assets": {
            "embedded_local_images": renderer.local_images,
            "degraded_remote_or_missing_images": renderer.degraded_images,
            "mistune": MISTUNE_VERSION,
            "mermaid": MERMAID_VERSION,
        },
    }

    template = (ASSETS_DIR / "report.html").read_text(encoding="utf-8")
    css = (ASSETS_DIR / "report.css").read_text(encoding="utf-8")
    app_js = (ASSETS_DIR / "report.js").read_text(encoding="utf-8")
    mermaid_js = (ASSETS_DIR / "mermaid.min.js").read_text(encoding="utf-8")

    status = (
        presentation.get("status") if isinstance(presentation.get("status"), dict) else {}
    )
    field_toc = render_field_toc(presentation)
    design_read = presentation.get("design_read", {})
    replacements = {
        "LANG": escape(lang, quote=True),
        "ARCHETYPE": escape(str(presentation.get("archetype", "document")), quote=True),
        "TITLE": escape(title),
        "TITLE_ATTR": escape(title, quote=True),
        "EYEBROW": escape(str(presentation.get("eyebrow") or "Research field guide")),
        "DECK": escape(str(presentation.get("deck") or "")),
        "SUMMARY": escape(str(presentation.get("summary") or "")),
        "NEXT_MOVE": escape(str(presentation.get("next_move") or "")),
        "NARRATIVE_AXIS": escape(str(design_read.get("narrative_axis") or "")),
        "STATUS": render_status(status),
        "HIGHLIGHTS": render_highlights(presentation.get("highlights", [])),
        "FEATURED_VISUAL": featured_html
        + render_hero_image(presentation.get("hero_image")),
        "SYSTEM_FLOW": render_system_flow(
            presentation.get("system_flow", []),
            toc_items,
        ),
        "FIELD_PRESENTATION": render_field_presentation(presentation, toc_items),
        "SOURCE_META": render_meta(metadata),
        "SOURCE_NAME": escape(source_path.name),
        "SOURCE_PATH": escape(str(source_path)),
        "SOURCE_SHA": escape(source_sha256),
        "SOURCE_SHA_SHORT": escape(source_sha256[:12]),
        "RENDERED_AT": escape(rendered_at),
        "READING_MINUTES": str(stats["reading_minutes"]),
        "SECTION_COUNT": str(stats["sections"]),
        "TABLE_COUNT": str(stats["tables"]),
        "DIAGRAM_COUNT": str(stats["diagrams"]),
        "READING_PATH": render_reading_path(
            presentation.get("reading_path", []),
            toc_items,
        ),
        "TOC": render_toc(toc_items, field_toc),
        "ARTICLE": article_html,
        "SOURCE_MARKDOWN": escape(markdown),
        "MANIFEST_JSON": json_for_script(manifest),
        "CSS": css,
        "MERMAID_JS": inline_script(mermaid_js),
        "APP_JS": inline_script(app_js),
    }
    html = template
    for key, value in replacements.items():
        html = html.replace("{{" + key + "}}", value)
    unresolved = sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", html)))
    if unresolved:
        raise ValueError("unresolved template placeholders: " + ", ".join(unresolved))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    manifest["output"] = {"path": str(output_path), "bytes": output_path.stat().st_size}
    return manifest


def default_output(source: Path) -> Path:
    digest = hashlib.sha256(str(source.resolve()).encode("utf-8")).hexdigest()[:10]
    return (
        Path(tempfile.gettempdir())
        / "to-html"
        / f"{source.stem}-{digest}.html"
    )


def write_initial_presentation(source: Path, output: Path, force: bool = False) -> Path:
    source = source.expanduser().resolve()
    output = output.expanduser().resolve()
    if output.exists() and not force:
        raise ValueError(f"presentation already exists; use --force to replace it: {output}")
    markdown = source.read_text(encoding="utf-8")
    title = source_title(markdown, source.stem)
    _, metadata = strip_front_matter(markdown)
    payload = initial_presentation(markdown, title, metadata)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Turn Markdown into a self-contained HTML reading preview."
    )
    parser.add_argument("source", type=Path, help="UTF-8 Markdown source")
    parser.add_argument(
        "--presentation",
        "--brief",
        dest="presentation",
        type=Path,
        help="optional content presentation JSON",
    )
    parser.add_argument("--output", type=Path, help="output HTML path")
    parser.add_argument("--lang", default="zh-CN", help="HTML language tag")
    parser.add_argument(
        "--init-presentation",
        "--init-brief",
        dest="init_presentation",
        type=Path,
        help="write a field-guide presentation draft and exit",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace an existing presentation draft",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.init_presentation:
            output = write_initial_presentation(
                args.source,
                args.init_presentation,
                force=args.force,
            )
            print(json.dumps({"ok": True, "presentation": str(output)}, ensure_ascii=False))
            return 0
        output = args.output or default_output(args.source)
        manifest = render_report(args.source, output, args.presentation, args.lang)
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "ok": True,
                "html": manifest["output"]["path"],
                "source": manifest["source"]["path"],
                "source_sha256": manifest["source"]["sha256"],
                "bytes": manifest["output"]["bytes"],
                "warnings": manifest["assets"]["degraded_remote_or_missing_images"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
