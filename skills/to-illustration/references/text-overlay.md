# Exact Text Overlay

Use this only after two model text failures. It repairs correctness, not lettering style; reject the result if it looks typeset against `assets/lettering-board.jpg`.

## Requirements

- Python 3.10 or newer.
- Pillow in the active environment.
- An explicit TTF/OTF/TTC handwriting font, or `fc-match` plus the default `Hannotate SC` family.

The skill never installs dependencies or silently substitutes a generic font. A portable setup is:

```bash
python3 -m venv .venv-to-illustration
. .venv-to-illustration/bin/activate
python3 -m pip install Pillow
```

## Labels file

Coordinates and size are normalized to the canvas:

```json
{
  "labels": [
    {"text": "连接", "x": 0.52, "y": 0.28, "size": 0.055, "anchor": "center", "rotation": -1.5}
  ]
}
```

## Run

Prefer an explicit font path to avoid the optional fontconfig dependency:

```bash
python3 "$SKILL_DIR/scripts/overlay_labels.py" input.png output.png labels.json --font /path/to/font.ttf
```

Check the local environment before relying on the fallback:

```bash
python3 "$SKILL_DIR/scripts/overlay_labels.py" --self-test
```
