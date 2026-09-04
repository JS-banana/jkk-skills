# Planning an Article's Visual Layer

Read the full stable article before choosing images. Plan from cognitive load and evidence needs, not section count or a fixed number of pictures.

## Visual functions

Use one primary function per planned asset:

| Function | Reader result | Typical routes |
| --- | --- | --- |
| `evidence` | verifies a public claim or source | runtime, webpage, social post, paper, public record |
| `demonstration` | sees the product or process actually working | author screenshot, element capture, before/after |
| `explanation` | understands an invisible mechanism | diagram, annotated screenshot, original explainer |
| `comparison` | compares options or values quickly | table image, chart, aligned screenshots |
| `navigation` | keeps orientation in a long process | timeline, workflow, staged screenshots |
| `atmosphere` | establishes emotion or human context | real scene, editorial illustration |
| `cover` | receives the title's promise at a glance | strongest route for that promise |

If an asset cannot be assigned a function and article anchor, omit it.

## Candidate scoring

Do not impose a universal source hierarchy. Score candidates against the article:

- **claim relevance:** directly serves the adjacent statement or concept;
- **authenticity:** shows a real artifact, behavior, statement, or clearly original illustration;
- **glance comprehension:** a reader gets the main point without opening the original;
- **reading-width legibility:** meaningful content survives mobile and desktop placement;
- **visual interest:** earns attention without becoming decoration.

Author and runtime materials are often strong because they combine authenticity and uniqueness. Official material may be precise but visually poor. A public media or social explanation can be the display asset while an authoritative source remains the fact source.

## Source routing

For each plan entry, record a preferred route and at least one realistic alternative when the preferred route is uncertain.

```json
{
  "id": "V-agent-control",
  "position": "after:agent-control-explanation",
  "function": "demonstration",
  "serves": "The reader can take over or stop the running Agent.",
  "altText": "Agent task bar with Take over and Stop controls",
  "preferredRoute": "runtime-screenshot",
  "alternatives": ["public-product-page", "annotated-ui-crop"],
  "status": "planned"
}
```

## Height and legibility

Treat height as a reading-budget decision, not a global aspect-ratio rule.

- Remove browser chrome, navigation, sidebars, empty canvas, and unrelated conversation turns.
- Keep enough context to prevent a misleading crop.
- Split tall screenshots at semantic boundaries with a small overlap.
- Use a focused summary image plus a high-resolution original when direct reading and detail inspection need different scales.
- Preserve a vertical exception when splitting would destroy the structure.
- Never stretch, squeeze, or repeatedly recompress an asset.

The preview at channel width decides whether the result works. A 5:1 strip with tiny dense text can fail; a 1.6:1 product scene can pass when its visual meaning is immediate.

## Plan lifecycle

`visual-plan.json` belongs to the visual run and references the canonical article version. Recommended statuses:

`planned -> acquiring -> candidate -> approved -> placed`, with `blocked` and `rejected` as terminal branches for a candidate.

Changing an image without changing its served claim is an asset revision. Discovering a conflicting number, quote, behavior, or identity is a content finding and must return to the article gate.

Use this top-level shape so the plan remains readable across Agents:

```json
{
  "version": 1,
  "article": {"path": "../article.md", "version": "v3"},
  "channels": ["wechat", "desktop"],
  "items": [
    {
      "id": "V-agent-control",
      "position": "after:agent-control-explanation",
      "function": "demonstration",
      "serves": "The reader can take over or stop the running Agent.",
      "altText": "Agent task bar with Take over and Stop controls",
      "preferredRoute": "runtime-screenshot",
      "alternatives": ["public-product-page", "annotated-ui-crop"],
      "evidenceIds": ["E-agent-control"],
      "status": "planned"
    }
  ]
}
```

Do not put pixel recipes in the plan. They belong to `manifest.json` after a candidate is actually produced.
