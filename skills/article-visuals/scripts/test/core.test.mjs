import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdir, mkdtemp, readFile, unlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { promisify } from "node:util";
import { test } from "node:test";
import sharp from "sharp";

const exec = promisify(execFile);
const root = resolve(dirname(new URL(import.meta.url).pathname), "..");
const cli = join(root, "dist", "cli.js");

async function runCli(cwd, args, expectedCode = 0) {
  try {
    const result = await exec(process.execPath, [cli, ...args], { cwd, maxBuffer: 4 * 1024 * 1024 });
    assert.equal(expectedCode, 0);
    let json;
    try { json = result.stdout.trim() ? JSON.parse(result.stdout) : undefined; } catch { /* preview without --output is HTML */ }
    return { ...result, json };
  } catch (error) {
    assert.equal(error.code, expectedCode, `unexpected exit code; stdout=${error.stdout}; stderr=${error.stderr}`);
    let json;
    try { json = JSON.parse((error.stdout || error.stderr || "").trim()); } catch { /* human output is not expected for failures */ }
    return { ...error, json };
  }
}

async function fixture() {
  const directory = await mkdtemp(join(tmpdir(), "visual-assets-test-"));
  const source = join(directory, "source.png");
  const svg = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="120" height="240"><rect width="120" height="240" fill="white"/><rect x="20" y="60" width="80" height="120" fill="#0ea5e9"/><rect x="0" y="0" width="120" height="20" fill="#111827"/></svg>`);
  await sharp(svg).png().toFile(source);
  return { directory, source };
}

async function recipe(directory, name, value) {
  await mkdir(directory, { recursive: true });
  const path = join(directory, `${name}.json`);
  await writeFile(path, JSON.stringify(value, null, 2));
  return path;
}

test("capabilities and inspect expose stable machine-readable contracts", async () => {
  const { directory, source } = await fixture();
  const capabilities = await runCli(directory, ["capabilities", "--json"]);
  assert.equal(capabilities.json.ok, true);
  assert.equal(capabilities.json.engine.image, "sharp/libvips");
  assert.equal(capabilities.json.commands.transform.usage.startsWith("transform"), true);
  const inspected = await runCli(directory, ["inspect", "--input", source, "--json"]);
  assert.deepEqual({ width: inspected.json.width, height: inspected.json.height }, { width: 120, height: 240 });
  assert.match(inspected.json.sha256, /^[a-f0-9]{64}$/);
});

test("crop, resize without enlargement, pad and recipe replay are deterministic", async () => {
  const { directory, source } = await fixture();
  const recipes = join(directory, "recipes");
  const cropRecipe = await recipe(recipes, "crop", { version: 1, input: "../source.png", output: "../crop.png", operations: [{ op: "crop", normalized: { x: 0, y: 0.25, width: 1, height: 0.5 } }] });
  const crop = await runCli(recipes, ["transform", "--recipe", cropRecipe, "--json"]);
  assert.deepEqual({ width: crop.json.outputs[0].width, height: crop.json.outputs[0].height }, { width: 120, height: 120 });
  const resizeRecipe = await recipe(directory, "resize", { version: 1, input: "source.png", output: "small.png", operations: [{ op: "resize", width: 300 }] });
  const resized = await runCli(directory, ["transform", "--recipe", resizeRecipe, "--json"]);
  assert.equal(resized.json.outputs[0].width, 120, "default resize must not upscale");
  const padRecipe = await recipe(directory, "pad", { version: 1, input: "source.png", output: "square.png", operations: [{ op: "pad", aspectRatio: "1:1", background: "#ffffff" }] });
  const padded = await runCli(directory, ["transform", "--recipe", padRecipe, "--json"]);
  assert.deepEqual({ width: padded.json.outputs[0].width, height: padded.json.outputs[0].height }, { width: 240, height: 240 });
  const replay = await runCli(directory, ["transform", "--recipe", cropRecipe, "--output", join(directory, "crop-replay.png"), "--json"]);
  assert.equal(replay.json.outputs[0].sha256, crop.json.outputs[0].sha256);
});

test("trim, split overlap and annotation operations produce valid images", async () => {
  const { directory } = await fixture();
  const trimSource = join(directory, "trim-source.png");
  const inner = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"><rect width="20" height="20" fill="#ef4444"/></svg>`);
  await sharp({ create: { width: 60, height: 60, channels: 4, background: "#ffffff" } }).composite([{ input: inner, left: 20, top: 20 }]).png().toFile(trimSource);
  const trimRecipe = await recipe(directory, "trim", { version: 1, input: "trim-source.png", output: "trim.png", operations: [{ op: "trim", background: "#ffffff" }] });
  const trimmed = await runCli(directory, ["transform", "--recipe", trimRecipe, "--json"]);
  assert.deepEqual({ width: trimmed.json.outputs[0].width, height: trimmed.json.outputs[0].height }, { width: 20, height: 20 });
  const splitRecipe = await recipe(directory, "split", { version: 1, input: "source.png", output: "panel.png", operations: [{ op: "split", maxPanelHeight: 100, overlap: 10 }] });
  const split = await runCli(directory, ["transform", "--recipe", splitRecipe, "--json"]);
  assert.equal(split.json.outputs.length, 3);
  assert.deepEqual(split.json.outputs.map((output) => output.height), [100, 100, 100]);
  assert.match(split.json.outputs[1].path, /panel-02\.png$/);
  const semanticSplitRecipe = await recipe(directory, "semantic-split", { version: 1, input: "source.png", output: "semantic.png", operations: [{ op: "split", segments: [{ y: 0, height: 0.25, mode: "normalized" }, { y: 0.2, height: 0.5, mode: "normalized" }, { y: 0.7, height: 0.3, mode: "normalized" }] }] });
  const semanticSplit = await runCli(directory, ["transform", "--recipe", semanticSplitRecipe, "--json"]);
  assert.deepEqual(semanticSplit.json.outputs.map((output) => output.height), [60, 120, 72]);
  const annotationRecipe = await recipe(directory, "annotation", { version: 1, input: "source.png", output: "annotation.png", operations: [{ op: "annotate", annotations: [{ type: "box", normalized: { x: 0.1, y: 0.1, width: 0.3, height: 0.2 } }, { type: "arrow", from: { x: 0, y: 0, mode: "normalized" }, to: { x: 0.5, y: 0.5, mode: "normalized" } }, { type: "number", normalized: { x: 0.1, y: 0.1, width: 0.2, height: 0.2 }, value: 1 }, { type: "blur", normalized: { x: 0.5, y: 0.5, width: 0.2, height: 0.2 } }, { type: "redact", normalized: { x: 0.7, y: 0.7, width: 0.1, height: 0.1 } }, { type: "zoom-inset", normalized: { x: 0, y: 0, width: 0.2, height: 0.2 } }] }] });
  const annotated = await runCli(directory, ["transform", "--recipe", annotationRecipe, "--json"]);
  assert.deepEqual({ width: annotated.json.outputs[0].width, height: annotated.json.outputs[0].height }, { width: 120, height: 240 });
  const board = await runCli(directory, ["analysis-board", "--input", sourcePath(directory), "--output", join(directory, "board.png")]);
  assert.equal(board.json.command, "analysis-board");
});

function sourcePath(directory) { return join(directory, "source.png"); }

test("corrupt files, coordinate bounds and overwrite attempts fail with stable JSON errors", async () => {
  const { directory, source } = await fixture();
  const corrupt = join(directory, "corrupt.png");
  await writeFile(corrupt, "not an image");
  const corruptResult = await runCli(directory, ["inspect", "--input", corrupt, "--json"], 1);
  assert.equal(corruptResult.json.error.code, "IMAGE_DECODE_FAILED");
  const badRecipe = await recipe(directory, "bad", { version: 1, input: "source.png", output: "bad.png", operations: [{ op: "crop", normalized: { x: 0.9, y: 0, width: 0.5, height: 0.5 } }] });
  const bad = await runCli(directory, ["transform", "--recipe", badRecipe, "--json"], 1);
  assert.equal(bad.json.error.code, "COORDINATE_OUT_OF_BOUNDS");
  const overwriteRecipe = await recipe(directory, "overwrite", { version: 1, input: "source.png", output: "source.png", operations: [{ op: "trim" }] });
  const overwrite = await runCli(directory, ["transform", "--recipe", overwriteRecipe, "--json"], 1);
  assert.equal(overwrite.json.error.code, "OUTPUT_EQUALS_INPUT");
  const badBoard = await runCli(directory, ["analysis-board", "--input", source, "--output", join(directory, "board.jpg")], 1);
  assert.equal(badBoard.json.error.code, "ANALYSIS_BOARD_FORMAT");
  const badPad = await recipe(directory, "bad-pad-position", { version: 1, input: "source.png", output: "bad-pad.png", operations: [{ op: "pad", width: 200, height: 300, position: { x: "left" } }] });
  const badPadResult = await runCli(directory, ["transform", "--recipe", badPad, "--json"], 1);
  assert.equal(badPadResult.json.error.code, "INVALID_COORDINATE");
});

test("split outputs are explicit and collision-safe", async () => {
  const { directory } = await fixture();
  const explicit = await recipe(directory, "explicit-split", { version: 1, input: "source.png", outputs: ["first.png", "second.png"], operations: [{ op: "split", cuts: [120] }] });
  const result = await runCli(directory, ["transform", "--recipe", explicit, "--json"]);
  assert.deepEqual(result.json.outputs.map((output) => output.path), [join(directory, "first.png"), join(directory, "second.png")]);
  const mismatch = await recipe(directory, "mismatch-split", { version: 1, input: "source.png", outputs: ["only.png", "extra.png", "third.png"], operations: [{ op: "split", cuts: [120] }] });
  const mismatchResult = await runCli(directory, ["transform", "--recipe", mismatch, "--json"], 1);
  assert.equal(mismatchResult.json.error.code, "OUTPUT_COUNT_MISMATCH");
  const collision = await recipe(directory, "collision-split", { version: 1, input: "source.png", output: { dir: ".", pattern: "same.png" }, operations: [{ op: "split", cuts: [120] }] });
  const collisionResult = await runCli(directory, ["transform", "--recipe", collision, "--json"], 1);
  assert.equal(collisionResult.json.error.code, "DUPLICATE_OUTPUT_PATH");
});

test("unicode paths, transparency, JPEG/WebP, EXIF orientation and pixel limits", async () => {
  const { directory } = await fixture();
  const unicodeDirectory = join(directory, "中文 资产");
  await mkdir(unicodeDirectory, { recursive: true });
  const orientedJpeg = join(unicodeDirectory, "旋转.jpg");
  await sharp({ create: { width: 40, height: 20, channels: 3, background: "#22c55e" } }).jpeg().withMetadata({ orientation: 6 }).toFile(orientedJpeg);
  const oriented = await runCli(directory, ["inspect", "--input", orientedJpeg, "--json"]);
  assert.deepEqual({ width: oriented.json.width, height: oriented.json.height }, { width: 20, height: 40 });
  const webpRecipe = await recipe(directory, "webp", { version: 1, input: "中文 资产/旋转.jpg", output: "中文 资产/输出.webp", operations: [{ op: "resize", width: 18 }] });
  const webp = await runCli(directory, ["transform", "--recipe", webpRecipe, "--json"]);
  assert.equal((await sharp(webp.json.outputs[0].path).metadata()).format, "webp");
  const jpegRecipe = await recipe(directory, "jpeg", { version: 1, input: "中文 资产/输出.webp", output: "中文 资产/再输出.jpeg", operations: [{ op: "resize", width: 16 }] });
  const jpeg = await runCli(directory, ["transform", "--recipe", jpegRecipe, "--json"]);
  assert.equal((await sharp(jpeg.json.outputs[0].path).metadata()).format, "jpeg");
  const transparent = join(unicodeDirectory, "透明.png");
  await sharp({ create: { width: 24, height: 24, channels: 4, background: { r: 0, g: 0, b: 0, alpha: 0 } } }).png().toFile(transparent);
  const transparentRecipe = await recipe(directory, "transparent", { version: 1, input: "中文 资产/透明.png", output: "中文 资产/透明输出.png", operations: [{ op: "pad", width: 30, height: 30, background: { r: 255, g: 255, b: 255, alpha: 0 } }] });
  const transparentOutput = await runCli(directory, ["transform", "--recipe", transparentRecipe, "--json"]);
  assert.equal((await sharp(transparentOutput.json.outputs[0].path).metadata()).hasAlpha, true);
  const huge = join(directory, "too-many-pixels.png");
  await sharp({ create: { width: 10001, height: 5000, channels: 3, background: "#000000" } }).png().toFile(huge);
  const tooLarge = await runCli(directory, ["inspect", "--input", huge, "--json"], 1);
  assert.equal(tooLarge.json.error.code, "PIXEL_LIMIT_EXCEEDED");
});

test("failed replay leaves an existing output unchanged", async () => {
  const { directory } = await fixture();
  const good = await recipe(directory, "good-output", { version: 1, input: "source.png", output: "stable.png", operations: [{ op: "resize", width: 60 }] });
  const first = await runCli(directory, ["transform", "--recipe", good, "--json"]);
  const originalHash = first.json.outputs[0].sha256;
  const bad = await recipe(directory, "bad-existing-output", { version: 1, input: "source.png", output: "stable.png", operations: [{ op: "crop", normalized: { x: 0.8, y: 0, width: 0.5, height: 0.5 } }] });
  const failed = await runCli(directory, ["transform", "--recipe", bad, "--json"], 1);
  assert.equal(failed.json.error.code, "COORDINATE_OUT_OF_BOUNDS");
  const after = await runCli(directory, ["inspect", "--input", join(directory, "stable.png"), "--json"]);
  assert.equal(after.json.sha256, originalHash);
});

test("manifest update, validation profiles/final approval and self-contained preview", async () => {
  const { directory, source } = await fixture();
  const manifest = join(directory, "manifest.json");
  const article = join(directory, "article.md");
  await writeFile(article, "# Fixture article\n");
  const initialized = await runCli(directory, ["init", "--manifest", manifest, "--article", article, "--version", "v1", "--json"]);
  assert.equal(initialized.json.article.version, "v1");
  const transformRecipe = await recipe(directory, "manifest-recipe", { version: 1, assetId: "hero", purpose: "hero image", input: "source.png", output: "hero.png", operations: [{ op: "resize", width: 100 }] });
  const transformed = await runCli(directory, ["transform", "--recipe", transformRecipe, "--manifest", manifest, "--json"]);
  assert.equal(transformed.json.asset.status, "produced");
  assert.equal(transformed.json.asset.approval, "unreviewed");
  const valid = await runCli(directory, ["validate", "--manifest", manifest, "--profile", "wechat", "--json"]);
  assert.equal(valid.json.ok, true);
  const highResRecipe = await recipe(directory, "high-res", { version: 1, assetId: "high-res", purpose: "high resolution", input: "source.png", output: "high-res.png", operations: [{ op: "resize", width: 2000, allowEnlarge: true }] });
  await runCli(directory, ["transform", "--recipe", highResRecipe, "--manifest", manifest, "--json"]);
  const highResProfile = await runCli(directory, ["validate", "--manifest", manifest, "--profile", "wechat", "--json"]);
  assert.equal(highResProfile.json.ok, true);
  assert.equal(highResProfile.json.errors.some((error) => error.code === "PROFILE_WIDTH_EXCEEDED"), false);
  assert.equal(highResProfile.json.profileChecks.find((check) => check.asset === "high-res").display.width, 677);
  const finalBlocked = await runCli(directory, ["validate", "--manifest", manifest, "--final", "--json"], 1);
  assert.equal(finalBlocked.json.errors[0].code, "ASSET_NOT_REVIEWED");
  const reviewed = await runCli(directory, ["review", "--manifest", manifest, "--approve", "hero,high-res", "--json"]);
  assert.deepEqual(reviewed.json.assets, ["hero", "high-res"]);
  const reviewedManifest = JSON.parse(await readFile(manifest, "utf8"));
  assert.equal(reviewedManifest.assets.find((asset) => asset.id === "hero").status, "produced");
  assert.equal(reviewedManifest.assets.find((asset) => asset.id === "hero").approval, "approved");
  const finalValid = await runCli(directory, ["validate", "--manifest", manifest, "--final", "--json"]);
  assert.equal(finalValid.json.ok, true);
  const preview = await runCli(directory, ["preview", "--manifest", manifest]);
  assert.match(preview.stdout, /data:image\/webp;base64,/);
  assert.match(preview.stdout, /375px/);
  assert.match(preview.stdout, /class="viewports"/);
  assert.match(preview.stdout, /WeChat content/);
  const rejectedRecipe = await recipe(directory, "rejected-recipe", { version: 1, assetId: "alternative", purpose: "unused alternative", input: "source.png", output: "alternative.png", operations: [{ op: "resize", width: 90 }] });
  await runCli(directory, ["transform", "--recipe", rejectedRecipe, "--manifest", manifest, "--json"]);
  await runCli(directory, ["review", "--manifest", manifest, "--reject", "alternative", "--json"]);
  await unlink(join(directory, "alternative.png"));
  const finalWithRejectedAlternative = await runCli(directory, ["validate", "--manifest", manifest, "--final", "--json"]);
  assert.equal(finalWithRejectedAlternative.json.ok, true);
  const plan = join(directory, "visual-plan.json");
  const planValue = {
    version: 1,
    article: { path: "article.md", version: "v1" },
    channels: ["wechat", "desktop"],
    items: [
      { id: "hero", position: "after:intro", function: "evidence", serves: "Show the fixture source", altText: "Blue fixture block", preferredRoute: "local-source", alternatives: [], evidenceIds: ["E-fixture"], status: "approved" },
      { id: "high-res", position: "after:details", function: "explanation", serves: "Show the high-resolution rendering", altText: "High-resolution fixture block", preferredRoute: "local-source", alternatives: [], status: "approved" },
      { id: "alternative", position: "after:details", function: "explanation", serves: "Unused alternative", altText: "Rejected fixture alternative", preferredRoute: "local-source", alternatives: [], status: "rejected" },
    ],
  };
  await writeFile(plan, JSON.stringify(planValue, null, 2));
  const finalWithPlan = await runCli(directory, ["validate", "--manifest", manifest, "--plan", plan, "--profile", "wechat", "--final", "--json"]);
  assert.equal(finalWithPlan.json.ok, true);
  const previewWithPlan = await runCli(directory, ["preview", "--manifest", manifest, "--plan", plan]);
  assert.match(previewWithPlan.stdout, /Position/);
  assert.match(previewWithPlan.stdout, /Show the fixture source/);
  await writeFile(article, "# Fixture article\n\nVersion two.\n");
  const rebased = await runCli(directory, ["rebase", "--manifest", manifest, "--plan", plan, "--article", article, "--version", "v2", "--json"]);
  assert.deepEqual(rebased.json.resetAssets.sort(), ["hero", "high-res"]);
  const rebasedPlan = JSON.parse(await readFile(plan, "utf8"));
  assert.equal(rebasedPlan.article.version, "v2");
  assert.equal(rebasedPlan.items.find((item) => item.id === "hero").status, "candidate");
  assert.equal(rebasedPlan.items.find((item) => item.id === "alternative").status, "rejected");
  const rebasedBlocked = await runCli(directory, ["validate", "--manifest", manifest, "--plan", plan, "--final", "--json"], 1);
  assert.equal(rebasedBlocked.json.errors.some((error) => error.code === "ASSET_NOT_REVIEWED"), true);
  await runCli(directory, ["review", "--manifest", manifest, "--plan", plan, "--approve", "hero,high-res", "--json"]);
  const finalAfterRebaseReview = await runCli(directory, ["validate", "--manifest", manifest, "--plan", plan, "--final", "--json"]);
  assert.equal(finalAfterRebaseReview.json.ok, true);
  const reviewedPlan = JSON.parse(await readFile(plan, "utf8"));
  assert.equal(reviewedPlan.items.find((item) => item.id === "hero").status, "approved");
  const invalidPlan = structuredClone(planValue);
  invalidPlan.article.version = "v2";
  delete invalidPlan.items[0].altText;
  await writeFile(plan, JSON.stringify(invalidPlan, null, 2));
  const invalidPlanResult = await runCli(directory, ["validate", "--manifest", manifest, "--plan", plan, "--final", "--json"], 1);
  assert.equal(invalidPlanResult.json.errors[0].code, "VISUAL_PLAN_SCHEMA_INVALID");
});
