import { extname } from "node:path";
import { atomicWriteImage, assertOutputIsSafe } from "../core/fs.js";
import { VisualAssetsError } from "../core/errors.js";
import { readOrientedImage } from "../core/image.js";
import type { ImageDimensions } from "../core/types.js";
import sharp from "sharp";

function escapeXml(value: string): string {
  return value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
}

function gridSvg(size: ImageDimensions): Buffer {
  const { width, height } = size;
  const lines: string[] = [];
  const labelSize = Math.max(12, Math.round(Math.min(width, height) / 55));
  for (let index = 0; index <= 10; index += 1) {
    const x = Math.round((index / 10) * width);
    const y = Math.round((index / 10) * height);
    lines.push(`<line x1="${x}" y1="0" x2="${x}" y2="${height}" stroke="#00ffff" stroke-opacity="0.45" stroke-width="${index === 0 || index === 10 ? 4 : 2}"/>`);
    lines.push(`<line x1="0" y1="${y}" x2="${width}" y2="${y}" stroke="#00ffff" stroke-opacity="0.45" stroke-width="${index === 0 || index === 10 ? 4 : 2}"/>`);
    const text = `${index / 10}`;
    lines.push(`<text x="${Math.min(width - labelSize * 2, x + 4)}" y="${Math.max(labelSize, labelSize + 2)}" font-family="Arial,sans-serif" font-size="${labelSize}" font-weight="700" fill="#001b1f" stroke="#ffffff" stroke-width="3" paint-order="stroke">${escapeXml(text)}</text>`);
    lines.push(`<text x="${Math.min(width - labelSize * 2, labelSize + 4)}" y="${Math.min(height - 4, Math.max(labelSize, y - 4))}" font-family="Arial,sans-serif" font-size="${labelSize}" font-weight="700" fill="#001b1f" stroke="#ffffff" stroke-width="3" paint-order="stroke">${escapeXml(text)}</text>`);
  }
  const border = `<rect x="2" y="2" width="${Math.max(0, width - 4)}" height="${Math.max(0, height - 4)}" fill="none" stroke="#ff2d55" stroke-width="5"/>`;
  return Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">${lines.join("")}${border}</svg>`);
}

export async function createAnalysisBoard(input: string, output: string): Promise<{ ok: true; command: "analysis-board"; input: string; output: string; width: number; height: number }> {
  await assertOutputIsSafe(input, output);
  if (extname(output).toLowerCase() !== ".png") {
    throw new VisualAssetsError("ANALYSIS_BOARD_FORMAT", "analysis-board output must use a .png extension", { output });
  }
  const image = await readOrientedImage(input);
  await atomicWriteImage(output, async (temporary) => {
    await sharp(image.buffer, { failOn: "error" }).composite([{ input: gridSvg(image.size) }]).png().toFile(temporary);
  });
  return { ok: true, command: "analysis-board", input, output, ...image.size };
}
