#!/usr/bin/env python3
"""Render a source-learning study using only the Python standard library."""

import argparse
import html
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import quote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r"[a-z][a-z0-9-]*\Z")
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
    for edge in array(overview.get("edges"), "overview.edges"):
        obj(edge, "edge")
        if edge.get("from") not in node_ids or edge.get("to") not in node_ids:
            raise ValueError("edge: unknown endpoint")
        string(edge.get("label"), "edge.label")
        refs(edge.get("evidence", []), "edge.evidence")
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
    return data


def render(data):
    e = lambda value: html.escape(str(value), quote=True)
    labels = LABELS[data["project"].get("language", "en")]
    t = lambda key: e(labels[key])
    paragraphs = lambda rows: "".join(f"<p>{e(row)}</p>" for row in rows)
    evidence = {item["id"]: item for item in data["evidence"]}

    def sources(refs):
        if not refs:
            return ""
        items = []
        for ref in dict.fromkeys(refs):
            source = evidence[ref]
            location = source.get("path", "")
            if "lines" in source:
                location += f" : {source['lines'][0]}–{source['lines'][1]}"
            code = ""
            if "excerpt" in source:
                start = source.get("lines", [1])[0]
                lines = "".join(f'<span class="code-line"><span class="line-number" aria-hidden="true">{i}</span><span>{e(line)}</span></span>'
                                for i, line in enumerate(source["excerpt"].splitlines(), start))
                code = f'<pre tabindex="0"><code>{lines}</code></pre>'
            link = (f'<a class="source-link" href="{e(source["url"])}" target="_blank" rel="noopener noreferrer">{t("open")} ↗</a>'
                    if "url" in source else "")
            items.append(f'<details class="evidence" data-evidence="{e(ref)}"><summary><span class="badge">{t(source["kind"])}</span> {e(source["label"])}</summary>'
                         f'<p class="source-location">{e(location)}</p><p>{e(source["supports"])}</p>{code}{link}</details>')
        return f'<div class="sources"><h4>{t("sources")}</h4>{"".join(items)}</div>'

    project = data["project"]
    project_link = (f'<a class="project-name" href="{e(project["url"])}" target="_blank" rel="noopener noreferrer">{e(project["name"])}</a>'
                    if "url" in project else f'<span class="project-name">{e(project["name"])}</span>')
    nav = f'<a href="#overview" data-nav="overview">{t("overview")}</a>'
    if data["mechanisms"]:
        nav += f'<p class="nav-label">{t("mechanisms")}</p>'
        for i, mechanism in enumerate(data["mechanisms"], 1):
            nav += f'<a href="#mechanism/{mechanism["id"]}" data-nav="{mechanism["id"]}"><span class="nav-number">{i:02}</span>{e(mechanism["title"])}</a>'

    overview = data["overview"]
    nodes = "".join(f'<a class="map-node" data-node="{node["id"]}" href="#node/{node["id"]}"><span class="node-index">{i:02}</span><strong>{e(node["title"])}</strong><span>{e(node["summary"])}</span></a>'
                    for i, node in enumerate(overview["nodes"], 1))
    by_node = {node["id"]: node for node in overview["nodes"]}
    edges = "".join(f'<li data-edge-from="{edge["from"]}" data-edge-to="{edge["to"]}"><span>{e(by_node[edge["from"]]["title"])}</span><span class="edge-label"> — {e(edge["label"])} → </span><span>{e(by_node[edge["to"]]["title"])}</span>{sources(edge.get("evidence", []))}</li>'
                    for edge in overview["edges"])
    node_details = ""
    for node in overview["nodes"]:
        deeper = (f'<a class="deeper-link" href="#mechanism/{node["mechanism"]}">{t("deeper")} →</a>' if "mechanism" in node else "")
        node_details += f'<section class="node-detail" data-node-detail="{node["id"]}" id="node/{node["id"]}"><h3 tabindex="-1">{e(node["title"])}</h3><p>{e(node["summary"])}</p>{deeper}{sources(node.get("evidence", []))}</section>'
    map_html = (f'<section class="map-section"><h2>{t("map")}</h2><p class="hint">{t("map_hint")}</p><div class="map-board"><svg class="map-lines" aria-hidden="true"></svg>{nodes}</div>'
                f'<details class="relationships" open><summary>{t("relations")}</summary><ul>{edges}</ul></details>{node_details}</section>' if nodes else "")
    recommendations = "".join(f'<a class="mechanism-entry" href="#mechanism/{m["id"]}"><span class="entry-number">{i:02}</span><span><strong>{e(m["title"])}</strong><span>{e(m["question"])}</span></span><span aria-hidden="true">↗</span></a>' for i, m in enumerate(data["mechanisms"], 1))
    next_html = f'<section class="next-reading"><h2>{t("next")}</h2>{paragraphs(data["next"])}</section>' if data["next"] else ""
    sections = f'<section class="view" data-view="overview" id="overview"><header class="intro"><p class="eyebrow">{e(project["name"])} / {t("overview")}</p><h1 tabindex="-1">{e(data["title"])}</h1><p class="lead">{e(data["summary"])}</p></header><div class="overview-prose">{paragraphs(overview["body"])}</div>{map_html}'
    if recommendations:
        sections += f'<section class="explore"><h2>{t("mechanisms")}</h2>{recommendations}</section>'
    sections += next_html + '</section>'

    for mechanism in data["mechanisms"]:
        mid = mechanism["id"]
        steps_nav = ""
        panels = ""
        transitions = []
        step_titles = {step["id"]: step["title"] for step in mechanism["steps"]}
        for i, step in enumerate(mechanism["steps"]):
            route = f'mechanism/{mid}/step/{step["id"]}'
            steps_nav += f'<a href="#{route}" data-step-link="{step["id"]}"><span>{i + 1:02}</span>{e(step["title"])}</a>'
            facts = "".join(f'<div><dt>{t(key)}</dt><dd>{e(step[key])}</dd></div>' for key in ("input", "output", "state") if key in step)
            branches = ""
            for branch in step.get("branches", []):
                target = f'<a href="#mechanism/{mid}/step/{branch["target"]}">→ {e(next(s["title"] for s in mechanism["steps"] if s["id"] == branch["target"]))}</a>' if "target" in branch else ""
                branches += f'<li><strong>{e(branch["condition"])}</strong><p>{e(branch["effect"])}</p>{target}</li>'
                destination = (f'<a href="#mechanism/{mid}/step/{branch["target"]}">{e(step_titles[branch["target"]])}</a>'
                               if "target" in branch else f'<span class="flow-terminal">{e(branch["effect"])}</span>')
                transitions.append(f'<li data-flow-step="{step["id"]}"><a href="#{route}">{e(step["title"])}</a><span class="flow-condition">{e(branch["condition"])}<span aria-hidden="true">⟶</span></span>{destination}</li>')
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
        sections += f'<section class="view mechanism" data-view="{mid}" id="mechanism/{mid}"><header class="intro"><a class="back-link" href="#overview">← {t("overview")}</a><h1 tabindex="-1">{e(mechanism["title"])}</h1><p class="question">{e(mechanism["question"])}</p><p class="lead">{e(mechanism["answer"])}</p></header>{flow}{walkthrough}<div class="lesson">{lesson}</div>{sources(mechanism.get("evidence", []))}</section>'
    css = (ROOT / "assets/reader.css").read_text(encoding="utf-8")
    js = (ROOT / "assets/reader.js").read_text(encoding="utf-8")
    return f'''<!doctype html>
<html lang="{e(project.get('language', 'en'))}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(data['title'])} · learn-project</title><style>{css}</style></head>
<body><a class="skip-link" href="#content">{t('skip')}</a><header class="topbar"><a class="brand" href="#overview"><span class="brand-mark">L</span>learn<span>project</span></a>{project_link}<button class="print-button" type="button">{t('print')}</button></header>
<div class="reading-shell"><aside class="sidebar"><nav aria-label="{t('reading')}">{nav}</nav><div class="revision"><span>{e(project['revision'])}</span></div></aside><main id="content" tabindex="-1"><noscript><p>{t('nojs')}</p></noscript>{sections}<footer class="scope"><h2>{t('scope')}</h2><p>{e(project['scope'])}</p><small>{t('artifact')}</small></footer></main></div><script>{js}</script></body></html>'''


def markdown(data):
    """Generate the complete portable reading view from the same study."""
    # Raw study text never becomes embedded HTML in the export.
    esc = lambda text: re.sub(r"([\\`*_{}\[\]()#+!|>])", r"\\\1", html.escape(text, quote=False))
    labels = LABELS[data["project"].get("language", "en")]
    out = [f'# {esc(data["title"])}', esc(data["summary"])]
    out += [esc(p) for p in data["overview"]["body"]]
    refs = lambda ids: ", ".join(f'[{esc(ref)}](#evidence-{ref})' for ref in dict.fromkeys(ids))
    for node in data["overview"]["nodes"]:
        out += [f'### {esc(node["title"])}', esc(node["summary"]), refs(node.get("evidence", []))]
    for edge in data["overview"]["edges"]:
        out += [esc(f'{edge["from"]} — {edge["label"]} → {edge["to"]}'), refs(edge.get("evidence", []))]
    for mechanism in data["mechanisms"]:
        out += [f'## {esc(mechanism["title"])}', esc(mechanism["question"]), esc(mechanism["answer"])]
        for step in mechanism["steps"]:
            out += [f'### {esc(step["title"])}'] + [esc(p) for p in step["body"]]
            for key in ("input", "output", "state"):
                if key in step:
                    out += [f'**{labels[key]}**: {esc(step[key])}']
            for branch in step.get("branches", []):
                target = f' → {branch["target"]}' if "target" in branch else ""
                out += [esc(f'{branch["condition"]}: {branch["effect"]}{target}')]
            out += [refs(step.get("evidence", []))]
        for key in ("principle", "limits"):
            if mechanism.get(key):
                out += [f'### {labels[key]}'] + [esc(p) for p in mechanism[key]]
        out += [refs(mechanism.get("evidence", []))]
    out += [f'## {labels["next"]}'] + [esc(p) for p in data["next"]]
    out += [f'## {labels["scope"]}', esc(data["project"]["revision"]), esc(data["project"]["scope"])]
    out += [f'## {labels["sources"]}']
    for source in data["evidence"]:
        out += [f'<a id="evidence-{source["id"]}"></a>', f'### {esc(source["label"])} · {labels[source["kind"]]}', esc(source["supports"])]
        if "path" in source:
            out += [esc(source["path"]) + (f' : {source["lines"][0]}–{source["lines"][1]}' if "lines" in source else "")]
        if "url" in source:
            safe_url = quote(source["url"], safe="/:#?=&%+@;,")
            out += [f'[{labels["open"]}](<{safe_url}>)']
        if "excerpt" in source:
            fence = "`" * max(3, max((len(m[0]) + 1 for m in re.finditer(r"`+", source["excerpt"])), default=3))
            out += [f'{fence}\n{source["excerpt"]}\n{fence}']
    return "\n\n".join(part for part in out if part) + "\n"


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
