#!/usr/bin/env python3
"""Overlay exact short labels on an illustration using normalized coordinates."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:  # pragma: no cover - exercised only without Pillow
    raise SystemExit("Pillow is required: python3 -m pip install Pillow") from exc


def resolve_font(explicit: str | None, family: str) -> tuple[Path, int]:
    if explicit:
        path = Path(explicit).expanduser()
        if not path.is_file():
            raise SystemExit(f"Font file not found: {path}")
        return path, 0

    if not shutil.which("fc-match"):
        raise SystemExit("No font supplied and fc-match is unavailable; pass --font PATH")

    result = subprocess.run(
        ["fc-match", "-f", "%{family}\t%{file}\t%{index}\n", family],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    matched_family, file_name, index = result.split("\t", 2)
    if family.casefold() not in matched_family.casefold():
        raise SystemExit(f"Handwriting font family not found: {family}; pass --font PATH")
    path = Path(file_name)
    if not path.is_file():
        raise SystemExit(f"Resolved font file not found: {path}")
    return path, int(index)


def load_labels(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    labels = data.get("labels") if isinstance(data, dict) else data
    if not isinstance(labels, list) or not labels:
        raise SystemExit("Labels JSON must be a non-empty list or an object with labels[]")

    for index, label in enumerate(labels):
        if not isinstance(label, dict) or not str(label.get("text", "")).strip():
            raise SystemExit(f"Label {index} needs non-empty text")
        for key in ("x", "y"):
            value = label.get(key)
            if not isinstance(value, (int, float)) or not 0 <= value <= 1:
                raise SystemExit(f"Label {index} {key} must be between 0 and 1")
        size = label.get("size", 0.055)
        if not isinstance(size, (int, float)) or not 0.01 <= size <= 0.25:
            raise SystemExit(f"Label {index} size must be between 0.01 and 0.25")
        if label.get("anchor", "center") not in {"left", "center", "right"}:
            raise SystemExit(f"Label {index} anchor must be left, center, or right")
    return labels


def overlay(
    image: Image.Image,
    labels: list[dict],
    font_path: Path,
    font_index: int,
) -> Image.Image:
    result = image.convert("RGBA")
    short_edge = min(result.size)

    for label in labels:
        pixels = max(12, round(short_edge * float(label.get("size", 0.055))))
        font = ImageFont.truetype(str(font_path), pixels, index=font_index)
        text = str(label["text"]).strip()
        color = label.get("color", "#272522")
        rotation = float(label.get("rotation", 0))
        anchor = label.get("anchor", "center")

        probe = ImageDraw.Draw(result)
        left, top, right, bottom = probe.textbbox((0, 0), text, font=font)
        padding = max(6, pixels // 4)
        layer = Image.new("RGBA", (right - left + padding * 2, bottom - top + padding * 2))
        ImageDraw.Draw(layer).text((padding - left, padding - top), text, font=font, fill=color)
        if rotation:
            layer = layer.rotate(rotation, resample=Image.Resampling.BICUBIC, expand=True)

        x = round(result.width * float(label["x"]))
        y = round(result.height * float(label["y"]))
        x -= {"left": 0, "center": layer.width // 2, "right": layer.width}[anchor]
        y -= layer.height // 2
        if x < 0 or y < 0 or x + layer.width > result.width or y + layer.height > result.height:
            raise SystemExit(f"Label falls outside the image: {text}")
        result.alpha_composite(layer, (x, y))

    return result


def save_image(image: Image.Image, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() in {".jpg", ".jpeg"}:
        image.convert("RGB").save(output, quality=95)
    else:
        image.save(output)


def self_test(family: str) -> None:
    font_path, font_index = resolve_font(None, family)
    canvas = Image.new("RGB", (640, 360), "#f6f4ef")
    labels = [{"text": "清晰表达", "x": 0.5, "y": 0.5, "size": 0.1}]
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "test.png"
        save_image(overlay(canvas, labels, font_path, font_index), output)
        if not output.is_file() or output.stat().st_size == 0:
            raise SystemExit("Self-test failed to write output")
    print(f"PASS overlay self-test ({font_path})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path)
    parser.add_argument("output", nargs="?", type=Path)
    parser.add_argument("labels", nargs="?", type=Path)
    parser.add_argument("--font", help="Explicit TTF/OTF/TTC font path")
    parser.add_argument("--font-family", default="Hannotate SC")
    parser.add_argument("--font-index", type=int)
    parser.add_argument("--force", action="store_true", help="Allow replacing output")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test(args.font_family)
        return
    if not all((args.input, args.output, args.labels)):
        parser.error("input, output, and labels JSON are required")
    if args.input.resolve() == args.output.resolve():
        raise SystemExit("Input and output must be different files")
    if args.output.exists() and not args.force:
        raise SystemExit(f"Output already exists: {args.output}; pass --force to replace it")

    font_path, resolved_index = resolve_font(args.font, args.font_family)
    font_index = args.font_index if args.font_index is not None else resolved_index
    labels = load_labels(args.labels)
    with Image.open(args.input) as source:
        save_image(overlay(source, labels, font_path, font_index), args.output)
    print(args.output)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        raise SystemExit(str(exc)) from exc
