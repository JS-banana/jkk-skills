# Content Presentation Grammar

Use this reference to turn source material into a presentation plan. A plan is
an information-architecture decision, not a CSS theme and not a shortened copy
of the Markdown.

## Design read

Before writing presentation JSON, record:

- **Page kind:** technical field guide, research dossier, comparison, case
  study or linear document.
- **Audience:** the people who must decide, implement, review or learn.
- **Vibe:** a concrete reading character such as “evidence-first industrial
  editorial”, not “modern and clean”.
- **Narrative axis:** one source-supported transformation, for example
  “signal → resolution → runtime → delivery evidence”.
- **Dials (1–10):** design variance, motion intensity and visual density.

For technical field guides, start near variance 5–7, motion 1–3 and density
6–8. Adjust for the actual audience and material.

## First viewport

The opening must answer:

1. What is the governing decision or conclusion?
2. What system or delivery path organizes the report?
3. What is the current state?
4. What is the next move?

Do not begin with a generic description, decorative hero image, report counts
or a repeated card dashboard.

## Field-guide plan

Initialize the plan with `--init-presentation`, then fill the source-backed
modules:

```json
{
  "archetype": "field-guide",
  "design_read": {
    "page_kind": "Technical implementation field guide",
    "audience": "Engineering leads and delivery team",
    "vibe": "Evidence-first industrial editorial",
    "narrative_axis": "Signal → runtime → release evidence",
    "design_variance": 6,
    "motion_intensity": 2,
    "visual_density": 8
  },
  "eyebrow": "Program / Field guide",
  "deck": "One sentence describing the reader's job.",
  "summary": "The governing source-supported conclusion.",
  "next_move": "The next concrete action already required by the source.",
  "status": {"label": "In progress", "tone": "warning"},
  "system_flow": [
    {
      "label": "Short role",
      "detail": "What crosses this boundary",
      "kind": "signal",
      "source_section": "1. Conclusion"
    }
  ],
  "acceptance_lanes": [
    {
      "label": "Runtime",
      "state": "Real loading path",
      "items": ["Observable condition", "Observable condition"],
      "source_section": "2. Success criteria"
    }
  ],
  "decisions": [
    {
      "id": "D1",
      "title": "Decision title",
      "principle": "The implementation boundary it creates.",
      "source_section": "4. Decisions"
    }
  ],
  "workstreams": [
    {
      "id": "P1-00",
      "title": "Work package",
      "phase": "M0",
      "effort": "0.5–1 day",
      "status": "In progress",
      "depends_on": [],
      "source_section": "8. Work packages"
    }
  ],
  "risks": [
    {
      "risk": "What may fail",
      "signal": "The earliest observable symptom.",
      "response": "The source-approved containment action.",
      "source_section": "11. Risks"
    }
  ],
  "reading_path": ["1. Conclusion", "4. Decisions", "8. Work packages"]
}
```

Minimum counts are deliberate quality gates: three system steps, two
acceptance lanes, three decisions, three workstreams and two risks. If the
source does not contain those shapes, use the `document` archetype instead of
inventing them.

## Composition rules

- Synthesize the decision, constraint, dependency, evidence or next action.
- Keep one job per module: path, gate, ledger, delivery spine or risk signal.
- Use exact domain names and IDs where they matter.
- Keep pending, unverified and conditional scope visible.
- Bind every module item to the nearest real H2 `source_section`.
- Prefer five strong system handoffs over a graph of every implementation node.
- Keep detailed commands, tables and proof in the complete dossier.

## Integrity

- Do not upgrade a proposal, assumption or target into a current fact.
- Do not infer completion from a percentage or vague status.
- Do not invent owners, dates, versions, metrics, dependencies or citations.
- If a synthesis cannot be traced to a source heading, remove it.
