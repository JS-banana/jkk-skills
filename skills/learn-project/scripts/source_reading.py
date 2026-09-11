"""Small, offline source excerpt highlighter used by the learn-project reader.

This module deliberately implements a conservative lexer instead of trying to
parse a programming language.  It only adds spans for tokens whose spelling is
locally recognisable.  The source text is always escaped before it is put in a
span, and a span is closed at every line boundary so callers can render one
``.code-line`` element per source line.
"""

from __future__ import annotations

from collections.abc import Mapping
from html import escape
from pathlib import PurePath
import re

__all__ = ["highlight_lines", "language_for"]


_LANGUAGE_ALIASES = {
    # Kotlin
    "kt": "kotlin",
    "kts": "kotlin",
    "kotlin": "kotlin",
    # JavaScript and TypeScript share the same conservative lexer, but keeping
    # their canonical names makes the rendered metadata useful to callers.
    "js": "javascript",
    "jsx": "javascript",
    "mjs": "javascript",
    "cjs": "javascript",
    "javascript": "javascript",
    "node": "javascript",
    "ts": "typescript",
    "tsx": "typescript",
    "mts": "typescript",
    "cts": "typescript",
    "typescript": "typescript",
    # Python
    "py": "python",
    "pyw": "python",
    "python": "python",
    # Shell scripts
    "sh": "shell",
    "bash": "shell",
    "zsh": "shell",
    "fish": "shell",
    "shell": "shell",
    "shellscript": "shell",
    # JSON.  JSONC comments are safe to colour with the JSON lexer too.
    "json": "json",
    "jsonc": "json",
    # Explicit plain text aliases
    "plain": "plain",
    "text": "plain",
    "txt": "plain",
    "markdown": "plain",
    "md": "plain",
}

_KEYWORDS = {
    "kotlin": {
        "actual", "abstract", "annotation", "as", "break", "by", "catch",
        "class", "companion", "const", "constructor", "continue", "crossinline",
        "data", "delegate", "do", "else", "enum", "expect", "external", "final",
        "finally", "for", "fun", "if", "import", "in", "infix", "init", "inline",
        "inner", "interface", "internal", "is", "lateinit", "noinline", "object",
        "open", "operator", "out", "override", "package", "private", "protected",
        "public", "reified", "return", "sealed", "set", "super", "suspend", "tailrec",
        "this", "throw", "try", "typealias", "typeof", "val", "var", "vararg", "when",
        "where", "while", "field", "file", "get", "param", "property", "receiver",
        "setparam",
    },
    "javascript": {
        "as", "async", "await", "break", "case", "catch", "class", "const", "continue",
        "debugger", "default", "delete", "do", "else", "export", "extends", "finally",
        "for", "from", "function", "get", "if", "import", "in", "instanceof", "interface",
        "let", "new", "of", "package", "private", "protected", "public", "return", "set",
        "static", "super", "switch", "this", "throw", "try", "typeof", "var", "void",
        "while", "with", "yield",
    },
    "typescript": {
        "as", "async", "await", "break", "case", "catch", "class", "const", "continue",
        "debugger", "declare", "default", "delete", "do", "else", "enum", "export", "extends",
        "finally", "for", "from", "function", "get", "if", "implements", "import", "in",
        "infer", "instanceof", "interface", "is", "keyof", "let", "module", "namespace",
        "never", "new", "of", "package", "private", "protected", "public", "readonly", "return",
        "set", "static", "super", "switch", "this", "throw", "try", "type", "typeof", "var",
        "void", "while", "with", "yield",
    },
    "python": {
        "and", "as", "assert", "async", "await", "break", "case", "class", "continue", "def",
        "del", "elif", "else", "except", "finally", "for", "from", "global", "if", "import",
        "in", "is", "lambda", "match", "nonlocal", "not", "or", "pass", "raise", "return",
        "try", "while", "with", "yield",
    },
    "shell": {
        "alias", "case", "coproc", "declare", "do", "done", "elif", "else", "esac", "export",
        "fi", "for", "function", "if", "in", "local", "readonly", "return", "select", "shift",
        "source", "then", "time", "typeset", "unalias", "unset", "until", "while",
    },
    "json": set(),
}

_BUILTINS = {
    "kotlin": {"arrayOf", "check", "error", "listOf", "mapOf", "println", "require", "run", "TODO"},
    "javascript": {"Array", "Boolean", "Date", "Error", "JSON", "Math", "Number", "Object", "Promise", "RegExp", "Set", "String", "Symbol", "console", "document", "parseInt", "parseFloat", "setTimeout", "window"},
    "typescript": {"Array", "Boolean", "Date", "Error", "JSON", "Math", "Number", "Object", "Promise", "RegExp", "Set", "String", "Symbol", "console", "document", "parseInt", "parseFloat", "setTimeout", "window"},
    "python": {"__import__", "abs", "all", "any", "bool", "dict", "enumerate", "float", "isinstance", "len", "list", "map", "max", "min", "open", "print", "range", "repr", "set", "sorted", "str", "sum", "tuple", "type", "zip"},
    "shell": {"cd", "echo", "exec", "exit", "printf", "pwd", "read", "test", "trap", "wait"},
    "json": set(),
}

_BOOLEAN_WORDS = {
    "kotlin": {"true", "false"},
    "javascript": {"true", "false"},
    "typescript": {"true", "false"},
    "python": {"True", "False"},
    "shell": {"true", "false"},
    "json": {"true", "false"},
}

_NULL_WORDS = {
    "kotlin": {"null"},
    "javascript": {"null", "undefined"},
    "typescript": {"null", "undefined"},
    "python": {"None"},
    "shell": {"null"},
    "json": {"null"},
}

_BLOCK_COMMENT_LANGUAGES = {"kotlin", "javascript", "typescript", "json"}
_SLASH_COMMENT_LANGUAGES = _BLOCK_COMMENT_LANGUAGES
_HASH_COMMENT_LANGUAGES = {"python", "shell"}

_OPERATORS = tuple(
    sorted(
        {
            "===", "!==", ">>>=", "**=", "&&=", "||=", "??=", ":::", "...",
            "->", "=>", "==", "!=", "<=", ">=", "&&", "||", "??", "?.", "++", "--",
            "+=", "-=", "*=", "/=", "%=", "**", "//", "<<", ">>", ">>>", "::", "?.",
            "|=", "&=", "^=", "??", "?.", "=", "+", "-", "*", "/", "%", "<", ">", "!",
            "&", "|", "^", "~", "?", "=>",
        },
        key=len,
        reverse=True,
    )
)

_PUNCTUATION = set("{}[]();,.:")
_IDENTIFIER_START = re.compile(r"[A-Za-z_$]", re.ASCII)
_IDENTIFIER_PART = re.compile(r"[A-Za-z0-9_$]", re.ASCII)
_NUMBER = re.compile(
    r"(?:0[xX][0-9A-Fa-f](?:_?[0-9A-Fa-f])*|0[bB][01](?:_?[01])*|"
    r"0[oO][0-7](?:_?[0-7])*|(?:\d(?:_?\d)*)?(?:\.\d(?:_?\d)*)"
    r"(?:[eE][+-]?\d(?:_?\d)*)?|\d(?:_?\d)*(?:[eE][+-]?\d(?:_?\d)*)?)"
    r"[A-Za-z]*",
)


def _normalise_language(value: object) -> str | None:
    """Return a canonical language name, or ``None`` when it is unknown."""

    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    text = text.removeprefix("language-")
    if text.startswith("."):
        text = text[1:]
    if text in _LANGUAGE_ALIASES:
        return _LANGUAGE_ALIASES[text]
    return None


def language_for(source: Mapping[str, object]) -> str:
    """Infer the highlighter language from ``source.language`` or ``source.path``.

    Explicit but unknown language names intentionally fall back to ``plain``
    instead of guessing from a possibly unrelated path.
    """

    explicit = source.get("language")
    if explicit is not None and str(explicit).strip():
        return _normalise_language(explicit) or "plain"

    path = source.get("path")
    if path is not None:
        # URLs and source locations occasionally carry a query/hash.  It is
        # still the file suffix that determines the lexer.
        path_text = str(path).split("?", 1)[0].split("#", 1)[0]
        suffix = PurePath(path_text).suffix
        return _normalise_language(suffix) or "plain"
    return "plain"


def _escaped(value: str) -> str:
    # quote=True is safe for both text nodes and any future attribute reuse.
    return escape(value, quote=True)


def _token(kind: str, value: str) -> str:
    return f'<span class="token {kind}">{_escaped(value)}</span>'


def _is_identifier_start(char: str) -> bool:
    return bool(char) and (char == "_" or char == "$" or char.isalpha())


def _is_identifier_part(char: str) -> bool:
    return bool(char) and (char == "_" or char == "$" or char.isalnum())


def _next_nonspace(line: str, index: int) -> str:
    while index < len(line) and line[index].isspace():
        index += 1
    return line[index] if index < len(line) else ""


def _find_string_end(line: str, start: int, delimiter: str, raw: bool = False) -> int | None:
    index = start
    while index < len(line):
        if line.startswith(delimiter, index):
            return index + len(delimiter)
        if line[index] == "\\" and not raw:
            index += 2
        else:
            index += 1
    return None


def _python_string_start(line: str, index: int) -> tuple[int, str, bool] | None:
    """Return ``(prefix length, delimiter, raw)`` for a Python string start."""

    if index >= len(line) or line[index].lower() not in "rubf":
        return None
    for prefix in ("rf", "fr", "rb", "br", "ur", "ru", "r", "u", "b", "f"):
        end = index + len(prefix)
        if line[index:end].lower() != prefix or end >= len(line) or line[end] not in "'\"":
            continue
        quote = line[end]
        delimiter = quote * 3 if line.startswith(quote * 3, end) else quote
        # A Python raw prefix changes escape interpretation, but a backslash
        # can still protect the quote that terminates the literal.  The lexer
        # therefore keeps quote detection enabled; ``raw`` is reserved for
        # Kotlin's triple-quoted strings below.
        return len(prefix), delimiter, False
    return None


class _Lexer:
    __slots__ = ("language", "mode", "delimiter", "raw", "token_kind")

    def __init__(self, language: str):
        self.language = language
        self.mode = ""
        self.delimiter = ""
        self.raw = False
        self.token_kind = "string"

    def _string_allowed(self, char: str) -> bool:
        if self.language == "json":
            return char == '"'
        if self.language == "python":
            return char in "'\""
        if self.language == "shell":
            return char in "'\"`"
        if self.language == "kotlin":
            return char in "'\""
        return char in "'\"`"

    def _identifier_kind(self, word: str, line: str, end: int, previous: str) -> str | None:
        if word in _BOOLEAN_WORDS.get(self.language, set()):
            return "boolean"
        if word in _NULL_WORDS.get(self.language, set()):
            return "null"
        if word in _KEYWORDS.get(self.language, set()):
            return "keyword"
        if word in _BUILTINS.get(self.language, set()):
            return "builtin"
        if self.language in {"kotlin", "typescript"} and word[:1].isupper():
            return "class-name"
        if previous == ".":
            return "property"
        if _next_nonspace(line, end) == "(":
            return "function"
        return None

    def _comment_start(self, line: str, index: int) -> str | None:
        if self.language in _HASH_COMMENT_LANGUAGES and line[index] == "#":
            return "#"
        if self.language in _SLASH_COMMENT_LANGUAGES:
            if line.startswith("//", index):
                return "//"
            if line.startswith("/*", index):
                return "/*"
        return None

    def _flush_plain(self, chunks: list[str], line: str, start: int, end: int) -> None:
        if start < end:
            chunks.append(_escaped(line[start:end]))

    def line(self, line: str) -> str:
        chunks: list[str] = []
        plain_start = 0
        index = 0
        previous = ""

        while index < len(line):
            if self.mode == "comment":
                end = line.find("*/", index)
                if end < 0:
                    self._flush_plain(chunks, line, plain_start, index)
                    chunks.append(_token("comment", line[index:]))
                    return "".join(chunks)
                end += 2
                self._flush_plain(chunks, line, plain_start, index)
                chunks.append(_token("comment", line[index:end]))
                index = end
                plain_start = index
                self.mode = ""
                previous = ""
                continue

            if self.mode == "string":
                end = _find_string_end(line, index, self.delimiter, self.raw)
                if end is None:
                    self._flush_plain(chunks, line, plain_start, index)
                    chunks.append(_token(self.token_kind, line[index:]))
                    return "".join(chunks)
                self._flush_plain(chunks, line, plain_start, index)
                chunks.append(_token(self.token_kind, line[index:end]))
                index = end
                plain_start = index
                self.mode = ""
                self.delimiter = ""
                self.raw = False
                self.token_kind = "string"
                previous = ""
                continue

            comment = self._comment_start(line, index)
            if comment:
                self._flush_plain(chunks, line, plain_start, index)
                if comment != "/*":
                    chunks.append(_token("comment", line[index:]))
                    return "".join(chunks)
                end = line.find("*/", index + 2)
                if end < 0:
                    chunks.append(_token("comment", line[index:]))
                    self.mode = "comment"
                    return "".join(chunks)
                end += 2
                chunks.append(_token("comment", line[index:end]))
                index = end
                plain_start = index
                previous = ""
                continue

            # Python prefixes (r, b, f, rf...) belong to the string token.
            prefix = _python_string_start(line, index) if self.language == "python" else None
            quote_index = index
            if prefix:
                prefix_length, delimiter, raw = prefix
                quote_index = index + prefix_length
            elif self._string_allowed(line[index]):
                delimiter = line[index]
                raw = False
                if self.language in {"python", "kotlin"} and line.startswith(delimiter * 3, index):
                    delimiter = delimiter * 3
                    raw = self.language == "kotlin"
            else:
                delimiter = ""
                raw = False

            if delimiter:
                end = _find_string_end(line, quote_index + len(delimiter), delimiter, raw)
                kind = "string"
                if self.language == "json" and end is not None and _next_nonspace(line, end) == ":":
                    kind = "property"
                self._flush_plain(chunks, line, plain_start, index)
                if end is None:
                    chunks.append(_token(kind, line[index:]))
                    self.mode = "string"
                    self.delimiter = delimiter
                    self.raw = raw
                    self.token_kind = kind
                    return "".join(chunks)
                chunks.append(_token(kind, line[index:end]))
                index = end
                plain_start = index
                previous = ""
                continue

            # Shell variables are unambiguous enough to colour without parsing
            # parameter expansion expressions.
            if self.language == "shell" and line[index] == "$":
                end = index + 1
                if end < len(line) and line[end] == "{":
                    close = line.find("}", end + 1)
                    end = len(line) if close < 0 else close + 1
                elif end < len(line) and line[end] in "?#@*$!-":
                    end += 1
                else:
                    while end < len(line) and (line[end].isalnum() or line[end] == "_"):
                        end += 1
                if end > index + 1:
                    self._flush_plain(chunks, line, plain_start, index)
                    chunks.append(_token("variable", line[index:end]))
                    index = end
                    plain_start = index
                    previous = ""
                    continue

            if _is_identifier_start(line[index]):
                end = index + 1
                while end < len(line) and _is_identifier_part(line[end]):
                    end += 1
                word = line[index:end]
                kind = self._identifier_kind(word, line, end, previous)
                if kind:
                    self._flush_plain(chunks, line, plain_start, index)
                    chunks.append(_token(kind, word))
                    plain_start = end
                index = end
                previous = word
                continue

            number = _NUMBER.match(line, index)
            if number and (index == 0 or not _is_identifier_part(line[index - 1])):
                end = number.end()
                self._flush_plain(chunks, line, plain_start, index)
                chunks.append(_token("number", line[index:end]))
                index = end
                plain_start = index
                previous = ""
                continue

            operator = next((item for item in _OPERATORS if line.startswith(item, index)), None)
            if operator:
                self._flush_plain(chunks, line, plain_start, index)
                chunks.append(_token("operator", operator))
                index += len(operator)
                plain_start = index
                previous = operator
                continue

            if line[index] in _PUNCTUATION:
                self._flush_plain(chunks, line, plain_start, index)
                chunks.append(_token("punctuation", line[index]))
                previous = line[index]
                index += 1
                plain_start = index
                continue

            index += 1

        self._flush_plain(chunks, line, plain_start, len(line))
        return "".join(chunks)


def highlight_lines(excerpt: str, language: str | None = None) -> list[str]:
    """Escape and highlight an excerpt one ``str.splitlines()`` row at a time.

    The returned rows contain HTML with optional ``<span class="token ...">``
    elements.  Removing those elements and HTML-unescaping a row reproduces
    the corresponding source row.  Unknown languages are intentionally plain
    text.  ``language`` may be an alias or a canonical name; callers that have
    a source record can pass ``language_for(source)`` first.
    """

    if not isinstance(excerpt, str):
        raise TypeError("excerpt must be a string")
    canonical = _normalise_language(language) or "plain"
    rows = excerpt.splitlines()
    if canonical == "plain":
        return [_escaped(row) for row in rows]
    lexer = _Lexer(canonical)
    return [lexer.line(row) for row in rows]
