# Evidence Ledger

Use this file before making research-backed claims. It is a local, durable
summary of the external material behind this skill. External links are for
refreshing or attribution, not required for normal execution.

Checked: 2026-06-09

## Evidence Strength

- Strong: empirical paper or official product documentation.
- Medium: first-party platform blog or cross-repo analysis with a described
  corpus, but not a controlled study.
- Weak: vendor guide, anecdotal blog, or synthesis useful for heuristics but
  not a general proof.

## Claims To Use

### Codex Discovery

- Claim: Codex discovers AGENTS guidance from global and project scopes, merges
  root-to-current-dir, and lets closer files override broader guidance.
  Strength: Strong.
  Source: OpenAI Codex docs.
  Boundary: Product behavior can change; refresh for exact config names.

- Claim: Codex uses `AGENTS.override.md` before `AGENTS.md` at the same level
  and can use configured fallback filenames.
  Strength: Strong.
  Source: OpenAI Codex docs.
  Boundary: Codex-specific; do not generalize to other tools.

- Claim: Codex has a default combined guidance byte limit, documented as 32 KiB
  at time of check.
  Strength: Strong.
  Source: OpenAI Codex docs.
  Boundary: Codex-specific; refresh before hard-coding in user docs.

### Claude Code Discovery

- Claim: Claude Code loads user-scope `~/.claude/CLAUDE.md` and project-tree
  `CLAUDE.md` files; nested files load when work happens in their directory.
  Strength: Strong.
  Source: Anthropic Claude Code memory docs.
  Boundary: Product behavior changes fast; refresh for exact scope names.

- Claim: CLAUDE.md supports `@path` import lines that inline other files, with
  a maximum depth of 5; imports inside code spans/blocks are not evaluated.
  Strength: Strong.
  Source: Anthropic Claude Code memory docs.
  Boundary: Claude-specific syntax; do not use it in AGENTS.md for other tools.

- Claim: Rule files under `.claude/rules/` load as additional persistent
  instructions at user or project scope.
  Strength: Medium.
  Source: Anthropic docs and observed product behavior.
  Boundary: Newer surface; verify against current docs before citing limits.

### AGENTS.md Format

- Claim: AGENTS.md is an open Markdown format for agent instructions, not a
  fixed schema.
  Strength: Strong.
  Source: agents.md official site.
  Boundary: Good reason to avoid rigid templates.

- Claim: Nested AGENTS.md files can scope guidance for subprojects; closest
  guidance wins in conflict.
  Strength: Strong.
  Source: agents.md official site and OpenAI Codex docs.
  Boundary: Exact mechanics vary by agent.

### Empirical Findings

- Claim: In one controlled study, LLM-generated context files tended to reduce
  task success and increase inference cost; developer-written files gave only
  modest gains.
  Strength: Strong.
  Source: Gloaguen et al., arXiv:2602.11988.
  Boundary: Use as caution, not universal law.

- Claim: Context files can change agent behavior by encouraging more
  exploration, testing, and file traversal.
  Strength: Strong.
  Source: Gloaguen et al., arXiv:2602.11988.
  Boundary: This can be useful or costly depending on task.

- Claim: Another study found AGENTS.md associated with lower median runtime and
  output tokens while maintaining comparable task completion behavior.
  Strength: Strong.
  Source: Lulla et al., arXiv:2601.20404.
  Boundary: Evidence is about efficiency, not necessarily task quality.

### Practice Guidance

- Claim: GitHub's cross-repo analysis recommends exact commands, boundaries,
  stack specificity, and concrete examples.
  Strength: Medium.
  Source: GitHub Blog, 2,500+ repositories.
  Boundary: Practice analysis, not controlled causal evidence.

- Claim: "Never commit secrets" appears as a common helpful boundary in
  GitHub's analysis.
  Strength: Medium.
  Source: GitHub Blog.
  Boundary: Not a substitute for secret scanning or permissions.

- Claim: HumanLayer argues CLAUDE.md/AGENTS.md should be short, broadly
  applicable, and use progressive disclosure.
  Strength: Weak-Medium.
  Source: HumanLayer blog.
  Boundary: Practical guidance; not a controlled study.

- Claim: Augment Code recommends focusing on non-inferable details and avoiding
  redundant docs.
  Strength: Weak.
  Source: Augment Code guide.
  Boundary: Vendor guide; useful synthesis, not independent proof.

- Claim: Phil Schmid synthesizes ETH/HumanLayer guidance into "less is more"
  AGENTS.md practices.
  Strength: Weak.
  Source: Phil Schmid blog.
  Boundary: Secondary synthesis; use for framing, not primary evidence.

- Claim: In underspecified software tasks, agents often benefit from asking
  targeted clarification questions.
  Strength: Strong.
  Source: Ambig-SWE, OpenReview ICLR 2026.
  Boundary: Applies to ambiguous user requests, not every context-file edit.

## Preferred Framing

Say:

- "The evidence supports keeping root context minimal and focused on
  non-inferable operating rules."
- "Auto-generated context should be treated as a draft that requires human
  pruning."
- "Long context files have a real opportunity cost; include only rules that
  prevent likely mistakes or save repeated discovery."
- "Use local verification for commands and paths."

Avoid saying:

- "AGENTS.md always improves performance."
- "AGENTS.md always hurts performance."
- "The six-section template is mandatory."
- "External blogs prove this rule."
- "The model will definitely follow every instruction."

## Source List

- Anthropic Claude Code memory docs:
  https://docs.claude.com/en/docs/claude-code/memory
- OpenAI Codex docs:
  https://developers.openai.com/codex/guides/agents-md
- AGENTS.md official site:
  https://agents.md/index
- Gloaguen et al., "Evaluating AGENTS.md":
  https://arxiv.org/abs/2602.11988
- Lulla et al., "On the Impact of AGENTS.md Files":
  https://arxiv.org/abs/2601.20404
- GitHub Blog, "How to write a great agents.md":
  https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/
- HumanLayer, "Writing a good CLAUDE.md":
  https://www.humanlayer.dev/blog/writing-a-good-claude-md
- Augment Code, "How to Build Your AGENTS.md":
  https://www.augmentcode.com/guides/how-to-build-agents-md
- Phil Schmid, "Writing a Good AGENTS.md":
  https://www.philschmid.de/writing-good-agents
- Ambig-SWE OpenReview:
  https://openreview.net/forum?id=X2yzXtH4wp
