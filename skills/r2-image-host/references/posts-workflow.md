# Posts Workflow Reference

The posts repository is the writing source of truth. R2 URLs are introduced at
archive/publish time, not during early drafting.

## Intended Flow

1. Write drafts with local images.
2. Publish to WeChat using the existing WeChat posting flow.
3. Before archiving to `wechat/` or publishing from `blog/`, run `publish`.
4. Commit Markdown with R2 URLs and the project manifest.
5. Run `check` before blog sync.

## Commands

```bash
python3 /path/to/r2_asset_publish.py publish wechat/文章.md --write
python3 /path/to/r2_asset_publish.py publish blog/2026/post.md --write
python3 /path/to/r2_asset_publish.py check blog wechat --published-only
```

## Boundaries

- Do not upload from GitHub Actions until the local skill path and credentials
  are intentionally installed in CI.
- Do not delete local draft images automatically.
- Do not rewrite already-published WeChat archives without user approval.
- Do not replace existing remote WeChat or third-party image URLs unless the
  user explicitly asks to migrate them.
