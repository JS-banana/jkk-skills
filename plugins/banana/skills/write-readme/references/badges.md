# Badge Rules

Badges are status claims. Add them only when the repository or user provides
evidence.

## Evidence Requirements

| Badge type | Evidence required |
|------------|-------------------|
| GitHub Actions | `.github/workflows/*.yml` plus known owner/repo remote |
| License | `LICENSE` file or manifest license field |
| Runtime version | engines, `requires-python`, `go.mod`, `rust-toolchain`, CI matrix |
| Package version | Existing published package evidence or user confirmation |
| Coverage | Existing coverage service config or existing badge |
| Docker image | Docker Hub/GHCR evidence or user confirmation |
| Downloads/stars/social | Public repository/package evidence or user request |
| Security/scorecard | Existing config or user request for public repo |

When evidence is missing, omit the badge and mention the missing evidence in the
review report if it matters.

## Style Consistency

- Pick one shields.io `style` for the whole README — `flat` (default),
  `flat-square`, or `for-the-badge` — and never mix styles in one file.
- `for-the-badge` only suits a centered hero header; badges inside body
  sections stay `flat`/`flat-square`.
- Add `logo=` only for recognizable brands, and keep `logoColor` legible
  against the badge color.
- Color carries meaning: green for passing/stable, blue/gray for neutral
  information, red only for real failure states — never decoratively.

## Placement

- Put badges near the title or centered header.
- Use 0-5 badges for most projects. The badge-wall register (10+ badges grouped
  into rows with `<br/>`) is legitimate only as part of the full
  community-product style — see Two Legitimate Styles in
  `references/presentation.md`.
- Prefer useful operational badges over decorative badges.
- Keep style consistent.

Recommended order when all are backed:

1. CI/build/test status
2. Coverage or quality gate
3. Package/runtime version
4. License
5. Downloads or stars

## Common Badge Sources

Use only after substituting known owner/repo/package values:

```markdown
[![Tests](https://github.com/OWNER/REPO/actions/workflows/test.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![Node.js](https://img.shields.io/badge/node-%3E%3D18-339933?logo=node.js&logoColor=white)](https://nodejs.org/)
```

Do not leave `OWNER`, `REPO`, `{owner}`, `{repo}`, `user/repo`, or similar
placeholders in generated README output.
