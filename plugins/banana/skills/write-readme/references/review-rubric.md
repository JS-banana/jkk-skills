# README Review Rubric

Use this for audits and before presenting a generated README.

## Veto Rules

Any veto blocks an A/S grade regardless of total score:

- Missing project name or value proposition.
- No locally supported install/setup or usage path.
- Commands, badges, links, screenshots, APIs, or config options are fabricated.
- Existing accurate README content was removed without reason.
- Broken relative links or images are present and not reported.
- Secrets or private tokens appear in examples.

## Scorecard

Score out of 100:

| Dimension | Points | What to check |
|-----------|--------|---------------|
| Evidence and accuracy | 30 | Claims trace to local files or user input; no invented badges, commands, assets, or status. |
| First-screen clarity | 15 | A new reader knows what it is, who it is for, and why it matters within seconds. |
| Runnable path | 20 | Install/setup and usage are copy-pasteable, ordered, and suited to the project type. |
| Structure and navigation | 15 | Sections match the chosen shape; optional sections are included only when useful. |
| Writing quality | 10 | Concrete language, consistent terms, short paragraphs, no generic filler. |
| Maintenance | 10 | Links/assets resolve, commands are easy to re-check, future docs have clear owners or pointers. |

## Grade Scale

| Grade | Score | Meaning |
|-------|-------|---------|
| S | 90-100 | Strong enough to serve as a project-facing example. |
| A | 80-89 | High quality with small improvements possible. |
| B | 70-79 | Usable but at least one important dimension needs work. |
| C | 60-69 | Basic shape exists, but multiple gaps remain. |
| D | 50-59 | Significant rewrite needed. |
| F | 0-49 | Not trustworthy or not useful. |

## Report Format

```markdown
## README Review

Score: 82/100 (A)

Findings:
- High: [unsupported badge] The npm badge has no local or user-provided proof of publication.
- Medium: [quick start] The first runnable example appears after installation details.

Passed:
- Project purpose is clear in the first screen.
- Usage command is backed by `package.json` bin field.

Assumptions:
- Repository remote is public, but package publication was not verified.

Validation:
- `python3 scripts/validate.py --readme README.md` passed.
```

For code-review style requests, lead with findings before score or summary.

## Manual Judgment Prompts

- Would a new reader know whether this project is for them?
- Can the reader run one useful path without guessing?
- Does every status marker have evidence?
- Are examples real enough to copy, but small enough to scan?
- Is the README an entry point, not a full internal manual?
