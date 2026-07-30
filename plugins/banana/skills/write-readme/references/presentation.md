# Presentation and Layout

How a README looks is part of what it communicates: visual hierarchy is how a
human decides in seconds whether to keep reading. Use this file when creating
or rewriting a README, or when the user asks for visual polish. Layout never
overrides evidence — every badge, image, and link still needs local backing
per `method.md` and `badges.md`.

## First-Screen Anatomy

For public repositories with visual identity, a centered header in this order:

```html
<div align="center">
  <img src="docs/assets/logo.png" width="120" alt="Project logo">
  <h1>project-name</h1>
  <p>One-line value proposition.</p>
  <p><!-- badge row --></p>
  <p>
    <a href="#quick-start">Quick Start</a> ·
    <a href="docs/">Docs</a> ·
    <a href="#examples">Examples</a>
  </p>
</div>
```

Rules:

- Order is logo → title → tagline → badges → nav links. Omit any missing piece
  rather than filling it with an invented asset.
- Nav links point only to sections and files that exist. A language switcher
  (see Bilingual README) joins this row with the same `·` separators.
- Use a plain Markdown H1 instead when the repo is internal, sparse, or has no
  logo; a centered header on an empty project reads as overcompensation.
- Registry pages (npm, PyPI, crates.io) sanitize or ignore some HTML, so keep
  the project name and value proposition readable as plain text even inside an
  HTML header, and never put critical facts only in HTML attributes.

## Two Legitimate Styles

A 2026-07 survey of 20 well-known repositories (react, vite, fastapi, ripgrep,
shadcn/ui, ant-design, dify, lobe-chat, and similar) shows two coherent
registers; pick one and stay consistent rather than mixing halves of each:

- **Engineering restraint** (the mainstream, and the default): plain or lightly
  centered header, 0-5 badges, no growth widgets. shadcn/ui's entire README is
  17 lines with one hero image; ripgrep leads with plain text. Restraint at
  high star counts reads as confidence.
- **Community product** (dify, lobe-chat): grouped badge wall split into rows
  with `<br/>`, star history chart, contributors wall, language switcher, and
  emoji on every major heading — all or none. Badge-heavy files stay editable
  only with reference-style links (`[![][shield]][link]` with definitions at
  the bottom of the file), and long ones add `<a name="readme-top"></a>` plus
  back-to-top links.

Choose community-product style only when the project actually courts a
community (open-source product, plugin ecosystem, self-host audience). Default
to restraint.

## Logo Sourcing

- Prefer an existing asset, in this order: files already in the repo
  (`docs/assets/`, `public/`, `.github/`), the project site's own CDN, the
  org/user avatar. In the survey, every logo was an existing brand asset —
  none were invented for the README.
- No logo is a respectable choice: use a plain H1, never a placeholder image.
- Generating a logo is a user decision. Offer it; on yes, produce a simple SVG
  wordmark, commit it to the repo (for example `docs/assets/logo.svg`), and
  reference it locally. Do not hotlink generated images from external hosts.

## Community and Growth Widgets

These widgets claim traction. Use them only on public repos where community
growth is part of the pitch; on a young or internal repo they advertise the
absence of what they measure.

- Star history chart: place it in the community/contributing section near the
  bottom, dark-mode aware, collapsed in `<details>` when the section is long.
  Requires a public repo and the real owner/repo substituted:

```html
<picture>
  <source media="(prefers-color-scheme: dark)"
          srcset="https://api.star-history.com/svg?repos=owner-name/repo-name&type=Date&theme=dark">
  <img src="https://api.star-history.com/svg?repos=owner-name/repo-name&type=Date"
       alt="Star history chart" width="100%">
</picture>
```

- Contributors wall (`https://contrib.rocks/image?repo=owner-name/repo-name`)
  only when there is a real multi-contributor base to show.
- Sponsor sections only when sponsorship actually exists (GitHub Sponsors or
  OpenCollective evidence), per the no-invented-claims rule in `method.md`.

## Media

- UI projects: one hero screenshot or short GIF/video directly after the first
  screen. One strong visual beats four weak ones.
- Constrain size with `width=` on an `<img>` tag; always set `alt`.
- Store assets in the repo (for example `docs/assets/`) so links cannot rot;
  do not hotlink third-party hosts.
- Dark/light adaptive images when both variants exist:

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/hero-dark.png">
  <img src="docs/assets/hero-light.png" alt="Screenshot" width="720">
</picture>
```

## GitHub-Flavored Building Blocks

- Alerts for genuinely important asides, at most one per screen:
  `> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]`, `> [!CAUTION]`.
  These render only on GitHub; content must still make sense as a plain quote.
- `<details><summary>…</summary></details>` for long optional content: full
  CLI flag tables, FAQ, changelog excerpts. Never collapse the quick start or
  install steps.
- Mermaid code blocks for architecture only when the system is complex enough
  that readers need the mental model.
- Add a table of contents only when the README exceeds roughly two screens and
  GitHub's auto-generated outline is not enough; link real headings only.

## Rhythm and Scannability

- Short paragraphs (three lines or fewer); one idea per section.
- Lists for parallel facts; tables only for enumerable data such as config
  options, commands, or compatibility matrices — explanations go in prose.
- Emoji in section headings is a binary style choice: all major sections or
  none. Pick task-relevant emoji, and skip them for formal or enterprise
  projects.
- Blank line before and after every heading, code block, and table.
- Horizontal rules sparingly — headings already separate sections.

## Bilingual README

- Keep the canonical `README.md` in the primary audience's language; add the
  second language as `README.zh-CN.md`, `README.en.md`, or similar.
- Put a language switcher line directly under the title in both files:

```markdown
**English** | [简体中文](README.zh-CN.md)
```

- Keep both files structurally aligned and self-contained. When updating one,
  update the other or flag the stale one in the report — a silently outdated
  translation is worse than none.
