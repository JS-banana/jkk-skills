import sharp, { type OverlayOptions } from "sharp";
import { VisualAssetsError } from "../core/errors.js";
import type { OperationSpec, ResolvedRect } from "../core/types.js";
import { resolvePoint, resolveRect } from "./geometry.js";

function escapeXml(value: unknown): string {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}

function numberValue(value: unknown, fallback: number): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function colorValue(value: unknown, fallback: string): string {
  return typeof value === "string" && value.length > 0 ? value : fallback;
}

function annotationRect(item: Record<string, unknown>, width: number, height: number, index: number): ResolvedRect {
  const value = item.region ?? item.rect ?? item.box ?? item;
  return resolveRect(value, width, height, `annotate[${index}]`);
}

function svgForAnnotations(items: Array<Record<string, unknown>>, width: number, height: number): string {
  const content: string[] = [];
  const defs = `<defs><marker id="va-arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="#e11d48"/></marker></defs>`;
  items.forEach((item, index) => {
    const type = String(item.type ?? item.kind ?? "box").toLowerCase();
    if (["blur", "redact", "zoom", "zoom-inset", "zoom_inset", "zoominset"].includes(type)) return;
    const color = colorValue(item.color, type === "highlight" ? "#f59e0b" : "#e11d48");
    const strokeWidth = Math.max(1, numberValue(item.strokeWidth, Math.max(2, Math.round(Math.min(width, height) / 300))));
    if (type === "arrow") {
      const fallbackRect = item.region ?? item.rect ?? item.box;
      const rect = fallbackRect === undefined ? undefined : annotationRect(item, width, height, index);
      const from = item.from ? resolvePoint(item.from, width, height, `annotate[${index}].from`) : rect ? { x: rect.left, y: rect.top + Math.floor(rect.height / 2) } : undefined;
      const to = item.to ? resolvePoint(item.to, width, height, `annotate[${index}].to`) : rect ? { x: rect.left + Math.floor(rect.width / 2), y: rect.top + Math.floor(rect.height / 2) } : undefined;
      if (!from || !to) throw new VisualAssetsError("ARROW_POINTS_REQUIRED", `annotate[${index}] arrow requires from and to points or a region`, { index });
      content.push(`<line x1="${from.x}" y1="${from.y}" x2="${to.x}" y2="${to.y}" stroke="${escapeXml(color)}" stroke-width="${strokeWidth}" stroke-linecap="round" marker-end="url(#va-arrow)"/>`);
    } else {
      const rect = annotationRect(item, width, height, index);
      if (type === "highlight") {
      const opacity = Math.max(0, Math.min(1, numberValue(item.opacity, 0.28)));
      content.push(`<rect x="${rect.left}" y="${rect.top}" width="${rect.width}" height="${rect.height}" fill="${escapeXml(color)}" fill-opacity="${opacity}" stroke="${escapeXml(color)}" stroke-width="${strokeWidth}"/>`);
      } else if (type === "box") {
      content.push(`<rect x="${rect.left}" y="${rect.top}" width="${rect.width}" height="${rect.height}" fill="none" stroke="${escapeXml(color)}" stroke-width="${strokeWidth}"/>`);
      } else if (type === "number") {
      const label = escapeXml(item.label ?? item.value ?? index + 1);
      const radius = Math.max(12, numberValue(item.radius, Math.min(rect.width, rect.height, 28) / 2));
      const cx = rect.left + radius + 3;
      const cy = rect.top + radius + 3;
      content.push(`<circle cx="${cx}" cy="${cy}" r="${radius}" fill="${escapeXml(color)}" stroke="#ffffff" stroke-width="2"/><text x="${cx}" y="${cy + radius * 0.35}" text-anchor="middle" font-family="Arial,sans-serif" font-size="${Math.max(11, radius)}" font-weight="700" fill="#ffffff">${label}</text>`);
      } else {
      throw new VisualAssetsError("UNSUPPORTED_ANNOTATION", `Unsupported annotation type: ${type}`, { type, index });
      }
    }
  });
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">${defs}${content.join("")}</svg>`;
}

function insetRect(item: Record<string, unknown>, width: number, height: number, index: number): ResolvedRect {
  const inset = item.inset;
  if (inset && typeof inset === "object") return resolveRect(inset, width, height, `annotate[${index}].inset`);
  const insetWidth = Math.max(1, Math.round(numberValue(item.insetWidth, Math.round(width * 0.32))));
  const insetHeight = Math.max(1, Math.round(numberValue(item.insetHeight, Math.round(height * 0.32))));
  const margin = Math.max(4, Math.round(Math.min(width, height) * 0.03));
  return { left: Math.max(0, width - insetWidth - margin), top: margin, width: Math.min(insetWidth, width), height: Math.min(insetHeight, height) };
}

export async function applyAnnotate(buffer: Buffer, operation: OperationSpec): Promise<Buffer> {
  const metadata = await sharp(buffer, { failOn: "error" }).metadata();
  const width = metadata.width ?? 0;
  const height = metadata.height ?? 0;
  const rawItems = operation.annotations ?? operation.items;
  if (!Array.isArray(rawItems)) throw new VisualAssetsError("ANNOTATIONS_REQUIRED", "annotate requires an annotations array");
  const items = rawItems as Array<Record<string, unknown>>;
  const composites: OverlayOptions[] = [];
  const rasterTypes = new Set(["blur", "redact", "zoom", "zoom-inset", "zoom_inset", "zoominset"]);
  for (let index = 0; index < items.length; index += 1) {
    const item = items[index];
    if (!item || typeof item !== "object" || Array.isArray(item)) throw new VisualAssetsError("INVALID_ANNOTATION", `annotate[${index}] must be an object`, { index });
    const type = String(item.type ?? item.kind ?? "box").toLowerCase();
    if (type === "blur") {
      const rect = annotationRect(item, width, height, index);
      const sigma = Math.max(0.3, Math.min(100, numberValue(item.sigma, 12)));
      const patch = await sharp(buffer, { failOn: "error" }).extract(rect).blur(sigma).png().toBuffer();
      composites.push({ input: patch, left: rect.left, top: rect.top });
    } else if (type === "redact") {
      const rect = annotationRect(item, width, height, index);
      const fill = colorValue(item.color ?? item.fill, "#111827");
      const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${rect.width}" height="${rect.height}"><rect width="100%" height="100%" fill="${escapeXml(fill)}"/></svg>`;
      composites.push({ input: Buffer.from(svg), left: rect.left, top: rect.top });
    } else if (["zoom", "zoom-inset", "zoom_inset", "zoominset"].includes(type)) {
      const sourceRect = annotationRect(item, width, height, index);
      const targetRect = insetRect(item, width, height, index);
      const patch = await sharp(buffer, { failOn: "error" }).extract(sourceRect).resize({ width: targetRect.width, height: targetRect.height, fit: "contain", withoutEnlargement: false }).png().toBuffer();
      composites.push({ input: patch, left: targetRect.left, top: targetRect.top });
      const border = `<svg xmlns="http://www.w3.org/2000/svg" width="${targetRect.width}" height="${targetRect.height}"><rect x="1" y="1" width="${Math.max(0, targetRect.width - 2)}" height="${Math.max(0, targetRect.height - 2)}" fill="none" stroke="${escapeXml(colorValue(item.color, "#2563eb"))}" stroke-width="3"/></svg>`;
      composites.push({ input: Buffer.from(border), left: targetRect.left, top: targetRect.top });
    }
  }
  const vectorItems = items.filter((item) => !rasterTypes.has(String(item.type ?? item.kind ?? "box").toLowerCase()));
  if (vectorItems.length > 0) composites.push({ input: Buffer.from(svgForAnnotations(vectorItems, width, height)) });
  if (composites.length === 0) return buffer;
  return sharp(buffer, { failOn: "error" }).composite(composites).toBuffer();
}
