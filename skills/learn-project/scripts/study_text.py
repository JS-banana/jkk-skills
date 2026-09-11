"""One non-nesting inline grammar shared by validation and all reading exports."""
import re

INLINE = re.compile(r"`([^`\n]+)`|\*\*([^*\n]+)\*\*|\[\[([a-z][a-z0-9-]*)(?:\|([^]\n]+))?\]\]")


def term_ids(text):
    return {m[3] for m in INLINE.finditer(text) if m[3] is not None}


def plain_text(text, terms):
    return INLINE.sub(lambda m: m[1] if m[1] is not None else m[2] if m[2] is not None else m[4] or terms[m[3]]["label"], text)


# Only these fields are prose. Titles, captions, definitions, locations and
# excerpts remain literal, even when they contain something resembling markup.
PROSE = {
    "study": ("summary", "next"), "overview": ("body",),
    "node": ("summary",), "edge": ("label", "diagram_label"),
    "group": ("summary",), "journey": ("body",), "path": ("summary",),
    "mechanism": ("answer", "principle", "limits"),
    "step": ("body", "input", "output", "state"),
    "branch": ("condition", "effect"), "evidence": ("supports", "reading_goal"),
    "annotation": ("body",),
}
CHILDREN = {
    "study": {"overview": "overview", "mechanisms": "mechanism", "evidence": "evidence"},
    "overview": {"nodes": "node", "edges": "edge", "groups": "group", "journey": "journey", "paths": "path"},
    "mechanism": {"steps": "step"}, "step": {"branches": "branch"},
    "evidence": {"annotations": "annotation"},
}


def prose_values(item, kind="study"):
    for field in PROSE.get(kind, ()):
        value = item.get(field, [])
        yield from ([value] if isinstance(value, str) else value)
    for field, child_kind in CHILDREN.get(kind, {}).items():
        children = item.get(field, [])
        if isinstance(children, dict):
            children = [children]
        for child in children:
            yield from prose_values(child, child_kind)
