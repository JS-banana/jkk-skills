# Visual Routing

Choose the visual from the relationship being explained. A visual system is
part of information architecture, not decoration.

| Information job | Primary form |
| --- | --- |
| Main implementation or delivery path | `system_flow` semantic path |
| Independent acceptance dimensions | `acceptance_lanes` |
| Settled architectural boundaries | `decisions` ledger |
| Work packages, dependencies and state | `workstreams` delivery spine |
| Risk, early signal and response | `risks` ledger |
| Architecture topology | Mermaid flowchart/architecture diagram |
| Interaction over time | Mermaid sequence diagram |
| State changes or lifecycle | Mermaid state diagram |
| Comparison or capability matrix | Semantic HTML table |
| Milestones or chronology | Timeline/table, or Mermaid Gantt |
| Code, commands or logs | Fenced code with a language label |
| Qualitative thesis or conceptual metaphor | Optional hand-drawn illustration |
| Numerical evidence | Source-backed table or SVG/chart |

## Typed diagram modes

Classify a precise diagram before drawing it:

- **Architecture:** components, boundaries and ownership.
- **Workflow:** actor lanes, decisions, handoffs and outputs.
- **Sequence:** time-ordered calls and replies.
- **Data flow:** transformations, stores and sinks.
- **Lifecycle:** states, events and terminal conditions.

Read the topology from source Mermaid when available, but recompose the main
reading path around one spatial narrative. Do not blindly promote a dense
source diagram into the hero.

## Tool routing

- Use semantic HTML/CSS first for paths, gates, ledgers and delivery status.
- Use Mermaid for exact, versionable topology and keep its source fallback.
- Use `shape-product-experience` when the report needs a redesign from product
  truth through experience architecture and art direction.
- Use `handdrawn-illustrator` for at most one conceptual explainer. Do not use
  it for strict topology, many nodes, numerical precision or UI screenshots.
- Add React, Canvas or WebGL only when native HTML/CSS/SVG cannot express the
  required interaction.

## Rules

- Every visual must answer one reader question.
- Preserve exact names, direction, cardinality and uncertainty from the source.
- Prefer one main path, few labelled edges and short side branches.
- A source section link is part of the visual, not optional metadata.
- Avoid visual duplication unless each form answers a different question.
- Every image needs useful alt text; interpretation must be labelled as such.
