"""Contract and publication regressions. Run: python3 -m unittest discover -s scripts."""

import copy
import json
import re
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import render


class StudyRenderingTests(unittest.TestCase):
    def setUp(self):
        self.study = {
            "version": 1,
            "project": {"name": "Example", "revision": "working tree", "scope": "Static source only"},
            "title": "How does it work?", "summary": "A selective explanation.",
            "overview": {"body": ["Start with a request."], "nodes": [], "edges": []},
            "mechanisms": [], "evidence": [], "next": [],
        }

    def test_orientation_does_not_require_fabricated_mechanisms(self):
        render.validate(self.study)
        page = render.render(self.study)
        self.assertIn("How does it work?", page)
        self.assertNotIn('class="step-panel"', page)
        self.assertNotIn('src="http', page)
        self.assertIn('<link rel="icon" href="data:image/svg+xml,', page)
        self.assertIn('data-nav="overview"><span class="nav-number"', page)

    def test_broken_relationships_and_sources_are_rejected(self):
        cases = []
        source_ref = copy.deepcopy(self.study)
        source_ref["overview"]["nodes"] = [{"id": "entry", "title": "Entry", "summary": "Entry", "evidence": ["missing"]}]
        cases.append(source_ref)
        bad_edge = copy.deepcopy(self.study)
        bad_edge["overview"]["edges"] = [{"from": "missing", "to": "unknown", "label": "Calls"}]
        cases.append(bad_edge)
        bad_branch = copy.deepcopy(self.study)
        bad_branch["mechanisms"] = [{"id": "path", "title": "Path", "question": "Why?", "answer": "Because.", "steps": [{"id": "entry", "title": "Entry", "body": [], "branches": [{"condition": "Ready", "effect": "Continue", "target": "missing"}]}]}]
        cases.append(bad_branch)
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                render.validate(case)

    def test_repository_text_cannot_escape_into_executable_html(self):
        attack = '</script><img src=x onerror="alert(1)"> & `code`'
        self.study["summary"] = attack
        self.study["overview"]["nodes"] = [{"id": "entry", "title": attack, "summary": attack, "evidence": ["source"]}]
        self.study["evidence"] = [{"id": "source", "label": attack, "kind": "implementation", "supports": attack, "excerpt": attack}]
        page = render.render(render.validate(self.study))
        self.assertNotIn('<img src=x', page)
        self.assertIn('&lt;/script&gt;&lt;img', page)
        self.assertEqual(page.count('</script>'), 1)
        exported = render.markdown(self.study)
        self.assertNotIn('<img src=x', exported.split('\n```\n')[0])
        self.assertIn('\n```\n' + attack + '\n```', exported)
        for url in ('javascript:alert(1)', 'data:text/html,hello', '//evil.example/', 'https://good.example/\nx'):
            self.study["evidence"][0]["url"] = url
            with self.subTest(url=url), self.assertRaises(ValueError):
                render.validate(self.study)

    def test_excerpt_range_must_match_rendered_line_numbers(self):
        self.study["evidence"] = [{"id": "source", "label": "Source", "kind": "implementation", "supports": "A statement", "lines": [8, 9], "excerpt": "one line"}]
        with self.assertRaises(ValueError):
            render.validate(self.study)
        self.study["evidence"][0]["excerpt"] = "one line\nsecond line\n"
        render.validate(self.study)

    def test_semantic_prose_is_safe_and_portable(self):
        self.study["terms"] = [{"id": "rpc", "label": "RPC", "definition": "A remote call."}]
        self.study["summary"] = 'Call `<img onerror=x>` with **care** using [[rpc|协议]].'
        self.study["frontmatter"] = {"title": 'A: "quoted" title', "tags": ["study"]}
        page = render.render(render.validate(self.study))
        self.assertIn('<code>&lt;img onerror=x&gt;</code>', page)
        self.assertNotIn('<img onerror=x>', page)
        self.assertIn('href="#term/rpc"', page)
        self.assertIn('id="term/rpc"', page)
        export = render.markdown(self.study)
        self.assertTrue(export.startswith('---\n'))
        self.assertIn('A remote call.', export)
        self.assertNotIn('[[rpc', export)
        self.study["summary"] = 'Unknown [[missing]].'
        with self.assertRaises(ValueError):
            render.validate(self.study)

    def test_group_and_journey_references_are_checked(self):
        self.study["overview"]["groups"] = [{"id": "host", "title": "Host"}]
        self.study["overview"]["nodes"] = [{"id": "entry", "title": "Entry", "summary": "Receives input", "group": "host"}]
        self.study["overview"]["journey"] = [{"title": "Input", "body": "Receives a request"}]
        page = render.render(render.validate(self.study))
        self.assertIn('Receives a request', page)
        self.study["overview"]["nodes"][0]["group"] = "missing"
        with self.assertRaises(ValueError):
            render.validate(self.study)
        self.study["overview"]["nodes"][0]["group"] = "host"
        self.study["overview"]["journey"][0]["evidence"] = ["missing"]
        with self.assertRaises(ValueError):
            render.validate(self.study)

    def test_read_fingerprint_changes_with_supporting_evidence(self):
        self.study["evidence"] = [{"id": "source", "label": "Source", "kind": "implementation", "supports": "Original claim"}]
        self.study["overview"]["nodes"] = [{"id": "entry", "title": "Entry", "summary": "Receives input", "evidence": ["source"]}]
        before = render.render(render.validate(self.study))
        self.study["evidence"][0]["supports"] = "Corrected claim"
        after = render.render(render.validate(self.study))
        pattern = r'data-fingerprint="([a-f0-9]+)"'
        self.assertNotEqual(re.search(pattern, before)[1], re.search(pattern, after)[1])

    def test_map_terms_do_not_nest_links_and_source_focus_is_bounded(self):
        class Links(HTMLParser):
            def __init__(self):
                super().__init__()
                self.depth = 0
                self.nested = False
            def handle_starttag(self, tag, attrs):
                if tag == "a":
                    self.nested |= self.depth > 0
                    self.depth += 1
            def handle_endtag(self, tag):
                if tag == "a":
                    self.depth -= 1
        self.study["terms"] = [{"id": "rpc", "label": "RPC", "definition": "A remote call"}]
        self.study["overview"]["nodes"] = [{"id": "entry", "title": "Entry", "summary": "Uses [[rpc]]", "evidence": ["source"]}]
        self.study["evidence"] = [{"id": "source", "label": "Source", "kind": "implementation", "supports": "A call", "lines": [4, 4], "excerpt": "call()", "focus_lines": [4]}]
        page = render.render(render.validate(self.study))
        parser = Links()
        parser.feed(page)
        self.assertFalse(parser.nested)
        self.assertIn('code-line is-highlight', page)
        self.study["evidence"][0]["focus_lines"] = [5]
        with self.assertRaises(ValueError):
            render.validate(self.study)

    def test_graph_routes_and_annotation_bounds(self):
        self.study["overview"]["nodes"] = [
            {"id": "entry", "title": "Entry", "summary": "Input", "position": [0, 0]},
            {"id": "worker", "title": "Worker", "summary": "Execute", "position": [1, 0]}]
        self.study["overview"]["edges"] = [{"from": "entry", "to": "worker", "label": "Send <request>", "role": "primary"}]
        self.study["overview"]["paths"] = [{"id": "request", "title": "Request", "summary": "Static path", "edges": [0]}]
        self.study["evidence"] = [{"id": "source", "label": "Guard", "kind": "implementation", "supports": "A guard",
            "path": "guard.kt", "lines": [10, 11], "excerpt": 'if (ready) {\n    run("<script>")',
            "reading_goal": "Find the guard", "annotations": [{"lines": [10, 10], "body": "Only when ready"}]}]
        self.study["overview"]["nodes"][0]["evidence"] = ["source"]
        page = render.render(render.validate(self.study))
        self.assertIn('id="relationship/0"', page)
        self.assertIn('href="#relationship/0"', page)
        self.assertIn('Only when ready', render.markdown(self.study))
        self.assertNotIn('<request>', page)
        self.study["evidence"][0]["annotations"][0]["lines"] = [9, 10]
        with self.assertRaises(ValueError):
            render.validate(self.study)
        self.study["evidence"][0]["annotations"][0]["lines"] = [10, 10]
        self.study["overview"]["paths"][0]["edges"] = [1]
        with self.assertRaises(ValueError):
            render.validate(self.study)
        self.study["overview"]["paths"][0]["edges"] = [0]
        self.study["overview"]["nodes"][1]["position"] = [0, 0]
        with self.assertRaises(ValueError):
            render.validate(self.study)

    def test_lexical_colors_preserve_original_source(self):
        from source_reading import highlight_lines
        class Text(HTMLParser):
            def __init__(self):
                super().__init__()
                self.parts = []
            def handle_data(self, data):
                self.parts.append(data)
        samples = [
            ('kotlin', '/* comment\ncontinued */ val x = "</script>&"\n'),
            ('javascript', 'const x = `first\n<script>${value}`;\n// note'),
            ('python', 's = """one\ntwo"""\nif s: print(s)'),
            ('shell', '# note\nprintf "%s" "$HOME"'),
            ('json', '{"name":"<img>","value":12}'),
            ('plain', '<tag> & text')]
        for language, excerpt in samples:
            with self.subTest(language=language):
                lines = highlight_lines(excerpt, language)
                self.assertEqual(len(lines), len(excerpt.splitlines()))
                for actual, expected in zip(lines, excerpt.splitlines()):
                    parser = Text()
                    parser.feed(actual)
                    self.assertEqual(''.join(parser.parts), expected)
                    self.assertNotIn('<script>', actual)
                    self.assertNotIn('<img>', actual)

    def test_unknown_language_is_readable_and_keeps_its_name(self):
        self.study["evidence"] = [{"id": "source", "label": "Source", "kind": "implementation", "supports": "A function", "language": "go", "excerpt": "func main() {}"}]
        self.study["overview"]["nodes"] = [{"id": "entry", "title": "Entry", "summary": "Input", "evidence": ["source"]}]
        page = render.render(render.validate(self.study))
        self.assertIn('go · Plain text fallback', page)
        self.assertIn('func main() {}', page)
        for invalid in ([], None, " "):
            self.study["evidence"][0]["language"] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                render.validate(self.study)

    def test_literal_fields_and_inline_terms_have_one_contract(self):
        self.study["title"] = "Literal [[undefined]]"
        self.study["summary"] = "Code `[[undefined]]` is literal."
        self.study["terms"] = [{"id": "rpc", "label": "Remote call", "definition": "Literal [[undefined]]"}]
        self.study["overview"]["nodes"] = [{"id": "a", "title": "A", "summary": "A"}, {"id": "b", "title": "B", "summary": "B"}]
        self.study["overview"]["edges"] = [{"from": "a", "to": "b", "label": "Uses [[rpc]]"}]
        page = render.render(render.validate(self.study))
        self.assertIn('<h1 tabindex="-1">Literal [[undefined]]</h1>', page)
        self.assertIn('Uses <a class="term" href="#term/rpc">Remote call</a>', page)
        self.assertIn('>Uses Remote call</tspan>', page)
        self.assertIn('Uses Remote call', render.markdown(self.study))
        self.study["overview"]["edges"][0]["label"] = "Uses [[unknown]]"
        with self.assertRaises(ValueError):
            render.validate(self.study)

    def test_source_term_changes_invalidate_read_state_and_sources_have_unique_anchors(self):
        self.study["terms"] = [{"id": "rpc", "label": "RPC", "definition": "Original definition"}]
        self.study["evidence"] = [{"id": "source", "label": "Source", "kind": "implementation", "supports": "Uses [[rpc]]"}]
        self.study["overview"]["nodes"] = [{"id": "a", "title": "A", "summary": "A", "evidence": ["source"]}, {"id": "b", "title": "B", "summary": "B", "evidence": ["source"]}]
        before = render.render(render.validate(self.study))
        self.assertIn('id="source/source/1"', before)
        self.assertIn('id="source/source/2"', before)
        self.study["terms"][0]["definition"] = "Corrected definition"
        after = render.render(render.validate(self.study))
        pattern = r'data-fingerprint="([a-f0-9]+)"'
        self.assertNotEqual(re.search(pattern, before)[1], re.search(pattern, after)[1])

    def test_graph_viewport_contains_long_connection_labels_and_self_loops(self):
        import xml.etree.ElementTree as ET
        from architecture import render_architecture
        for start, end in ((0, 2), (2, 0), (0, 0)):
            nodes = [{"id": "a", "title": "A", "summary": "A", "position": [0, start]}]
            if start != end:
                nodes.append({"id": "b", "title": "B", "summary": "B", "position": [0, end]})
            overview = {"nodes": nodes, "edges": [{"from": "a", "to": "b" if start != end else "a", "label": "Long supporting connection"}]}
            tree = ET.fromstring(render_architecture(overview, False))
            left, top, width, height = map(float, tree.get("viewBox").split())
            ns = {"s": "http://www.w3.org/2000/svg"}
            label = next(a for a in tree.findall('s:a', ns) if 'architecture-edge-label' in a.get('class', ''))
            text = label.find('s:text', ns)
            x, y = float(text.get('x')), float(text.get('y'))
            # This real label needs substantially more than the old 8px remainder.
            self.assertGreater(left + width - x, 100)
            self.assertGreater(height + top, y + 20)
            self.assertLess(top, y - 35)

    def test_invalid_input_preserves_existing_exports(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, page, markdown = root / 'study.json', root / 'study.html', root / 'study.md'
            page.write_text('previous page')
            markdown.write_text('previous markdown')
            source.write_text(json.dumps({**self.study, "version": 2}))
            result = subprocess.run([sys.executable, str(Path(render.__file__)), str(source), '-o', str(page)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(page.read_text(), 'previous page')
            self.assertEqual(markdown.read_text(), 'previous markdown')
            source.write_text(json.dumps(self.study))
            result = subprocess.run([sys.executable, str(Path(render.__file__)), str(source), '-o', str(page)], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(self.study['title'], page.read_text())
            self.assertIn(self.study['title'], markdown.read_text())


if __name__ == '__main__':
    unittest.main()
