# Markdown Asset Reference

The publisher treats Markdown as the editable source and R2 URLs as the archive
form.

## Supported References

- Inline Markdown images: `![alt](path/to/image.png)`
- Reference images: `![alt][id]` with `[id]: path/to/image.png`
- HTML images: `<img src="path/to/image.png" alt="alt">`

Skip:

- Fenced code blocks
- `http://` and `https://`
- `data:`
- `mailto:`
- Fragment-only links
- Missing files

## Rewrite Rules

`publish` is dry-run by default. It uploads and rewrites only with `--write`.

When rewriting:

- Replace only image URLs, not surrounding prose.
- Preserve inline alt text.
- Preserve reference definition labels.
- Leave remote URLs untouched.
- Report every skipped local reference with a reason.

## Key Prefixes

When no prefix is passed:

- `blog/<year>/<file>.md` -> `posts/blog/<year>/<file-slug>/`
- `wechat/<file>.md` -> `posts/wechat/<year>/<file-slug>/`
- Any other Markdown -> `assets/<project>/<file-slug>/`

For `wechat/`, the year comes from frontmatter `date` when available, otherwise
the file mtime/current year fallback used by the script.

## File Names

R2 keys use ASCII-safe slugs plus a short optimized hash:

```text
posts/blog/2026/my-post/cover.a1b2c3d4e5f6.webp
```

This keeps URLs stable for immutable caching while avoiding Unicode key and URL
encoding drift.
