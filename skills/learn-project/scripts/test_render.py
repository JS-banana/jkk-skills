"""Contract and publication regressions. Run: python3 -m unittest discover -s scripts."""

import copy
import json
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
