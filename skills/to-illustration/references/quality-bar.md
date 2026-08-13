# Quality Bar

## Hard gates

Reject the image if any item fails:

- It communicates exactly one thesis.
- Objects share perspective, ground or a coherent spatial frame.
- No important subject, character or label is cropped.
- No sticker collage, card grid, formal diagram or PPT title treatment appears.
- The traveler is load-bearing when present and matches the canonical sheet.
- Every requested character is exact, readable and attached to the right visual idea.
- Visible text matches the canonical lettering board: intentional hierarchy, one writer, natural baseline and spacing variation, and no typeset regularity.
- There is no extra title, unrequested English, watermark, logo or prompt leakage.
- The image borrows no distinctive character, prop or composition from a reference.

## Aesthetic score

Score `0` (fails), `1` (usable), or `2` (strong):

- **Hierarchy:** the focal action is immediate.
- **Composition:** asymmetry, depth and quiet space feel intentional.
- **Cohesion:** every element inhabits the same world.
- **Line:** graphite, hatching and lettering establish form without becoming uniformly busy or mechanically regular.
- **Taste:** the result feels editorial and specific, not generic AI illustration.

Deliver only when all hard gates pass and the total is at least `7/10`.

## Failure tags and one-change repairs

| Tag | Repair |
|---|---|
| `weak-thesis` | Remove the secondary idea and restate the focal action |
| `collage` | Replace symbols with one ground, object relationship or physical mechanism |
| `flat-scale` | Introduce foreground/background separation or one meaningful scale contrast |
| `too-dense` | Remove props and hatching outside the focal region |
| `decorative-character` | Give the traveler the decisive action or remove it |
| `too-cute` | Reduce eye size and expression; restore calm posture and practical action |
| `style-drift` | Reapply the canonical board and lock canvas, line and single accent |
| `too-typeset` | Keep the exact strings and layout; repair only baseline, spacing, character boxes and pressure against the lettering board |
| `text-overload` | Remove the least necessary label or split the thesis; do not shrink everything into a legend |
| `text-error` | Run one text-only repair, then blank-zone regeneration and overlay |
| `copied-scene` | Keep the thesis but replace viewpoint, physical action and principal object |

Repair the lowest-scoring dimension first. Recheck every hard gate after each edit.
