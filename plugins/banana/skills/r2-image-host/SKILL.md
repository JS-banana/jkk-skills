---
name: r2-image-host
description: >
  Asset publishing to Cloudflare R2 for local images and Markdown documents.
  Use when the user wants an R2 image host, upload local images to R2, compress
  images before publishing, rewrite Markdown image links to public URLs, build
  or query an asset manifest/catalog, verify Wrangler/R2 setup, or prepare blog
  and WeChat article images for durable public access.
---

# R2 Image Host

Publish local image assets to Cloudflare R2, record the public URL in a
manifest, and rewrite Markdown so archived content no longer depends on local
image files.

## Load Rules

- Before Cloudflare, Wrangler, bucket, domain, cache, or smoke verification
  work, read `references/cloudflare-r2.md`.
- Before scanning or rewriting Markdown, read `references/markdown-assets.md`.
- Before changing manifest shape, dedupe behavior, catalog output, or `find`,
  read `references/manifest-schema.md`.
- Before using this in the posts writing repository, read
  `references/posts-workflow.md`.

## Workflow

1. Diagnose the environment.
   - Run `python3 scripts/r2_asset_publish.py doctor`.
   - Completion: Python version, Wrangler command, login state, compression
     tools, configured bucket, and configured domain are known.

2. Set up the R2 target only when the user asks for live publishing.
   - Run `python3 scripts/r2_asset_publish.py setup`.
   - Use `--dry-run` first if the user did not explicitly allow Cloudflare
     mutations.
   - Completion: the bucket exists and the custom domain is connected or the
     exact missing permission/configuration is reported.

3. Publish or inspect assets.
   - For one-off images, use `optimize`.
   - For Markdown, use `publish`; it is dry-run by default and only uploads and
     rewrites when `--write` is passed.
   - For release checks, use `check`.
   - For reuse and browsing, use `find` or `catalog`.
   - Completion: every local image reference is either rewritten to a public
     URL, explicitly skipped, or reported as an error.

4. Verify public delivery after live publishing.
   - Run `python3 scripts/r2_asset_publish.py smoke`.
   - Completion: a generated image is compressed, uploaded to `_smoke/`, served
     from the public URL with the expected `Content-Type` and `Cache-Control`,
     then deleted from R2.

## Commands

```bash
python3 scripts/r2_asset_publish.py doctor
python3 scripts/r2_asset_publish.py init
python3 scripts/r2_asset_publish.py setup
python3 scripts/r2_asset_publish.py optimize image.png --out-dir /tmp/r2-assets
python3 scripts/r2_asset_publish.py publish article.md --write
python3 scripts/r2_asset_publish.py check blog wechat --published-only
python3 scripts/r2_asset_publish.py catalog --html /tmp/r2-assets.html
python3 scripts/r2_asset_publish.py find keyword
python3 scripts/r2_asset_publish.py smoke --wait-seconds 180
```

## Defaults

- Bucket: `laifuyou-assets`
- Domain: `assets.laifuyou.com`
- Public base URL: `https://assets.laifuyou.com`
- Zone ID: `caf7791839a1c0ef2115d1b9e73234a8`
- Cache-Control: `public, max-age=31536000, immutable`
- Project manifest: `.r2-assets/manifest.json`

## Resources

- `references/cloudflare-r2.md`: Wrangler resolver, R2 setup, cache, domain,
  and live verification rules.
- `references/markdown-assets.md`: Markdown image parsing and rewrite contract.
- `references/manifest-schema.md`: manifest source of truth and dedupe model.
- `references/posts-workflow.md`: posts/blog/wechat prefix and archive flow.
- `scripts/r2_asset_publish.py`: deterministic asset publishing CLI.
