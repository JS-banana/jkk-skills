import { readFile, stat } from "node:fs/promises";
import sharp from "sharp";
import { ensureFile, sha256File, DEFAULT_MAX_PIXELS } from "./fs.js";
import { VisualAssetsError } from "./errors.js";
import type { ImageDimensions, InspectResult } from "./types.js";

export async function readOrientedImage(input: string): Promise<{ buffer: Buffer; size: ImageDimensions }> {
  await ensureFile(input);
  try {
    const buffer = await sharp(input, { failOn: "error", limitInputPixels: DEFAULT_MAX_PIXELS }).rotate().toBuffer();
    const metadata = await sharp(buffer, { failOn: "error", limitInputPixels: DEFAULT_MAX_PIXELS }).metadata();
    const width = metadata.width ?? 0;
    const height = metadata.height ?? 0;
    if (!width || !height || width * height > DEFAULT_MAX_PIXELS) throw new VisualAssetsError("PIXEL_LIMIT_EXCEEDED", "Image exceeds the pixel safety limit", { width, height, maxPixels: DEFAULT_MAX_PIXELS });
    return { buffer, size: { width, height } };
  } catch (error) {
    if (error instanceof VisualAssetsError) throw error;
    const message = error instanceof Error ? error.message : String(error);
    if (/pixel limit|too many pixels|exceeds.*pixel/i.test(message)) {
      throw new VisualAssetsError("PIXEL_LIMIT_EXCEEDED", "Image exceeds the pixel safety limit", { path: input, cause: message, maxPixels: DEFAULT_MAX_PIXELS });
    }
    throw new VisualAssetsError("IMAGE_DECODE_FAILED", `Unable to decode image: ${input}`, {
      path: input,
      cause: message,
    });
  }
}

export async function inspectImage(input: string): Promise<InspectResult> {
  await ensureFile(input);
  try {
    const [raw, oriented, info, sourceSha256] = await Promise.all([
      sharp(input, { failOn: "error", limitInputPixels: DEFAULT_MAX_PIXELS }).metadata(),
      readOrientedImage(input),
      stat(input),
      sha256File(input),
    ]);
    return {
      ok: true,
      command: "inspect",
      input,
      sha256: sourceSha256,
      bytes: info.size,
      format: raw.format,
      width: oriented.size.width,
      height: oriented.size.height,
      rawWidth: raw.width,
      rawHeight: raw.height,
      space: raw.space,
      channels: raw.channels,
      hasAlpha: raw.hasAlpha,
      density: raw.density,
      orientation: raw.orientation,
      isAnimated: raw.pages !== undefined && raw.pages > 1,
      pages: raw.pages,
      pageHeight: raw.pageHeight,
    };
  } catch (error) {
    if (error instanceof VisualAssetsError) throw error;
    const message = error instanceof Error ? error.message : String(error);
    if (/pixel limit|too many pixels|exceeds.*pixel/i.test(message)) {
      throw new VisualAssetsError("PIXEL_LIMIT_EXCEEDED", "Image exceeds the pixel safety limit", { path: input, cause: message, maxPixels: DEFAULT_MAX_PIXELS });
    }
    throw new VisualAssetsError("IMAGE_DECODE_FAILED", `Unable to inspect image: ${input}`, {
      path: input,
      cause: message,
    });
  }
}

export async function readBuffer(path: string): Promise<Buffer> {
  await ensureFile(path);
  try {
    return await readFile(path);
  } catch (error) {
    throw new VisualAssetsError("INPUT_READ_FAILED", `Unable to read image: ${path}`, {
      path,
      cause: error instanceof Error ? error.message : String(error),
    });
  }
}
