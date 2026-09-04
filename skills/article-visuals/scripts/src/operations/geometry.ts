import sharp, { type FitEnum } from "sharp";
import { assertCondition, VisualAssetsError } from "../core/errors.js";
import type { OperationSpec, RectSpec, ResolvedRect } from "../core/types.js";

function finiteNumber(value: unknown, name: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new VisualAssetsError("INVALID_COORDINATE", `${name} must be a finite number`, { name, value });
  }
  return value;
}

function positiveNumber(value: unknown, name: string): number {
  const number = finiteNumber(value, name);
  if (number <= 0) throw new VisualAssetsError("INVALID_DIMENSION", `${name} must be greater than zero`, { name, value });
  return number;
}

function sourceObject(spec: unknown): { source: Record<string, unknown>; mode?: string } {
  if (!spec || typeof spec !== "object" || Array.isArray(spec)) {
    throw new VisualAssetsError("INVALID_RECTANGLE", "A rectangle must be an object", { value: spec });
  }
  const value = spec as Record<string, unknown>;
  if (value.normalized && typeof value.normalized === "object") {
    return { source: value.normalized as Record<string, unknown>, mode: "normalized" };
  }
  if (value.pixel && typeof value.pixel === "object") {
    return { source: value.pixel as Record<string, unknown>, mode: "pixel" };
  }
  const nested = value.rect ?? value.region;
  if (nested && typeof nested === "object") {
    const child = nested as Record<string, unknown>;
    return { source: child, mode: String(child.mode ?? child.space ?? child.unit ?? value.mode ?? value.space ?? value.unit ?? "pixel") };
  }
  return { source: value, mode: String(value.mode ?? value.space ?? value.unit ?? "pixel") };
}

export function resolveRect(spec: unknown, width: number, height: number, label = "rectangle"): ResolvedRect {
  const { source, mode } = sourceObject(spec);
  const xValue = source.x ?? source.left;
  const yValue = source.y ?? source.top;
  const x = finiteNumber(xValue, `${label}.x`);
  const y = finiteNumber(yValue, `${label}.y`);
  const rectWidth = positiveNumber(source.width, `${label}.width`);
  const rectHeight = positiveNumber(source.height, `${label}.height`);
  const normalized = mode === "normalized";
  if (mode !== "normalized" && mode !== "pixel") {
    throw new VisualAssetsError("INVALID_COORDINATE_SPACE", `${label} space must be pixel or normalized`, { mode });
  }
  const left = normalized ? Math.round(x * width) : Math.round(x);
  const top = normalized ? Math.round(y * height) : Math.round(y);
  const finalWidth = normalized ? Math.round(rectWidth * width) : Math.round(rectWidth);
  const finalHeight = normalized ? Math.round(rectHeight * height) : Math.round(rectHeight);
  if (normalized && (x < 0 || y < 0 || x > 1 || y > 1 || rectWidth > 1 || rectHeight > 1 || x + rectWidth > 1 || y + rectHeight > 1)) {
    throw new VisualAssetsError("COORDINATE_OUT_OF_BOUNDS", `${label} normalized coordinates must be within [0, 1]`, {
      x,
      y,
      width: rectWidth,
      height: rectHeight,
    });
  }
  if (left < 0 || top < 0 || finalWidth <= 0 || finalHeight <= 0 || left + finalWidth > width || top + finalHeight > height) {
    throw new VisualAssetsError("COORDINATE_OUT_OF_BOUNDS", `${label} must be fully inside the image`, {
      left,
      top,
      width: finalWidth,
      height: finalHeight,
      imageWidth: width,
      imageHeight: height,
    });
  }
  return { left, top, width: finalWidth, height: finalHeight };
}

export function resolvePoint(spec: unknown, width: number, height: number, label = "point"): { x: number; y: number } {
  if (!spec || typeof spec !== "object" || Array.isArray(spec)) {
    throw new VisualAssetsError("INVALID_POINT", `${label} must be an object`, { value: spec });
  }
  const value = spec as Record<string, unknown>;
  const mode = String(value.mode ?? value.space ?? value.unit ?? "pixel");
  if (mode !== "pixel" && mode !== "normalized") {
    throw new VisualAssetsError("INVALID_COORDINATE_SPACE", `${label} space must be pixel or normalized`, { mode });
  }
  const x = finiteNumber(value.x, `${label}.x`);
  const y = finiteNumber(value.y, `${label}.y`);
  if (mode === "normalized") {
    if (x < 0 || x > 1 || y < 0 || y > 1) throw new VisualAssetsError("COORDINATE_OUT_OF_BOUNDS", `${label} normalized coordinates must be within [0, 1]`, { x, y });
    return { x: Math.round(x * width), y: Math.round(y * height) };
  }
  if (x < 0 || y < 0 || x > width || y > height) throw new VisualAssetsError("COORDINATE_OUT_OF_BOUNDS", `${label} must be inside the image`, { x, y, width, height });
  return { x: Math.round(x), y: Math.round(y) };
}

function backgroundOf(value: unknown): string | { r: number; g: number; b: number; alpha?: number } {
  if (typeof value === "string") return value;
  if (value && typeof value === "object" && !Array.isArray(value)) {
    const color = value as Record<string, unknown>;
    return {
      r: Math.max(0, Math.min(255, Math.round(finiteNumber(color.r, "background.r")))),
      g: Math.max(0, Math.min(255, Math.round(finiteNumber(color.g, "background.g")))),
      b: Math.max(0, Math.min(255, Math.round(finiteNumber(color.b, "background.b")))),
      ...(color.alpha === undefined ? {} : { alpha: Math.max(0, Math.min(1, finiteNumber(color.alpha, "background.alpha"))) }),
    };
  }
  return "#ffffff";
}

function positionOffsets(position: unknown, extraWidth: number, extraHeight: number): { left: number; top: number } {
  if (typeof position === "string") {
    const normalized = position.toLowerCase();
    const left = normalized.includes("left") ? 0 : normalized.includes("right") ? extraWidth : Math.floor(extraWidth / 2);
    const top = normalized.includes("top") ? 0 : normalized.includes("bottom") ? extraHeight : Math.floor(extraHeight / 2);
    return { left, top };
  }
  if (position && typeof position === "object" && !Array.isArray(position)) {
    const value = position as Record<string, unknown>;
    const left = value.left ?? value.x;
    const top = value.top ?? value.y;
    if (left !== undefined || top !== undefined) {
      const resolvedLeft = left === undefined ? 0 : finiteNumber(left, "pad.position.left");
      const resolvedTop = top === undefined ? 0 : finiteNumber(top, "pad.position.top");
      return {
        left: Math.max(0, Math.min(extraWidth, Math.round(resolvedLeft))),
        top: Math.max(0, Math.min(extraHeight, Math.round(resolvedTop))),
      };
    }
  }
  return { left: Math.floor(extraWidth / 2), top: Math.floor(extraHeight / 2) };
}

export async function applyCrop(buffer: Buffer, operation: OperationSpec): Promise<Buffer> {
  const metadata = await sharp(buffer, { failOn: "error" }).metadata();
  const width = metadata.width ?? 0;
  const height = metadata.height ?? 0;
  const rect = resolveRect(operation, width, height, "crop");
  return sharp(buffer, { failOn: "error" }).extract(rect).toBuffer();
}

export async function applyTrim(buffer: Buffer, operation: OperationSpec): Promise<Buffer> {
  const options: { background?: string | { r: number; g: number; b: number; alpha?: number }; threshold?: number } = {};
  if (operation.background !== undefined) options.background = backgroundOf(operation.background);
  if (operation.threshold !== undefined) {
    const threshold = finiteNumber(operation.threshold, "trim.threshold");
    if (threshold < 0 || threshold > 100) throw new VisualAssetsError("INVALID_TRIM_THRESHOLD", "trim.threshold must be between 0 and 100", { threshold });
    options.threshold = threshold;
  }
  return sharp(buffer, { failOn: "error" }).trim(options).toBuffer();
}

export async function applyResize(buffer: Buffer, operation: OperationSpec): Promise<Buffer> {
  const width = operation.width === undefined ? undefined : Math.round(positiveNumber(operation.width, "resize.width"));
  const height = operation.height === undefined ? undefined : Math.round(positiveNumber(operation.height, "resize.height"));
  if (width === undefined && height === undefined) throw new VisualAssetsError("RESIZE_DIMENSION_REQUIRED", "resize requires width or height");
  const fit = operation.fit === undefined ? "inside" : String(operation.fit);
  const allowedFits = new Set(["cover", "contain", "fill", "inside", "outside"]);
  if (!allowedFits.has(fit)) throw new VisualAssetsError("INVALID_RESIZE_FIT", `Unsupported resize fit: ${fit}`, { fit });
  const allowEnlarge = operation.allowEnlarge === true || operation.withoutEnlargement === false;
  return sharp(buffer, { failOn: "error" }).resize({
    width,
    height,
    fit: fit as keyof FitEnum,
    withoutEnlargement: !allowEnlarge,
  }).toBuffer();
}

export async function applyPad(buffer: Buffer, operation: OperationSpec): Promise<Buffer> {
  const metadata = await sharp(buffer, { failOn: "error" }).metadata();
  const width = metadata.width ?? 0;
  const height = metadata.height ?? 0;
  let targetWidth: number;
  let targetHeight: number;
  const target = operation.target;
  const targetObject = target && typeof target === "object" ? target as Record<string, unknown> : undefined;
  const widthValue = operation.width ?? targetObject?.width;
  const heightValue = operation.height ?? targetObject?.height;
  const aspectValue = operation.aspectRatio ?? operation.aspect ?? targetObject?.aspectRatio ?? targetObject?.aspect;
  if (widthValue !== undefined || heightValue !== undefined) {
    if (widthValue === undefined || heightValue === undefined) throw new VisualAssetsError("PAD_DIMENSIONS_REQUIRED", "pad requires both width and height when using explicit dimensions");
    targetWidth = Math.round(positiveNumber(widthValue, "pad.width"));
    targetHeight = Math.round(positiveNumber(heightValue, "pad.height"));
  } else if (aspectValue !== undefined) {
    const ratio = parseAspect(aspectValue);
    if (width / height < ratio) {
      targetWidth = Math.ceil(height * ratio);
      targetHeight = height;
    } else {
      targetWidth = width;
      targetHeight = Math.ceil(width / ratio);
    }
  } else {
    throw new VisualAssetsError("PAD_TARGET_REQUIRED", "pad requires target width/height or aspectRatio");
  }
  if (targetWidth < width || targetHeight < height) {
    throw new VisualAssetsError("PAD_TARGET_TOO_SMALL", "pad target must not crop the image", { width, height, targetWidth, targetHeight });
  }
  const offsets = positionOffsets(operation.position, targetWidth - width, targetHeight - height);
  return sharp(buffer, { failOn: "error" }).extend({
    left: offsets.left,
    right: targetWidth - width - offsets.left,
    top: offsets.top,
    bottom: targetHeight - height - offsets.top,
    background: backgroundOf(operation.background),
  }).toBuffer();
}

export function parseAspect(value: unknown): number {
  if (typeof value === "string" && value.includes(":")) {
    const [left, right] = value.split(":").map(Number);
    if (Number.isFinite(left) && Number.isFinite(right) && left > 0 && right > 0) return left / right;
  }
  const ratio = positiveNumber(value, "aspectRatio");
  if (!Number.isFinite(ratio)) throw new VisualAssetsError("INVALID_ASPECT_RATIO", "aspectRatio must be positive");
  return ratio;
}

export async function splitVertical(buffer: Buffer, operation: OperationSpec): Promise<Array<{ buffer: Buffer; rect: ResolvedRect }>> {
  const metadata = await sharp(buffer, { failOn: "error" }).metadata();
  const width = metadata.width ?? 0;
  const height = metadata.height ?? 0;
  const explicit = operation.segments ?? operation.regions;
  if (explicit !== undefined) {
    if (!Array.isArray(explicit) || explicit.length === 0) throw new VisualAssetsError("INVALID_SPLIT_SEGMENTS", "split.segments must be a non-empty array");
    const result: Array<{ buffer: Buffer; rect: ResolvedRect }> = [];
    for (let index = 0; index < explicit.length; index += 1) {
      const candidate = explicit[index];
      if (!candidate || typeof candidate !== "object" || Array.isArray(candidate)) throw new VisualAssetsError("INVALID_SPLIT_SEGMENT", `split.segments[${index}] must be a rectangle`, { index });
      const value = candidate as Record<string, unknown>;
      const normalized = String(value.mode ?? value.space ?? value.unit ?? (value.normalized ? "normalized" : "pixel"));
      const segment = value.width === undefined
        ? { ...value, x: normalized === "normalized" ? 0 : 0, width: normalized === "normalized" ? 1 : width }
        : value;
      const rect = resolveRect(segment, width, height, `split.segments[${index}]`);
      if (rect.left !== 0 || rect.width !== width) throw new VisualAssetsError("INVALID_SPLIT_SEGMENT", "Vertical split segments must span the full image width", { index, rect, width });
      result.push({ rect, buffer: await sharp(buffer, { failOn: "error" }).extract(rect).toBuffer() });
    }
    return result;
  }
  if (operation.cuts !== undefined) {
    if (!Array.isArray(operation.cuts)) throw new VisualAssetsError("INVALID_SPLIT_CUTS", "split.cuts must be an array");
    const mode = String(operation.mode ?? operation.space ?? operation.unit ?? "pixel");
    if (mode !== "pixel" && mode !== "normalized") throw new VisualAssetsError("INVALID_COORDINATE_SPACE", "split.cuts space must be pixel or normalized", { mode });
    const cuts = operation.cuts.map((cut, index) => {
      const raw = cut && typeof cut === "object" ? (cut as Record<string, unknown>).y : cut;
      const number = finiteNumber(raw, `split.cuts[${index}]`);
      const value = mode === "normalized" ? Math.round(number * height) : Math.round(number);
      if (value <= 0 || value >= height) throw new VisualAssetsError("COORDINATE_OUT_OF_BOUNDS", "split cuts must be strictly inside the image", { index, value, height });
      return value;
    }).sort((a, b) => a - b);
    if (new Set(cuts).size !== cuts.length) throw new VisualAssetsError("INVALID_SPLIT_CUTS", "split cuts must be unique");
    const boundaries = [0, ...cuts, height];
    return Promise.all(boundaries.slice(0, -1).map(async (start, index) => {
      const rect: ResolvedRect = { left: 0, top: start, width, height: boundaries[index + 1] - start };
      return { rect, buffer: await sharp(buffer, { failOn: "error" }).extract(rect).toBuffer() };
    }));
  }
  const rawMaximum = operation.maxPanelHeight ?? operation.maxHeight ?? operation.height ?? 2048;
  const maximum = Math.round(positiveNumber(rawMaximum, "split.maxPanelHeight"));
  const overlap = Math.round(operation.overlap === undefined ? 0 : finiteNumber(operation.overlap, "split.overlap"));
  if (overlap < 0 || overlap >= maximum) throw new VisualAssetsError("INVALID_SPLIT_OVERLAP", "split.overlap must be >= 0 and less than maxPanelHeight", { overlap, maximum });
  const result: Array<{ buffer: Buffer; rect: ResolvedRect }> = [];
  let start = 0;
  while (start < height) {
    const end = Math.min(height, start + maximum);
    const rect: ResolvedRect = { left: 0, top: start, width, height: end - start };
    result.push({
      rect,
      buffer: await sharp(buffer, { failOn: "error" }).extract(rect).toBuffer(),
    });
    if (end === height) break;
    let next = end - overlap;
    // Keep a final full-height panel whenever the regular stride would leave
    // a tiny tail. This also guarantees progress for every legal overlap.
    if (next + maximum > height) next = height - maximum;
    start = next <= start ? end : next;
  }
  return result;
}
