# README Patterns

Use this after scanning the repository. Pick section priorities that explain the
project truthfully, but do not force a fixed README template.

## Selection Matrix

| Project signal | Shape | Prioritize |
|----------------|-------|------------|
| `bin` field, `commands/`, CLI entry point | CLI manual | command purpose, install, first invocation, flags, examples |
| Published or reusable package, exports, SDK API | Library | install, minimal import/use, API surface, compatibility |
| React/Vue/Svelte/Next/Vite app, UI-first repo | Web app | user-visible value, screenshot if real, local dev, env, build |
| Express/Fastify/FastAPI/Flask/API routes | Service/API | startup, env, endpoints, auth/data stores if real, tests |
| Personal utility, automation, data, desktop, mobile | Practical tool | real workflow, setup, run, output, recovery |
| Workspaces, packages/apps, Nx/Turbo/Lerna | Monorepo | repository map, workspace commands, package/app entry points |

If multiple signals appear, choose the entry path that matters most to the
reader and blend section priorities. A monorepo README should orient the
repository first, then link to package/app docs.

## Detection Signals

Check these sources before choosing:

- Manifests: `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`,
  `deno.json`, `composer.json`.
- Entrypoints: `bin`, `exports`, `main`, `src/index.*`, `cli.*`, route files,
  app directories.
- Scripts: install, dev, start, build, test, lint, release.
- CI: workflow names and commands that prove tests/builds exist.
- Assets/docs: screenshots, demo GIFs, docs site config, example projects.

## Section Menu

Usually required when supported by evidence:

- Title and one-line value proposition.
- Quick start or shortest runnable path.
- Installation or setup.
- Usage example.
- License status or explicit note that no license file is present.

Optional when real:

- Screenshots/demos for UI or visual output.
- Configuration table for user-facing options.
- API reference for libraries/services.
- Troubleshooting for common known failures.
- Development/contributing for open source or team projects.
- Architecture only for complex systems where readers need the mental model.

Use this as a menu, not a checklist. Omit any section that would require
guessing.

## Shape Notes

### CLI Manual

Lead with the command's job and one copy-paste invocation. Include flags,
configuration, integrations, shell completion, and troubleshooting only when
present.

### Library

Lead with the import and smallest working example. Include install, supported
runtimes, API surface, examples, TypeScript/types when real, compatibility, and
links to deeper docs.

### Web App

Lead with what the app does for users and a screenshot/demo if available.
Include local development, environment setup, build/deploy commands, major
screens/features, and where data/configuration comes from.

### Service/API

Lead with what the service exposes. Include local startup, environment
variables, API examples, auth if real, data stores, health checks, tests, and
deployment notes only when backed by files.

### Practical Tool

Lead with the real workflow: install, configure, run, inspect output. Keep
theory short. Include examples, data/config files, extension points, and failure
recovery only when discoverable.

### Monorepo

Lead with repository map and how to run the main app/package. Include package
manager, shared commands, per-package links, development flow, and ownership
boundaries only when useful.

## Header Style

See `references/presentation.md` for first-screen anatomy, media, GitHub
building blocks, and layout rhythm. Short version: centered HTML header only
for public repos with visual identity; plain Markdown H1 for sparse or
internal repos; 0-5 badges.
