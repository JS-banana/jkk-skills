import { createHash, randomBytes } from "node:crypto";
import { mkdir, readFile, rename, rm, stat, writeFile } from "node:fs/promises";
import { dirname, extname, isAbsolute, relative, resolve, sep } from "node:path";
import { VisualAssetsError, assertCondition } from "./errors.js";

export const DEFAULT_MAX_PIXELS = 50_000_000;

export function resolvePath(value: string, base = process.cwd()): string {
  return isAbsolute(value) ? resolve(value) : resolve(base, value);
}

export async function ensureFile(path: string, code = "INPUT_NOT_FOUND"): Promise<void> {
  try {
    const info = await stat(path);
    if (!info.isFile()) throw new Error("not a file");
  } catch {
    throw new VisualAssetsError(code, `File does not exist or is not a regular file: ${path}`, { path });
  }
}

export async function readJson(path: string): Promise<unknown> {
  await ensureFile(path, "JSON_NOT_FOUND");
  let text: string;
  try {
    text = await readFile(path, "utf8");
  } catch (error) {
    throw new VisualAssetsError("JSON_READ_FAILED", `Unable to read JSON file: ${path}`, {
      path,
      cause: error instanceof Error ? error.message : String(error),
    });
  }
  try {
    return JSON.parse(text) as unknown;
  } catch (error) {
    throw new VisualAssetsError("JSON_PARSE_FAILED", `Invalid JSON: ${path}`, {
      path,
      cause: error instanceof Error ? error.message : String(error),
    });
  }
}

export async function sha256File(path: string): Promise<string> {
  await ensureFile(path);
  const data = await readFile(path);
  return createHash("sha256").update(data).digest("hex");
}

export function sha256Buffer(data: Buffer): string {
  return createHash("sha256").update(data).digest("hex");
}

function tempName(destination: string): string {
  const extension = extname(destination) || ".tmp";
  const base = destination.slice(0, destination.length - extname(destination).length);
  return `${base}.tmp-${process.pid}-${Date.now()}-${randomBytes(5).toString("hex")}${extension}`;
}

async function atomicRename(tempPath: string, destination: string): Promise<void> {
  try {
    await rename(tempPath, destination);
  } catch (error) {
    // Windows can reject replacing an existing destination. The first rename
    // remains the normal atomic path; this fallback only replaces the output,
    // never the input, after the complete temporary file has been written.
    const code = (error as NodeJS.ErrnoException).code;
    if (code !== "EEXIST" && code !== "EPERM" && code !== "ENOTEMPTY") throw error;
    await rm(destination, { force: true });
    await rename(tempPath, destination);
  }
}

export async function atomicWriteFile(destination: string, data: string | Uint8Array): Promise<void> {
  const output = resolve(destination);
  await mkdir(dirname(output), { recursive: true });
  const temporary = tempName(output);
  try {
    await writeFile(temporary, data, { flag: "wx" });
    await atomicRename(temporary, output);
  } finally {
    await rm(temporary, { force: true }).catch(() => undefined);
  }
}

export async function atomicWriteImage(
  destination: string,
  writeImage: (temporary: string) => Promise<void>,
): Promise<void> {
  const output = resolve(destination);
  await mkdir(dirname(output), { recursive: true });
  const temporary = tempName(output);
  try {
    await writeImage(temporary);
    await atomicRename(temporary, output);
  } catch (error) {
    throw error instanceof VisualAssetsError
      ? error
      : new VisualAssetsError("OUTPUT_WRITE_FAILED", `Unable to write output: ${output}`, {
          path: output,
          cause: error instanceof Error ? error.message : String(error),
        });
  } finally {
    await rm(temporary, { force: true }).catch(() => undefined);
  }
}

export async function pathsReferToSameFile(first: string, second: string): Promise<boolean> {
  const a = resolve(first);
  const b = resolve(second);
  if (a === b) return true;
  try {
    const [realA, realB] = await Promise.all([
      import("node:fs/promises").then((fs) => fs.realpath(a)),
      import("node:fs/promises").then((fs) => fs.realpath(b)),
    ]);
    return realA === realB;
  } catch {
    return false;
  }
}

export async function assertOutputIsSafe(input: string, output: string): Promise<void> {
  if (await pathsReferToSameFile(input, output)) {
    throw new VisualAssetsError("OUTPUT_EQUALS_INPUT", "Output path must not overwrite the input image", {
      input: resolve(input),
      output: resolve(output),
    });
  }
}

export function relativePath(fromFile: string, target: string): string {
  const value = relative(dirname(resolve(fromFile)), resolve(target));
  return value.split(sep).join("/") || ".";
}

export function assertPixelBudget(width: number, height: number, maxPixels = DEFAULT_MAX_PIXELS): void {
  assertCondition(
    Number.isSafeInteger(width) && Number.isSafeInteger(height) && width > 0 && height > 0,
    "INVALID_IMAGE_DIMENSIONS",
    "Image dimensions must be positive safe integers",
    { width, height },
  );
  assertCondition(
    width * height <= maxPixels,
    "PIXEL_LIMIT_EXCEEDED",
    `Image exceeds the ${maxPixels.toLocaleString()} pixel safety limit`,
    { width, height, maxPixels },
  );
}

export function imageExtension(path: string): string {
  const extension = extname(path).toLowerCase();
  if (!extension) throw new VisualAssetsError("OUTPUT_EXTENSION_REQUIRED", "Image output must have a file extension", { path });
  const allowed = new Set([".png", ".jpg", ".jpeg", ".webp", ".avif", ".tif", ".tiff", ".gif"]);
  if (!allowed.has(extension)) {
    throw new VisualAssetsError("UNSUPPORTED_OUTPUT_FORMAT", `Unsupported image output extension: ${extension}`, { path });
  }
  return extension;
}
