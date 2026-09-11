#!/usr/bin/env python3
"""Render a source-learning study using only the Python standard library."""

import argparse
import html
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import quote, urlsplit

from architecture import render_architecture
from source_reading import highlight_lines, language_for
from study_text import INLINE, term_ids, prose_values


ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r"[a-z][a-z0-9-]*\Z")
# Inline SVG favicon keeps the single-file promise: no external asset, no network.
FAVICON = "data:image/svg+xml," + quote(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    '<rect width="64" height="64" rx="14" fill="#20263a"/>'
    '<text x="32" y="45" font-family="Georgia,serif" font-style="italic" font-size="40" '
    'text-anchor="middle" fill="#f8f7f3">L</text></svg>', safe="")
KINDS = {"implementation", "docs", "test", "inference", "execution"}
LABELS = {
    "en": dict(overview="Overview", mechanisms="Explore a mechanism", scope="Study scope",
               map="How the parts cooperate", map_hint="Select a part to inspect its role and sources.",
               reading="Reading path", reading_hint="Steps organize the explanation; conditions below describe runtime transitions.",
               flow="Conditional flow", flow_hint="Only the conditions and destinations recorded in this study are shown.",
               input="Input", output="Output", state="State & ownership", branches="Conditions & transitions",
               principle="Why it works", limits="Constraints & limits", sources="Source evidence",
               next="Where to read next", deeper="Explore this mechanism", previous="Previous step", following="Next step",
               print="Print / PDF", skip="Skip to content", relations="Authored relationships", open="Open source",
               implementation="Source inspected", docs="Documented intent", test="Test inspected",
               inference="Inference", execution="Executed check", artifact="Generated reading view · learn-project",
               nojs="JavaScript is disabled. The complete study remains readable below.", step="Step"),
    "zh-CN": dict(overview="项目总览", mechanisms="深入核心机制", scope="研究范围",
                  map="这些部分如何协作", map_hint="选择一个部分，查看职责、来源和相关机制。",
                  reading="沿着实现读下去", reading_hint="步骤组织阅读顺序；实际运行的转移条件见下方说明。",
                  flow="条件流程示意", flow_hint="这里只展示本次研究明确记录的条件与去向。",
                  input="输入", output="输出", state="状态与归属", branches="条件与去向",
                  principle="原理与设计取舍", limits="适用条件与边界", sources="源码依据",
                  next="接下来读哪里", deeper="深入这个机制", previous="上一步", following="下一步",
                  print="打印 / PDF", skip="跳到正文", relations="已梳理的关系", open="打开源码",
                  implementation="源码已阅读", docs="文档描述", test="测试已阅读",
                  inference="推断", execution="实际执行", artifact="项目学习页 · learn-project",
                  nojs="JavaScript 已禁用，下方仍可阅读完整研究内容。", step="步骤"),
}


def validate(data):
    """Validate the presentation contract, not the research conclusions."""
    def obj(value, where):
        if not isinstance(value, dict):
            raise ValueError(f"{where}: expected an object")
        return value

    def string(value, where):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{where}: expected non-empty text")

    def array(value, where):
        if not isinstance(value, list):
            raise ValueError(f"{where}: expected an array")
        return value

    def prose(value, where):
        for item in array(value, where):
            string(item, where)

    def collection(value, where):
        seen = set()
        for item in array(value, where):
            obj(item, where)
            key = item.get("id")
            if not isinstance(key, str) or not ID.fullmatch(key) or key in seen:
                raise ValueError(f"{where}: invalid or duplicate id {key!r}")
            seen.add(key)
        return seen

    def url(value, where):
        string(value, where)
        parsed = urlsplit(value)
        if (parsed.scheme not in {"http", "https"} or not parsed.netloc or
                any(ord(c) < 32 or c.isspace() for c in value)):
            raise ValueError(f"{where}: only absolute HTTP(S) URLs are supported")

    obj(data, "study")
    if type(data.get("version")) is not int or data["version"] != 1:
        raise ValueError("version: expected 1")
    project = obj(data.get("project"), "project")
    for key in ("name", "revision", "scope"):
        string(project.get(key), f"project.{key}")
    if project.get("language", "en") not in LABELS:
        raise ValueError("project.language: expected en or zh-CN")
    if "url" in project:
        url(project["url"], "project.url")
    for key in ("title", "summary"):
        string(data.get(key), key)
    prose(data.get("next"), "next")
    evidence_ids = collection(data.get("evidence"), "evidence")

    def refs(value, where):
        for ref in array(value, where):
            if not isinstance(ref, str) or ref not in evidence_ids:
                raise ValueError(f"{where}: unknown evidence {ref!r}")

    for source in data["evidence"]:
        for key in ("label", "supports"):
            string(source.get(key), f"evidence.{key}")
        if source.get("kind") not in KINDS:
            raise ValueError("evidence.kind: unsupported evidence kind")
        for key in ("path", "excerpt"):
            if key in source:
                string(source[key], f"evidence.{key}")
        if "url" in source:
            url(source["url"], "evidence.url")
        if "lines" in source:
            lines = source["lines"]
            if (not isinstance(lines, list) or len(lines) != 2 or
                    any(type(n) is not int or n < 1 for n in lines) or lines[1] < lines[0]):
                raise ValueError("evidence.lines: expected positive [start, end]")
            if "excerpt" in source and len(source["excerpt"].splitlines()) != lines[1] - lines[0] + 1:
                raise ValueError(f"evidence {source['id']}: excerpt length does not match lines")

    for source in data["evidence"]:
        for line in array(source.get("focus_lines", []), "evidence.focus_lines"):
            if (type(line) is not int or "lines" not in source or
                    not source["lines"][0] <= line <= source["lines"][1]):
                raise ValueError("evidence.focus_lines: line outside excerpt range")
        if "language" in source:
            string(source["language"], "evidence.language")
        if "reading_goal" in source:
            string(source["reading_goal"], "evidence.reading_goal")
        for annotation in array(source.get("annotations", []), "evidence.annotations"):
            obj(annotation, "annotation")
            bounds = annotation.get("lines")
            if (not isinstance(bounds, list) or len(bounds) != 2 or
                    any(type(n) is not int for n in bounds) or "lines" not in source or
                    "excerpt" not in source or not source["lines"][0] <= bounds[0] <= bounds[1] <= source["lines"][1]):
                raise ValueError("annotation.lines: outside source excerpt")
            string(annotation.get("body"), "annotation.body")
    mechanism_ids = collection(data.get("mechanisms"), "mechanisms")
    if "overview" in mechanism_ids:
        raise ValueError("mechanism id 'overview' is reserved for navigation")
    overview = obj(data.get("overview"), "overview")
    prose(overview.get("body"), "overview.body")
    node_ids = collection(overview.get("nodes"), "overview.nodes")
    for node in overview["nodes"]:
        for key in ("title", "summary"):
            string(node.get(key), f"node.{key}")
        refs(node.get("evidence", []), "node.evidence")
        if "mechanism" in node and node["mechanism"] not in mechanism_ids:
            raise ValueError(f"node {node['id']}: unknown mechanism")
    occupied = set()
    for node in overview["nodes"]:
        if "caption" in node:
            string(node["caption"], "node.caption")
        if "position" in node:
            position = node["position"]
            if (not isinstance(position, list) or len(position) != 2 or
                    any(type(n) is not int or not 0 <= n <= 20 for n in position)):
                raise ValueError("node.position: expected nonnegative [column, row] up to 20")
            if tuple(position) in occupied:
                raise ValueError("node.position: overlapping nodes")
            occupied.add(tuple(position))
    if occupied and len(occupied) != len(overview["nodes"]):
        raise ValueError("node.position: provide positions for all nodes or none")
    for edge in array(overview.get("edges"), "overview.edges"):
        obj(edge, "edge")
        if edge.get("from") not in node_ids or edge.get("to") not in node_ids:
            raise ValueError("edge: unknown endpoint")
        string(edge.get("label"), "edge.label")
        if "diagram_label" in edge:
            string(edge["diagram_label"], "edge.diagram_label")
        if edge.get("role", "primary") not in {"primary", "support"}:
            raise ValueError("edge.role: expected primary or support")
        refs(edge.get("evidence", []), "edge.evidence")
    collection(overview.get("paths", []), "overview.paths")
    for path in overview.get("paths", []):
        string(path.get("title"), "path.title")
        string(path.get("summary"), "path.summary")
        indices = array(path.get("edges"), "path.edges")
        if not indices or len(set(str(i) for i in indices)) != len(indices):
            raise ValueError("path.edges: expected distinct edge indices")
        for index in indices:
            if type(index) is not int or not 0 <= index < len(overview["edges"]):
                raise ValueError("path.edges: unknown edge index")
    for mechanism in data["mechanisms"]:
        for key in ("title", "question", "answer"):
            string(mechanism.get(key), f"mechanism.{key}")
        for key in ("principle", "limits"):
            prose(mechanism.get(key, []), f"mechanism.{key}")
        refs(mechanism.get("evidence", []), "mechanism.evidence")
        step_ids = collection(mechanism.get("steps"), "mechanism.steps")
        for step in mechanism["steps"]:
            string(step.get("title"), "step.title")
            prose(step.get("body"), "step.body")
            refs(step.get("evidence", []), "step.evidence")
            for key in ("input", "output", "state"):
                if key in step:
                    string(step[key], f"step.{key}")
            for branch in array(step.get("branches", []), "step.branches"):
                obj(branch, "branch")
                for key in ("condition", "effect"):
                    string(branch.get(key), f"branch.{key}")
                if "target" in branch and branch["target"] not in step_ids:
                    raise ValueError(f"step {step['id']}: unknown branch target")
    terms = collection(data.get("terms", []), "terms")
    for term in data.get("terms", []):
        for key in ("label", "definition"):
            string(term.get(key), f"term.{key}")
    for mechanism in data["mechanisms"]:
        if "nav_title" in mechanism:
            string(mechanism["nav_title"], "mechanism.nav_title")
    groups = collection(overview.get("groups", []), "overview.groups")
    for group in overview.get("groups", []):
        string(group.get("title"), "group.title")
        if "summary" in group:
            string(group["summary"], "group.summary")
    for node in overview["nodes"]:
        if "group" in node and node["group"] not in groups:
            raise ValueError("node.group: unknown group")
    for item in array(overview.get("journey", []), "overview.journey"):
        obj(item, "journey item")
        string(item.get("title"), "journey.title")
        string(item.get("body"), "journey.body")
        refs(item.get("evidence", []), "journey.evidence")
        if "mechanism" in item and item["mechanism"] not in mechanism_ids:
            raise ValueError("journey.mechanism: unknown mechanism")
    for value in prose_values(data):
        unknown = term_ids(value) - terms
        if unknown:
            raise ValueError(f"unknown term: {sorted(unknown)[0]}")
    for key, value in obj(data.get("frontmatter", {}), "frontmatter").items():
        if not re.fullmatch(r"[a-z][a-z0-9_-]*", key):
            raise ValueError("frontmatter: invalid key")
        if isinstance(value, list):
            prose(value, "frontmatter value")
        else:
            string(value, "frontmatter value")
    return data


def render(data):
    e = lambda value: html.escape(str(value), quote=True)
    labels = LABELS[data["project"].get("language", "en")]
    t = lambda key: e(labels[key])
    terms = {item["id"]: item for item in data.get("terms", [])}
    def inline(value):
        parts, end = [], 0
        for match in INLINE.finditer(value):
            parts.append(e(value[end:match.start()]))
            if match[1] is not None:
                parts.append(f"<code>{e(match[1])}</code>")
            elif match[2] is not None:
                parts.append(f"<strong>{e(match[2])}</strong>")
            else:
                label = match[4] or terms[match[3]]["label"]
                parts.append(f'<a class="term" href="#term/{match[3]}">{e(label)}</a>')
            end = match.end()
        return "".join(parts) + e(value[end:])
    paragraphs = lambda rows: "".join(f"<p>{inline(row)}</p>" for row in rows)
    zh = data["project"].get("language") == "zh-CN"
    ui = lambda cn, en: e(cn if zh else en)
    def fingerprint(value, kind):
        refs_used = set()
        def collect(item):
            if isinstance(item, dict):
                refs_used.update(item.get("evidence", []))
                for key, nested in item.items():
                    if key != "evidence":
                        collect(nested)
            elif isinstance(item, list):
                for nested in item:
                    collect(nested)
        collect(value)
        sources_used = [evidence[ref] for ref in sorted(refs_used)]
        prose = list(prose_values(value, kind))
        if kind == "overview":
            prose.append(value["summary"])
        for source in sources_used:
            prose.extend(prose_values(source, "evidence"))
        used_terms = set().union(*(term_ids(text) for text in prose))
        payload = [value, data["project"]["revision"], sources_used,
                   [terms[ref] for ref in sorted(used_terms)]]
        return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]
    def actions():
        return f'<div class="chapter-actions"><button type="button" data-reading-state="read">{ui("标为读过", "Mark as read")}</button><button type="button" data-reading-state="question">{ui("还有疑问", "Have a question")}</button><span class="chapter-status" role="status"></span><button type="button" class="copy-question">{ui("带着这章继续提问", "Continue this question")}</button><span class="copy-status" role="status"></span></div>'

    evidence = {item["id"]: item for item in data["evidence"]}

    source_occurrences = {}

    def sources(refs):
        if not refs:
            return ""
        items = []
        for ref in dict.fromkeys(refs):
            source = evidence[ref]
            source_occurrences[ref] = source_occurrences.get(ref, 0) + 1
            source_id = f"source/{ref}/{source_occurrences[ref]}"
            location = source.get("path", "")
            if "lines" in source:
                location += f" : {source['lines'][0]}–{source['lines'][1]}"
            code = ""
            if "excerpt" in source:
                start = source.get("lines", [1])[0]
                language = language_for(source)
                display_language = source.get("language", language).strip()
                language_label = e(display_language) + (" · " + ui("暂无语法高亮", "Plain text fallback") if language == "plain" and display_language.lower() not in {"plain", "text", "txt"} else "")
                colored = highlight_lines(source["excerpt"], language)
                lines = "".join(f'<span class="code-line{" is-highlight" if i in source.get("focus_lines", []) else ""}" data-line="{i}"><span class="line-number" aria-hidden="true">{i}</span><span>{line}</span></span>'
                                for i, line in enumerate(colored, start))
                goal = f'<p class="source-reading-goal"><strong>{ui("阅读目标", "Reading goal")}</strong> {inline(source["reading_goal"])}</p>' if source.get("reading_goal") else ""
                notes = "".join(f'<li><button type="button" class="source-annotation" data-line-start="{a["lines"][0]}" data-line-end="{a["lines"][1]}" aria-pressed="false">L{a["lines"][0]}–{a["lines"][1]}</button><span class="source-annotation-text">{inline(a["body"])}</span></li>' for a in source.get("annotations", []))
                notes = f'<div class="source-annotations"><h5>{ui("阅读导注 · 非原文注释", "Reading notes · not original comments")}</h5><ol>{notes}</ol></div>' if notes else ""
                code = f'{goal}<div class="source-code-label">{language_label} · {ui("原始摘录", "Original excerpt")}</div><pre tabindex="0"><code data-source-text="{e(json.dumps(source["excerpt"], ensure_ascii=False))}">{lines}</code></pre>{notes}'
            link = (f'<a class="source-link" href="{e(source["url"])}" target="_blank" rel="noopener noreferrer">{t("open")} ↗</a>'
                    if "url" in source else "")
            items.append(f'<details class="evidence" id="{source_id}" data-evidence="{e(ref)}"><summary><span class="badge">{t(source["kind"])}</span> {e(source["label"])}</summary>'
                         f'<p class="source-location">{e(location)}</p><p>{inline(source["supports"])}</p>{code}<button type="button" class="copy-source">{ui("复制摘录", "Copy excerpt")}</button><span class="copy-status" role="status"></span>{link}</details>')
        return f'<div class="sources"><h4>{t("sources")}</h4>{"".join(items)}</div>'

    project = data["project"]
    project_link = (f'<a class="project-name" href="{e(project["url"])}" target="_blank" rel="noopener noreferrer">{e(project["name"])}</a>'
                    if "url" in project else f'<span class="project-name">{e(project["name"])}</span>')
    # The overview link uses the same number/title/state grid as mechanism
    # links; a bare text node would land in the 26px number column and wrap
    # one character per line.
    nav = (f'<a href="#overview" data-nav="overview"><span class="nav-number" aria-hidden="true"></span>'
           f'<span class="nav-title">{t("overview")}</span><span class="nav-state" aria-hidden="true"></span></a>')
    if data["mechanisms"]:
        nav += f'<p class="nav-label">{t("mechanisms")}</p>'
        for i, mechanism in enumerate(data["mechanisms"], 1):
            nav += f'<a href="#mechanism/{mechanism["id"]}" data-nav="{mechanism["id"]}"><span class="nav-number">{i:02}</span><span class="nav-title">{e(mechanism.get("nav_title", mechanism["title"]))}</span><span class="nav-state" aria-hidden="true"></span></a>'

    overview = data["overview"]
    nodes = render_architecture(overview, zh, terms)
    by_node = {node["id"]: node for node in overview["nodes"]}
    edges = "".join(f'<li id="relationship/{i}" data-edge-index="{i}" data-edge-from="{edge["from"]}" data-edge-to="{edge["to"]}"><span>{e(by_node[edge["from"]]["title"])}</span><span class="edge-label"> — {inline(edge["label"])} → </span><span>{e(by_node[edge["to"]]["title"])}</span><details class="edge-evidence"><summary>{t("sources")}</summary>{sources(edge.get("evidence", []))}</details></li>'
                    for i, edge in enumerate(overview["edges"]))
    paths = overview.get("paths", [])
    path_controls = ""
    if paths:
        options = "".join(f'<option value="{e(path["id"])}">{e(path["title"])}</option>' for path in paths)
        path_controls = f'<label class="map-path-control">{ui("查看流向", "Follow a flow")} <select id="map-path"><option value="">{ui("全部架构关系", "All relationships")}</option>{options}</select></label>'
        for path in paths:
            path_controls += f'<div class="map-path-description" data-map-path="{e(path["id"])}" data-path-edges="{e(json.dumps(path["edges"]))}" hidden><p>{inline(path["summary"])}</p><ol>{"".join(f"<li>{inline(overview['edges'][i]['label'])}</li>" for i in path["edges"])}</ol></div>'
    node_details = ""
    for node in overview["nodes"]:
        deeper = (f'<a class="deeper-link" href="#mechanism/{node["mechanism"]}">{t("deeper")} →</a>' if "mechanism" in node else "")
        node_details += f'<section class="node-detail" data-node-detail="{node["id"]}" id="node/{node["id"]}"><h3 tabindex="-1">{e(node["title"])}</h3><p>{inline(node["summary"])}</p>{deeper}{sources(node.get("evidence", []))}</section>'
    map_html = (f'<section class="map-section"><h2>{t("map")}</h2><p class="hint">{t("map_hint")}</p>{path_controls}<div class="map-board">{nodes}</div><p class="map-legend">{ui("实线：主要协作通路 · 虚线：启动或辅助关系。箭头表达关系方向，不代表全局执行顺序；点击连线查看依据。", "Solid: primary collaboration · Dashed: startup or supporting relations. Arrows are not a global execution order; select an edge for evidence.")}</p><a class="map-clear" href="#overview">{ui("查看全部关系", "Show all relationships")}</a>'
                f'<details class="relationships"><summary>{t("relations")}</summary><ul>{edges}</ul></details>{node_details}</section>' if nodes else "")
    journey = ""
    for i, item in enumerate(overview.get("journey", []), 1):
        link = f'<a href="#mechanism/{item["mechanism"]}">{t("deeper")} →</a>' if "mechanism" in item else ""
        journey += f'<li><span class="journey-number">{i:02}</span><div><h3>{e(item["title"])}</h3><p>{inline(item["body"])}</p>{link}{sources(item.get("evidence", []))}</div></li>'
    if journey:
        journey = f'<section class="journey"><p class="eyebrow">{ui("跟随一个具体任务", "Follow one task")}</p><h2>{ui("一次任务怎样完成", "How a task moves through the system")}</h2><ol>{journey}</ol></section>'
    recommendations = "".join(f'<a class="mechanism-entry" href="#mechanism/{m["id"]}"><span class="entry-number">{i:02}</span><span><strong>{e(m["title"])}</strong><span>{e(m["question"])}</span></span><span aria-hidden="true">↗</span></a>' for i, m in enumerate(data["mechanisms"], 1))
    next_html = f'<section class="next-reading"><h2>{t("next")}</h2>{paragraphs(data["next"])}</section>' if data["next"] else ""
    sections = f'<section class="view" data-view="overview" data-fingerprint="{fingerprint(dict(overview, title=data["title"], summary=data["summary"]), "overview")}" id="overview"><header class="intro"><p class="eyebrow">{e(project["name"])} / {t("overview")}</p><h1 tabindex="-1">{e(data["title"])}</h1><p class="lead">{inline(data["summary"])}</p></header>{map_html}{journey}<div class="overview-prose">{paragraphs(overview["body"])}</div>'
    if recommendations:
        sections += f'<section class="explore"><h2>{t("mechanisms")}</h2>{recommendations}</section>'
    sections += next_html + actions() + '</section>'

    for mechanism in data["mechanisms"]:
        mid = mechanism["id"]
        steps_nav = ""
        panels = ""
        transitions = []
        step_titles = {step["id"]: step["title"] for step in mechanism["steps"]}
        for i, step in enumerate(mechanism["steps"]):
            route = f'mechanism/{mid}/step/{step["id"]}'
            steps_nav += f'<a href="#{route}" data-step-link="{step["id"]}"><span>{i + 1:02}</span>{e(step["title"])}</a>'
            facts = "".join(f'<div><dt>{t(key)}</dt><dd>{inline(step[key])}</dd></div>' for key in ("input", "output", "state") if key in step)
            branches = ""
            for branch in step.get("branches", []):
                target = f'<a href="#mechanism/{mid}/step/{branch["target"]}">→ {e(next(s["title"] for s in mechanism["steps"] if s["id"] == branch["target"]))}</a>' if "target" in branch else ""
                branches += f'<li><strong>{inline(branch["condition"])}</strong><p>{inline(branch["effect"])}</p>{target}</li>'
                destination = (f'<a href="#mechanism/{mid}/step/{branch["target"]}">{e(step_titles[branch["target"]])}</a>'
                               if "target" in branch else f'<span class="flow-terminal">{inline(branch["effect"])}</span>')
                transitions.append(f'<li data-flow-step="{step["id"]}"><a href="#{route}">{e(step["title"])}</a><span class="flow-condition">{inline(branch["condition"])}<span aria-hidden="true">⟶</span></span>{destination}</li>')
            if branches:
                branches = f'<div class="branches"><h4>{t("branches")}</h4><ul>{branches}</ul></div>'
            pager = ""
            for offset, label in ((-1, "previous"), (1, "following")):
                j = i + offset
                if 0 <= j < len(mechanism["steps"]):
                    pager += f'<a href="#mechanism/{mid}/step/{mechanism["steps"][j]["id"]}">{t(label)} {"←" if offset < 0 else "→"}</a>'
            panels += f'<section class="step-panel" id="{route}" data-step="{step["id"]}"><p class="eyebrow">{t("step")} {i + 1:02} / {len(mechanism["steps"]):02}</p><h3 tabindex="-1">{e(step["title"])}</h3>{paragraphs(step["body"])}<dl class="io-grid">{facts}</dl>{branches}{sources(step.get("evidence", []))}<nav class="step-pager" aria-label="{t("reading")}">{pager}</nav></section>'
        walkthrough = (f'<section class="walkthrough"><h2>{t("reading")}</h2><p class="hint">{t("reading_hint")}</p><div class="walkthrough-layout"><nav class="step-list" aria-label="{t("reading")}">{steps_nav}</nav><div class="step-panels">{panels}</div></div></section>' if panels else "")
        lesson = "".join(f'<section class="{key}"><h2>{t(key)}</h2>{paragraphs(mechanism.get(key, []))}</section>' for key in ("principle", "limits") if mechanism.get(key))
        flow = (f'<details class="flow-map"><summary>{t("flow")} <span>{len(transitions)}</span></summary><p class="hint">{t("flow_hint")}</p><ul>{"".join(transitions)}</ul></details>' if transitions else "")
        sections += f'<section class="view mechanism" data-view="{mid}" data-fingerprint="{fingerprint(mechanism, "mechanism")}" id="mechanism/{mid}"><header class="intro"><a class="back-link" href="#overview">← {t("overview")}</a><h1 tabindex="-1">{e(mechanism["title"])}</h1><p class="question">{e(mechanism["question"])}</p><p class="lead">{inline(mechanism["answer"])}</p></header>{flow}{walkthrough}<div class="lesson">{lesson}</div>{sources(mechanism.get("evidence", []))}{actions()}</section>'
    glossary = "".join(f'<details id="term/{term["id"]}" data-term="{term["id"]}"><summary>{e(term["label"])}</summary><p>{e(term["definition"])}</p></details>' for term in data.get("terms", []))
    if glossary:
        glossary = f'<section id="glossary" class="glossary"><h2>{ui("术语随查", "Glossary")}</h2>{glossary}</section>'
    dialogs = f'''<dialog id="search-dialog" aria-labelledby="search-title"><div class="dialog-header"><h2 id="search-title">{ui("搜索这份研究", "Search this study")}</h2><button type="button" data-close-search aria-label="{ui("关闭", "Close")}">×</button></div><label for="study-search">{ui("章节、概念或实现细节", "Chapters, concepts or implementation details")}</label><input id="study-search" type="search" autocomplete="off" placeholder="{ui("试试：上下文、ACP、错误", "Try: context, errors, protocol")}"><div class="search-results" aria-live="polite"></div></dialog><dialog id="term-dialog" aria-label="{ui("术语解释", "Term definition")}"><button type="button" data-close-term aria-label="{ui("关闭", "Close")}">×</button><div class="term-content"></div></dialog>'''
    css = "\n".join((ROOT / name).read_text(encoding="utf-8") for name in ("assets/reader.css", "assets/architecture.css", "assets/source-reading.css", "assets/search.css"))
    js = (ROOT / "assets/reader.js").read_text(encoding="utf-8")
    return f'''<!doctype html>
<html lang="{e(project.get('language', 'en'))}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(data['title'])} · learn-project</title><link rel="icon" href="{FAVICON}"><style>{css}</style></head>
<body data-study-key="{e(project.get('url', project['name']))}" data-revision="{e(project['revision'])}"><a class="skip-link" href="#content">{t('skip')}</a><header class="topbar"><a class="brand" href="#overview"><span class="brand-mark">L</span>learn<span>project</span></a>{project_link}<button type="button" class="search-button">{ui("搜索", "Search")} <kbd>⌘ K</kbd></button><button class="print-button" type="button">{t('print')}</button></header>
<div class="reading-shell"><aside class="sidebar"><a class="resume-link" hidden href="#overview">{ui("继续阅读", "Continue reading")}</a><output class="reading-progress"></output><nav aria-label="{t('reading')}">{nav}</nav><div class="revision"><span>{e(project['revision'][:10])}</span></div></aside><main id="content" tabindex="-1"><noscript><p>{t('nojs')}</p></noscript>{sections}{glossary}<footer class="scope"><h2>{t('scope')}</h2><p>{e(project['scope'])}</p><small>{t('artifact')}</small></footer></main></div>{dialogs}<script>{js}</script></body></html>'''


def markdown(data):
    """Generate the complete portable reading view from the same study."""
    # Raw study text never becomes embedded HTML in the export.
    escape_markdown = lambda text: re.sub(r"([\\`*_{}\[\]()#+!|>])", r"\\\1", html.escape(text, quote=False))
    term_by_id = {term["id"]: term for term in data.get("terms", [])}
    def inline_markdown(value):
        parts, end = [], 0
        for match in INLINE.finditer(value):
            parts.append(escape_markdown(value[end:match.start()]))
            if match[1] is not None:
                parts.append("`" + html.escape(match[1]) + "`")
            elif match[2] is not None:
                parts.append("**" + escape_markdown(match[2]) + "**")
            else:
                parts.append(escape_markdown(match[4] or term_by_id[match[3]]["label"]))
            end = match.end()
        return "".join(parts) + escape_markdown(value[end:])
    labels = LABELS[data["project"].get("language", "en")]
    out = [f'# {escape_markdown(data["title"])}', inline_markdown(data["summary"])]
    if data["mechanisms"]:
        out += ["## 目录" if data["project"].get("language") == "zh-CN" else "## Contents"]
        out += ["\n".join(f'- [{escape_markdown(m.get("nav_title", m["title"]))}](#mechanism-{m["id"]})' for m in data["mechanisms"])]
    out += [inline_markdown(p) for p in data["overview"]["body"]]
    refs = lambda ids: ", ".join(f'[{escape_markdown(ref)}](#evidence-{ref})' for ref in dict.fromkeys(ids))
    for group in data["overview"].get("groups", []):
        out += [f'### {escape_markdown(group["title"])}', inline_markdown(group.get("summary", ""))]
    for item in data["overview"].get("journey", []):
        out += [f'### {escape_markdown(item["title"])}', inline_markdown(item["body"]), refs(item.get("evidence", []))]
    for node in data["overview"]["nodes"]:
        out += [f'### {escape_markdown(node["title"])}', inline_markdown(node["summary"]), refs(node.get("evidence", []))]
    for edge in data["overview"]["edges"]:
        out += [escape_markdown(edge["from"]) + " — " + inline_markdown(edge["label"]) + " → " + escape_markdown(edge["to"]), refs(edge.get("evidence", []))]
    for path in data["overview"].get("paths", []):
        out += [f'### {escape_markdown(path["title"])}', inline_markdown(path["summary"])]
        out += ["\n".join(f'{order}. {inline_markdown(data["overview"]["edges"][index]["label"])}' for order, index in enumerate(path["edges"], 1))]
    for mechanism in data["mechanisms"]:
        out += [f'<a id="mechanism-{mechanism["id"]}"></a>', f'## {escape_markdown(mechanism["title"])}', escape_markdown(mechanism["question"]), inline_markdown(mechanism["answer"])]
        for step in mechanism["steps"]:
            out += [f'### {escape_markdown(step["title"])}'] + [inline_markdown(p) for p in step["body"]]
            for key in ("input", "output", "state"):
                if key in step:
                    out += [f'**{labels[key]}**: {inline_markdown(step[key])}']
            for branch in step.get("branches", []):
                target = f' → {branch["target"]}' if "target" in branch else ""
                out += [inline_markdown(branch["condition"]) + ": " + inline_markdown(branch["effect"]) + target]
            out += [refs(step.get("evidence", []))]
        for key in ("principle", "limits"):
            if mechanism.get(key):
                out += [f'### {labels[key]}'] + [inline_markdown(p) for p in mechanism[key]]
        out += [refs(mechanism.get("evidence", []))]
    for term in data.get("terms", []):
        out += [f'### {escape_markdown(term["label"])}', escape_markdown(term["definition"])]
    out += [f'## {labels["next"]}'] + [inline_markdown(p) for p in data["next"]]
    out += [f'## {labels["scope"]}', escape_markdown(data["project"]["revision"]), escape_markdown(data["project"]["scope"])]
    out += [f'## {labels["sources"]}']
    for source in data["evidence"]:
        out += [f'<a id="evidence-{source["id"]}"></a>', f'### {escape_markdown(source["label"])} · {labels[source["kind"]]}', inline_markdown(source["supports"])]
        if "path" in source:
            out += [escape_markdown(source["path"]) + (f' : {source["lines"][0]}–{source["lines"][1]}' if "lines" in source else "")]
        if "url" in source:
            safe_url = quote(source["url"], safe="/:#?=&%+@;,")
            out += [f'[{labels["open"]}]({safe_url})']
        if "excerpt" in source:
            fence = "`" * max(3, max((len(m[0]) + 1 for m in re.finditer(r"`+", source["excerpt"])), default=3))
            if source.get("reading_goal"):
                out += [inline_markdown(source["reading_goal"])]
            out += [f'{fence}\n{source["excerpt"]}\n{fence}']
            for annotation in source.get("annotations", []):
                out += [f'L{annotation["lines"][0]}–{annotation["lines"][1]} · ' + inline_markdown(annotation["body"])]
    frontmatter = ""
    if data.get("frontmatter"):
        frontmatter = "---\n" + "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in data["frontmatter"].items()) + "\n---\n\n"
    return frontmatter + "\n\n".join(part for part in out if part) + "\n"


def write_atomic(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("study", type=Path)
    parser.add_argument("--output", "-o", type=Path, help="HTML output; Markdown is written beside it")
    parser.add_argument("--check", action="store_true", help="Validate the data contract without writing")
    args = parser.parse_args()
    try:
        data = validate(json.loads(args.study.read_text(encoding="utf-8")))
        if args.check:
            print("Study format valid. Research claims and source contents are not verified.")
            return
        if args.output is None or args.output.suffix.lower() != ".html":
            raise ValueError("--output must be an .html path")
        md_path = args.output.with_suffix(".md")
        if args.study.resolve() in {args.output.resolve(), md_path.resolve()}:
            raise ValueError("output must not overwrite the input")
        if args.output.is_dir() or md_path.is_dir():
            raise ValueError("an output path is a directory")
        page, text = render(data), markdown(data)
        write_atomic(md_path, text)
        write_atomic(args.output, page)
        print(f"HTML: {args.output.resolve()}\nMarkdown: {md_path.resolve()}")
    except (ValueError, OSError, TypeError) as error:
        parser.exit(1, f"Study error: {error}\n")


if __name__ == "__main__":
    main()
