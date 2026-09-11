"""Deterministic SVG overview; coordinates arrange authored facts, never infer edges."""
import html
import unicodedata
import math

from study_text import plain_text


def wrapped(text, limit):
    lines, line, width = [], "", 0
    for char in text:
        size = 2 if unicodedata.east_asian_width(char) in "WF" else 1
        if width + size > limit and line:
            lines.append(line)
            line, width = "", 0
        line += char
        width += size
    return lines + ([line] if line else [])


def render_architecture(overview, zh, terms=None):
    terms = terms or {}
    e = lambda value: html.escape(str(value), quote=True)
    nodes = overview["nodes"]
    if not nodes:
        return ""
    groups = overview.get("groups", [])
    group_index = {group["id"]: i for i, group in enumerate(groups)}
    counters, positions = {}, {}
    for node in nodes:
        group = node.get("group", "")
        col = group_index.get(group, len(groups)) if groups else 0
        row = counters.get(group, 0)
        counters[group] = row + 1
        positions[node["id"]] = node.get("position", [col, row])
    # Room for real labels between nodes; the SVG scales but is never shrunk below readable size.
    w, h, dx, dy = 224, 90, 370, 174
    xy = {key: (48 + col * dx, 78 + row * dy) for key, (col, row) in positions.items()}
    width = max(x for x, y in xy.values()) + w + 48
    height = max(y for x, y in xy.values()) + h + 48
    bounds = [(0, 0, width, height)]
    def include(x, y, box_width=0, box_height=0):
        bounds.append((x, y, x + box_width, y + box_height))
    def text_width(text, font_size):
        # Conservative advance including Latin wide glyphs, CJK and fallback fonts.
        return len(text) * font_size * 1.05
    parts = [f'<svg class="architecture" viewBox="0 0 {width} {height}" style="--diagram-width:{width}px" xmlns="http://www.w3.org/2000/svg" aria-labelledby="architecture-title architecture-desc">',
             f'<title id="architecture-title">{("系统全景与流向" if zh else "System architecture and flow")}</title>',
             f'<desc id="architecture-desc">{("箭头表示标注的协作关系；完整关系和证据也可在下方文字列表阅读。" if zh else "Arrows show authored relationships, also available in the text list below.")}</desc>',
             '<defs><marker id="architecture-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke"/></marker></defs>']
    for group in groups:
        members = [xy[n["id"]] for n in nodes if n.get("group") == group["id"]]
        if not members:
            continue
        left, top = min(p[0] for p in members) - 20, min(p[1] for p in members) - 46
        right, bottom = max(p[0] for p in members) + w + 20, max(p[1] for p in members) + h + 20
        include(left + 16, top + 9, text_width(group["title"], 13), 22)
        parts.append(f'<g class="architecture-boundary"><title>{e(group["title"] + ": " + plain_text(group.get("summary", ""), terms))}</title><rect x="{left}" y="{top}" width="{right-left}" height="{bottom-top}" rx="14"/><text x="{left+16}" y="{top+25}">{e(group["title"])}</text></g>')
    labels = []
    for i, edge in enumerate(overview["edges"]):
        ax, ay = xy[edge["from"]]
        bx, by = xy[edge["to"]]
        if ax == bx and ay != by:
            down = by > ay
            sx, sy = ax + w / 2, ay + (h if down else 0)
            tx, ty = bx + w / 2, by + (0 if down else h)
            if abs(by - ay) > dy:
                channel = ax + w + 30
                path = f'M {ax+w} {ay+h/2} H {channel} V {by+h/2} H {bx+w}'
                lx, ly = channel + 10, min(ay, by) + h + 26
                include(channel + 10, min(ay, by), 0, abs(ay-by) + h)
            else:
                path = f'M {sx} {sy} L {tx} {ty}'
                lx, ly = sx + 12, (sy + ty) / 2
            anchor = "start"
        elif ax != bx:
            right = bx > ax
            sx, sy = ax + (w if right else 0), ay + h / 2
            tx, ty = bx + (0 if right else w), by + h / 2
            middle = (sx + tx) / 2
            path = f'M {sx} {sy} H {middle} V {ty} H {tx}'
            lx, ly, anchor = middle, (sy + ty) / 2 - 12, "middle"
        else:
            sx, sy = ax + w, ay + h / 3
            path = f'M {sx} {sy} h 28 v 38 h -28'
            lx, ly, anchor = sx + 30, sy + 10, "start"
            include(sx, sy, 38, 48)
        role = edge.get("role", "primary")
        attrs = f'data-edge-index="{i}" data-edge-from="{e(edge["from"])}" data-edge-to="{e(edge["to"])}"'
        parts.append(f'<a class="architecture-edge {role}" {attrs} href="#relationship/{i}" aria-label="{e(plain_text(edge["label"], terms))}"><path class="edge-hit" d="{path}"/><path class="edge-stroke" d="{path}" marker-end="url(#architecture-arrow)"/></a>')
        words = wrapped(plain_text(edge.get("diagram_label", edge["label"]), terms), 18)
        label_width = max((text_width(word, 12) for word in words), default=0)
        include(lx - (label_width / 2 if anchor == "middle" else 0) - 6, ly - 17, label_width + 12, max(1, len(words)) * 17 + 6)
        include(lx - 28, ly - 36, 28, 28)
        text = "".join(f'<tspan x="{lx}" dy="{0 if j == 0 else 17}">{e(line)}</tspan>' for j, line in enumerate(words))
        labels.append(f'<a class="architecture-edge-label {role}" {attrs} href="#relationship/{i}"><text x="{lx}" y="{ly}" text-anchor="{anchor}">{text}</text><g class="path-order" transform="translate({lx-14},{ly-22})"><circle r="11"/><text text-anchor="middle" dy="4"></text></g></a>')
    parts.extend(labels)
    for node in nodes:
        x, y = xy[node["id"]]
        title = wrapped(node["title"], 26)
        caption = wrapped(node["caption"] if "caption" in node else plain_text(node["summary"], terms), 28)
        title_text = "".join(f'<tspan x="{x+16}" dy="{0 if i == 0 else 20}">{e(line)}</tspan>' for i, line in enumerate(title[:2]))
        caption_y = y + (68 if len(title) > 1 else 53)
        caption_text = "".join(f'<tspan x="{x+16}" dy="{0 if i == 0 else 17}">{e(line + ("…" if i == 1 and len(caption)>2 else ""))}</tspan>' for i, line in enumerate(caption[:2]))
        parts.append(f'<a class="map-node" data-node="{e(node["id"])}" href="#node/{e(node["id"])}" aria-label="{e(node["title"])}"><title>{e(node["title"] + ": " + plain_text(node["summary"], terms))}</title><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10"/><text class="architecture-node-title" x="{x+16}" y="{y+27}">{title_text}</text><text class="architecture-node-caption" x="{x+16}" y="{caption_y}">{caption_text}</text></a>')
    left = math.floor(min(box[0] for box in bounds) - 12)
    top = math.floor(min(box[1] for box in bounds) - 12)
    right = math.ceil(max(box[2] for box in bounds) + 12)
    bottom = math.ceil(max(box[3] for box in bounds) + 12)
    # Include routed edges, all label lines and step markers, not only nodes.
    parts[0] = (f'<svg class="architecture" viewBox="{left} {top} {right-left} {bottom-top}" '
                f'style="--diagram-width:{right-left}px" xmlns="http://www.w3.org/2000/svg" '
                'aria-labelledby="architecture-title architecture-desc">')
    parts.append('</svg>')
    return "".join(parts)
