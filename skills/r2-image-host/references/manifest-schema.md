# Manifest Schema

The project manifest is a usage ledger. R2 stores bytes; Markdown stores public
URLs; the manifest records where those URLs are used.

## Location

- Project manifest: `.r2-assets/manifest.json`

Commit the project manifest when the project needs auditability. Do not keep a
hidden machine cache as source of truth; cross-project reuse should use a future
explicit asset catalog repo, not `~/.cache`.

## Shape

```json
{
  "version": 1,
  "project": "posts",
  "updated_at": "2026-07-07T00:00:00Z",
  "usages": [
    {
      "source": "blog/2026/example.md",
      "role": "article-image",
      "alt": "cover",
      "url": "https://assets.laifuyou.com/posts/blog/2026/example/cover.ab12cd34ef56.webp",
      "key": "posts/blog/2026/example/cover.ab12cd34ef56.webp",
      "optimized_sha256": "...",
      "content_type": "image/webp",
      "width": 1200,
      "height": 675,
      "bytes_before": 1000000,
      "bytes_after": 180000,
      "tool": "cwebp",
      "uploaded_at": "2026-07-07T00:00:00Z",
      "original_ref": "imgs/cover.png"
    }
  ]
}
```

## Fields

Keep:

- `source`: Markdown file that uses the image.
- `role`: image role, default `article-image`.
- `alt`: Markdown alt text.
- `url`: public URL used by Markdown.
- `key`: R2 object key, needed for verification, deletion, and migration.
- `optimized_sha256`: hash of the uploaded bytes.
- `content_type`, `width`, `height`, `bytes_after`: catalog and audit fields.
- `bytes_before`: compression benefit, useful but not required at runtime.
- `tool`: optimizer used.
- `uploaded_at`: upload/reuse timestamp.
- `original_ref`: optional audit trace for the local path before rewrite.

Do not keep:

- `assets`: project manifests should not maintain a second index.
- `image_ref`: use optional `original_ref` instead.
- `source_sha256`: local source images are usually deleted after publish.
- Machine-local global cache files.

## Dedupe

Dedupe by `optimized_sha256` inside the current project manifest only. If the
same optimized hash already has a URL in `usages`, reuse that URL. Cross-project
reuse belongs in a future explicit asset catalog, not hidden local state.

Never dedupe by filename alone.

## Catalog

`catalog` renders `usages` to static HTML/JSON. It should not query R2 as its
normal path. R2 listing is only a recovery/debugging path for future versions.
