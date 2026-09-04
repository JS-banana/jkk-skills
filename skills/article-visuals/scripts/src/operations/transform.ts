import { basename, dirname, extname, join, parse, resolve } from "node:path";
import sharp from "sharp";
import { atomicWriteImage, assertOutputIsSafe, ensureFile, imageExtension, relativePath, sha256Buffer, sha256File } from "../core/fs.js";
import { VisualAssetsError, assertCondition } from "../core/errors.js";
import { manifestIssues, parseRecipe } from "../core/schemas.js";
import type { ImageDimensions, ImageOutputRecord, Manifest, ManifestAsset, ManifestOutput, OperationSpec, OutputSpec, Recipe, TransformResult } from "../core/types.js";
import { applyAnnotate } from "./annotate.js";
import { applyCrop, applyPad, applyResize, applyTrim, splitVertical } from "./geometry.js";

const DEFAULT_MAX_PIXELS = 50_000_000;

export interface TransformOptions {
  recipePath: string;
  inputOverride?: string;
  outputOverride?: string;
  manifestPath?: string;
}

async function orientedImage(input: string): Promise<{ buffer: Buffer; size: ImageDimensions }> {
  await ensureFile(input);
  try {
    const buffer = await sharp(input, { failOn: "error", limitInputPixels: DEFAULT_MAX_PIXELS }).rotate().toBuffer();
    const metadata = await sharp(buffer, { failOn: "error", limitInputPixels: DEFAULT_MAX_PIXELS }).metadata();
    const width = metadata.width ?? 0;
    const height = metadata.height ?? 0;
    if (!width || !height || width * height > DEFAULT_MAX_PIXELS) {
      throw new VisualAssetsError("PIXEL_LIMIT_EXCEEDED", "Image exceeds the pixel safety limit", { width, height, maxPixels: DEFAULT_MAX_PIXELS });
    }
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

async function dimensions(buffer: Buffer): Promise<ImageDimensions> {
  const metadata = await sharp(buffer, { failOn: "error", limitInputPixels: DEFAULT_MAX_PIXELS }).metadata();
  const width = metadata.width ?? 0;
  const height = metadata.height ?? 0;
  if (!width || !height) throw new VisualAssetsError("INVALID_IMAGE_DIMENSIONS", "Image has no usable dimensions");
  if (width * height > DEFAULT_MAX_PIXELS) throw new VisualAssetsError("PIXEL_LIMIT_EXCEEDED", "Image exceeds the pixel safety limit", { width, height });
  return { width, height };
}

async function applyOperation(buffer: Buffer, operation: OperationSpec): Promise<Buffer> {
  switch (String(operation.op).toLowerCase()) {
    case "crop": return applyCrop(buffer, operation);
    case "trim": return applyTrim(buffer, operation);
    case "resize": return applyResize(buffer, operation);
    case "pad": return applyPad(buffer, operation);
    case "annotate": return applyAnnotate(buffer, operation);
    case "split": throw new VisualAssetsError("SPLIT_NOT_SINGLE_OUTPUT", "split is a fan-out operation and must be the final recipe operation");
    default: throw new VisualAssetsError("UNSUPPORTED_OPERATION", `Unsupported recipe operation: ${operation.op}`, { operation: operation.op });
  }
}

function outputSpecList(recipe: Recipe, outputOverride: string | undefined, split: boolean): Array<string | OutputSpec> {
  if (outputOverride) return [outputOverride];
  if (recipe.output) return [recipe.output];
  if (recipe.outputs && recipe.outputs.length > 0) return recipe.outputs;
  if (split) throw new VisualAssetsError("OUTPUT_REQUIRED", "transform requires recipe.output, recipe.outputs, or --output");
  throw new VisualAssetsError("OUTPUT_REQUIRED", "transform requires an output path");
}

function formatPattern(pattern: string, outputIndex: number, total: number, inputPath: string): string {
  const input = parse(inputPath);
  const padded = String(outputIndex + 1).padStart(Math.max(2, String(total).length), "0");
  return pattern
    .replaceAll("{index}", padded)
    .replaceAll("{n}", String(outputIndex + 1))
    .replaceAll("{name}", input.name)
    .replaceAll("{ext}", input.ext || ".png");
}

function resolveOutputPaths(specs: Array<string | OutputSpec>, split: boolean, inputPath: string, count: number, baseDirectory: string): string[] {
  if (!split) {
    const first = specs[0];
    const output = typeof first === "string" ? first : first.path;
    if (!output) throw new VisualAssetsError("OUTPUT_PATH_REQUIRED", "A non-split output requires output.path");
    return [resolve(baseDirectory, output)];
  }
  if (specs.length > 1) {
    if (specs.length !== count) {
      throw new VisualAssetsError("OUTPUT_COUNT_MISMATCH", "recipe.outputs must contain exactly one path per split panel", { expected: count, actual: specs.length });
    }
    return specs.map((spec, index) => {
      const output = typeof spec === "string" ? spec : spec.path;
      if (!output) throw new VisualAssetsError("OUTPUT_PATH_REQUIRED", `recipe.outputs[${index}] requires a path`);
      return resolve(baseDirectory, output);
    });
  }
  const first = specs[0];
  const base = typeof first === "string" ? { path: first } : first;
  const dir = resolve(baseDirectory, base.dir ?? (base.path ? dirname(base.path) : "."));
  const defaultName = base.path ? basename(base.path) : `${parse(inputPath).name}-panel-{index}.png`;
  const defaultPattern = base.pattern ?? (base.path ? `${parse(defaultName).name}-{index}${extname(defaultName) || ".png"}` : defaultName);
  return Array.from({ length: count }, (_, index) => join(dir, formatPattern(defaultPattern, index, count, inputPath)));
}

async function writeImage(buffer: Buffer, output: string, input: string): Promise<ImageOutputRecord> {
  await assertOutputIsSafe(input, output);
  imageExtension(output);
  await atomicWriteImage(output, async (temporary) => {
    await sharp(buffer, { failOn: "error", limitInputPixels: DEFAULT_MAX_PIXELS }).toFile(temporary);
  });
  const outputBuffer = await import("node:fs/promises").then((fs) => fs.readFile(output));
  const size = await dimensions(outputBuffer);
  const info = await import("node:fs/promises").then((fs) => fs.stat(output));
  return { path: resolve(output), ...size, sha256: sha256Buffer(outputBuffer), bytes: info.size };
}

function makeAssetRecord(recipe: Recipe, input: string, sourceSha256: string, originalSize: ImageDimensions, outputs: ImageOutputRecord[], manifestPath?: string): ManifestAsset {
  const id = String(recipe.assetId ?? recipe.id ?? parse(input).name);
  const manifestBase = manifestPath ?? resolve(join(process.cwd(), "manifest.json"));
  const manifestOutputs: ManifestOutput[] = outputs.map((output) => ({
    path: relativePath(manifestBase, output.path),
    width: output.width,
    height: output.height,
    sha256: output.sha256,
    bytes: output.bytes,
  }));
  return {
    id,
    purpose: String(recipe.purpose ?? "article-asset"),
    source: relativePath(manifestBase, input),
    sourceSha256,
    originalSize,
    recipe,
    outputs: manifestOutputs,
    status: "produced",
    approval: "unreviewed",
  };
}

export async function transformRecipe(value: unknown, options: TransformOptions): Promise<TransformResult> {
  const recipe = parseRecipe(value);
  const recipeDir = dirname(resolve(options.recipePath));
  const manifest = options.manifestPath ? await loadManifestForUpdate(options.manifestPath) : undefined;
  // path.resolve processes arguments right-to-left; keep the recipe directory
  // first so a relative recipe input is resolved against the recipe file.
  const input = resolve(recipeDir, options.inputOverride ?? recipe.input);
  const sourceSha256 = await sha256File(input);
  const loaded = await orientedImage(input);
  let current = loaded.buffer;
  let splitBuffers: Buffer[] | undefined;
  const operations = recipe.operations;
  for (let index = 0; index < operations.length; index += 1) {
    const operation = operations[index];
    const op = String(operation.op).toLowerCase();
    if (op === "split") {
      if (index !== operations.length - 1) throw new VisualAssetsError("SPLIT_MUST_BE_FINAL", "split is a fan-out endpoint and must be the final operation", { index });
      const panels = await splitVertical(current, operation);
      splitBuffers = panels.map((panel) => panel.buffer);
    } else {
      current = await applyOperation(current, operation);
      const size = await dimensions(current);
      assertCondition(size.width * size.height <= DEFAULT_MAX_PIXELS, "PIXEL_LIMIT_EXCEEDED", "Recipe output exceeds the pixel safety limit", { ...size });
    }
  }
  const split = splitBuffers !== undefined;
  const buffers: Buffer[] = splitBuffers ?? [current];
  const specs = outputSpecList(recipe, options.outputOverride, split);
  const outputs = resolveOutputPaths(specs, split, input, buffers.length, recipeDir);
  if (new Set(outputs).size !== outputs.length) {
    throw new VisualAssetsError("DUPLICATE_OUTPUT_PATH", "Every split panel requires a unique output path", { outputs });
  }
  // Validate every destination before the first rename so a bad fan-out path
  // cannot leave an earlier panel written while the recipe is failing.
  for (const output of outputs) {
    await assertOutputIsSafe(input, output);
    imageExtension(output);
  }
  const records: ImageOutputRecord[] = [];
  for (let index = 0; index < buffers.length; index += 1) {
    const record = await writeImage(buffers[index], outputs[index], input);
    records.push({ ...record, ...(split ? { index } : {}) });
  }
  const asset = makeAssetRecord(recipe, input, sourceSha256, loaded.size, records, options.manifestPath);
  if (options.manifestPath && manifest) await updateManifest(options.manifestPath, manifest, asset);
  return {
    ok: true,
    command: "transform",
    input,
    sourceSha256,
    originalSize: loaded.size,
    recipe,
    outputs: records,
    asset,
  };
}

async function loadManifestForUpdate(path: string): Promise<Manifest> {
  const manifestPath = resolve(path);
  let raw: unknown;
  try {
    raw = await import("../core/fs.js").then((module) => module.readJson(manifestPath));
  } catch (error) {
    if (error instanceof VisualAssetsError && ["JSON_NOT_FOUND", "INPUT_NOT_FOUND"].includes(error.code)) {
      throw new VisualAssetsError("MANIFEST_NOT_INITIALIZED", "Initialize the manifest before using transform --manifest", { path: manifestPath });
    }
    throw error;
  }
  const issues = manifestIssues(raw);
  if (issues.length > 0) throw new VisualAssetsError("MANIFEST_SCHEMA_INVALID", "Manifest does not match schema v1", { path: manifestPath, issues });
  return raw as Manifest;
}

async function updateManifest(path: string, manifest: Manifest, asset: ManifestAsset): Promise<void> {
  const manifestPath = resolve(path);
  const existing = manifest.assets.findIndex((candidate) => candidate.id === asset.id);
  if (existing >= 0) manifest.assets[existing] = asset;
  else manifest.assets.push(asset);
  const { atomicWriteFile } = await import("../core/fs.js");
  await atomicWriteFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
}
