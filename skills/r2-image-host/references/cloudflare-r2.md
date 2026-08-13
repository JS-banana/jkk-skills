# Cloudflare R2 Reference

Use Wrangler as the operational surface. Do not require API tokens when the
user already has Wrangler OAuth login.

## Wrangler Resolution

`scripts/r2_asset_publish.py` resolves Wrangler in this order:

1. `R2_ASSET_WRANGLER`
2. `wrangler` from `PATH`
3. `npx --no-install wrangler`

If none work, report an install hint. Do not install Wrangler automatically.

## Default Target

- Account: current Wrangler login
- Bucket: `laifuyou-assets`
- Domain: `assets.laifuyou.com`
- Public base URL: `https://assets.laifuyou.com`
- Zone ID: `caf7791839a1c0ef2115d1b9e73234a8`

## R2 Setup

Use these commands through the script, not by hand unless debugging:

```bash
wrangler r2 bucket info laifuyou-assets --json
wrangler r2 bucket create laifuyou-assets
wrangler r2 bucket domain list laifuyou-assets
wrangler r2 bucket domain add laifuyou-assets \
  --domain assets.laifuyou.com \
  --zone-id caf7791839a1c0ef2115d1b9e73234a8 \
  --min-tls 1.2 \
  --force
```

Do not enable `r2.dev` for production. R2 public buckets should use a custom
domain for cache, WAF, and production access.

## Upload Contract

Use `wrangler r2 object put` with HTTP metadata:

```bash
wrangler r2 object put <bucket>/<key> \
  --file <optimized-file> \
  --content-type <mime> \
  --cache-control "public, max-age=31536000, immutable" \
  --remote \
  --force
```

Wrangler's object command does not provide a stable custom metadata flag, so
business metadata lives in the manifest.

## Verification

Live verification is complete only when:

- The object upload exits successfully.
- The public URL returns HTTP 200.
- `Content-Type` matches the optimized file.
- `Cache-Control` contains `max-age=31536000`.
- The returned byte count is non-zero.
- The smoke object is deleted and `wrangler r2 object get` confirms the key is
  gone from R2.

If a new custom domain is still initializing, poll and report the wait rather
than switching to `r2.dev`.

After deletion, a just-fetched public URL may still return from Cloudflare edge
cache because published assets use immutable long caching. Treat R2 object
lookup, not public URL status, as the deletion source of truth.
