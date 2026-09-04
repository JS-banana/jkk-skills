import { dirname, resolve } from "node:path";
import sharp from "sharp";
import { readJson, ensureFile, sha256File } from "./fs.js";
import { manifestIssues, visualPlanIssues } from "./schemas.js";
import type { Manifest, VisualPlan } from "./types.js";

export type ValidationProfile = "wechat" | "desktop";

export interface ValidationIssue {
  code: string;
  path: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface ManifestValidationResult {
  ok: boolean;
  command: "validate";
  manifest: string;
  plan?: string;
  profile?: ValidationProfile;
  final?: boolean;
  errors: ValidationIssue[];
  warnings: ValidationIssue[];
  assets: number;
  profileChecks?: Array<{ asset: string; output: string; native: { width: number; height: number }; viewportWidth: number; display: { width: number; height: number; scale: number } }>;
}

async function imageInfo(path: string): Promise<{ width: number; height: number }> {
  const metadata = await sharp(path, { failOn: "error" }).metadata();
  return { width: metadata.width ?? 0, height: metadata.height ?? 0 };
}

export async function validateManifest(path: string, profile?: ValidationProfile, final = false, visualPlanPath?: string): Promise<ManifestValidationResult> {
  const manifestPath = resolve(path);
  const planPath = visualPlanPath ? resolve(visualPlanPath) : undefined;
  const errors: ValidationIssue[] = [];
  const warnings: ValidationIssue[] = [];
  const profileChecks: NonNullable<ManifestValidationResult["profileChecks"]> = [];
  let raw: unknown;
  try {
    raw = await readJson(manifestPath);
  } catch (error) {
    return {
      ok: false,
      command: "validate",
      manifest: manifestPath,
      ...(planPath ? { plan: planPath } : {}),
      ...(profile ? { profile } : {}),
      ...(final ? { final } : {}),
      errors: [{ code: "MANIFEST_READ_FAILED", path: "/", message: error instanceof Error ? error.message : String(error) }],
      warnings,
      assets: 0,
    };
  }
  const issues = manifestIssues(raw);
  if (issues.length > 0) {
    errors.push(...issues.map((issue) => ({
      code: "MANIFEST_SCHEMA_INVALID",
      path: `/${(issue.path as unknown[] | undefined)?.join("/") ?? ""}`,
      message: String(issue.message ?? "Invalid manifest"),
    })));
    return { ok: false, command: "validate", manifest: manifestPath, ...(planPath ? { plan: planPath } : {}), ...(profile ? { profile } : {}), ...(final ? { final } : {}), errors, warnings, assets: 0 };
  }
  const manifest = raw as Manifest;
  let visualPlan: VisualPlan | undefined;
  if (planPath) {
    try {
      const planRaw = await readJson(planPath);
      const planSchemaIssues = visualPlanIssues(planRaw);
      if (planSchemaIssues.length > 0) {
        errors.push(...planSchemaIssues.map((issue) => ({
          code: "VISUAL_PLAN_SCHEMA_INVALID",
          path: `/plan/${(issue.path as unknown[] | undefined)?.join("/") ?? ""}`,
          message: String(issue.message ?? "Invalid visual plan"),
        })));
      } else {
        visualPlan = planRaw as VisualPlan;
      }
    } catch (error) {
      errors.push({ code: "VISUAL_PLAN_READ_FAILED", path: "/plan", message: error instanceof Error ? error.message : String(error) });
    }
  }
  if (final) {
    const article = manifest.article as Record<string, unknown>;
    const articlePathValue = article.path;
    const articleVersion = article.version;
    const articleSha256 = article.sha256;
    if (typeof articlePathValue !== "string" || !articlePathValue || (typeof articleVersion !== "string" && typeof articleVersion !== "number") || !String(articleVersion) || typeof articleSha256 !== "string" || !/^[a-f0-9]{64}$/i.test(articleSha256)) {
      errors.push({ code: "ARTICLE_BINDING_MISSING", path: "/article", message: "Final validation requires article path, version and sha256" });
    } else {
      const articlePath = resolve(dirname(manifestPath), articlePathValue);
      try {
        await ensureFile(articlePath, "ARTICLE_NOT_FOUND");
        const actualHash = await sha256File(articlePath);
        if (actualHash.toLowerCase() !== articleSha256.toLowerCase()) errors.push({ code: "ARTICLE_HASH_MISMATCH", path: "/article/sha256", message: "Article sha256 does not match the current article source", details: { expected: articleSha256, actual: actualHash } });
      } catch (error) {
        errors.push({ code: "ARTICLE_NOT_FOUND", path: "/article/path", message: error instanceof Error ? error.message : String(error) });
      }
    }
  }
  const viewportWidth = profile === "wechat" ? 677 : profile === "desktop" ? 960 : undefined;
  const base = dirname(manifestPath);
  if (visualPlan && planPath) {
    const manifestArticle = manifest.article as Record<string, unknown>;
    const planArticlePath = resolve(dirname(planPath), visualPlan.article.path);
    const manifestArticlePath = resolve(base, String(manifestArticle.path));
    if (planArticlePath !== manifestArticlePath) {
      errors.push({ code: "VISUAL_PLAN_ARTICLE_MISMATCH", path: "/plan/article/path", message: "Visual plan and manifest must reference the same article", details: { plan: planArticlePath, manifest: manifestArticlePath } });
    }
    if (String(visualPlan.article.version) !== String(manifestArticle.version)) {
      errors.push({ code: "VISUAL_PLAN_VERSION_MISMATCH", path: "/plan/article/version", message: "Visual plan and manifest article versions must match", details: { plan: visualPlan.article.version, manifest: manifestArticle.version } });
    }
    if (final) {
      const planItems = new Map(visualPlan.items.map((item) => [item.id, item]));
      const manifestAssets = new Map(manifest.assets.map((asset) => [asset.id, asset]));
      for (const asset of manifest.assets.filter((candidate) => candidate.approval === "approved")) {
        const item = planItems.get(asset.id);
        if (!item) {
          errors.push({ code: "VISUAL_PLAN_ITEM_MISSING", path: "/plan/items", message: `Approved asset ${asset.id} has no visual-plan item`, details: { asset: asset.id } });
        } else {
          if (item.status !== "approved" && item.status !== "placed") errors.push({ code: "VISUAL_PLAN_ITEM_NOT_APPROVED", path: `/plan/items/${visualPlan.items.indexOf(item)}/status`, message: `Approved asset ${asset.id} must be approved or placed in the visual plan`, details: { status: item.status } });
          if ((item.function === "evidence" || item.function === "demonstration") && (!item.evidenceIds || item.evidenceIds.length === 0)) errors.push({ code: "VISUAL_PLAN_EVIDENCE_MISSING", path: `/plan/items/${visualPlan.items.indexOf(item)}/evidenceIds`, message: `${item.function} item ${asset.id} requires at least one evidence ID` });
        }
      }
      for (const [itemIndex, item] of visualPlan.items.entries()) {
        if (item.status !== "approved" && item.status !== "placed") continue;
        const asset = manifestAssets.get(item.id);
        if (!asset || asset.approval !== "approved" || asset.status !== "produced") errors.push({ code: "VISUAL_PLAN_ASSET_NOT_APPROVED", path: `/plan/items/${itemIndex}/status`, message: `Visual-plan item ${item.id} is final but its manifest asset is not approved and produced` });
      }
    }
  }
  for (const [assetIndex, asset] of manifest.assets.entries()) {
    const assetPath = `/assets/${assetIndex}`;
    // A rejected candidate is retained only as an audit decision. It is not
    // part of the publishable set, so final validation must not require its
    // source/output files or emit channel-profile noise for it.
    if (final && asset.approval === "rejected") continue;
    if (final && asset.status !== "produced") {
      errors.push({ code: "ASSET_NOT_CURRENT", path: `${assetPath}/status`, message: "Final validation requires every retained asset to be produced and current", details: { status: asset.status } });
    }
    if (final && asset.approval === "unreviewed") {
      errors.push({ code: "ASSET_NOT_REVIEWED", path: `${assetPath}/approval`, message: "Final validation requires a review decision for every asset", details: { approval: asset.approval } });
    }
    const sourcePath = resolve(base, asset.source);
    try {
      await ensureFile(sourcePath);
      const sourceHash = await sha256File(sourcePath);
      if (sourceHash.toLowerCase() !== asset.sourceSha256.toLowerCase()) {
        errors.push({ code: "SOURCE_HASH_MISMATCH", path: `${assetPath}/sourceSha256`, message: "sourceSha256 does not match the current source file", details: { expected: asset.sourceSha256, actual: sourceHash } });
      }
    } catch (error) {
      errors.push({ code: "SOURCE_NOT_FOUND", path: `${assetPath}/source`, message: error instanceof Error ? error.message : String(error) });
    }
    for (const [outputIndex, output] of asset.outputs.entries()) {
      const outputPath = resolve(base, output.path);
      const outputPathRef = `${assetPath}/outputs/${outputIndex}`;
      try {
        await ensureFile(outputPath);
        const size = await imageInfo(outputPath);
        if (output.width !== size.width || output.height !== size.height) {
          errors.push({ code: "OUTPUT_DIMENSIONS_MISMATCH", path: outputPathRef, message: "Manifest output dimensions do not match the image", details: { declared: { width: output.width, height: output.height }, actual: size } });
        }
        if (viewportWidth !== undefined) {
          // Profiles model the reading column, not an export pixel cap. A
          // high-resolution asset is downscaled by the page; only its
          // rendered footprint and low-resolution risks are reported.
          const scale = size.width > viewportWidth ? viewportWidth / size.width : 1;
          const display = { width: Math.round(size.width * scale), height: Math.round(size.height * scale), scale: Number(scale.toFixed(4)) };
          profileChecks.push({ asset: asset.id, output: output.path, native: size, viewportWidth, display });
          if (size.width < viewportWidth) {
            warnings.push({ code: "PROFILE_LOW_RESOLUTION", path: outputPathRef, message: `${profile} viewport is ${viewportWidth}px but this asset is only ${size.width}px wide; it will not be upscaled by default`, details: { nativeWidth: size.width, viewportWidth } });
          }
          if (display.height > 4000) {
            warnings.push({ code: "PROFILE_TALL_DISPLAY", path: outputPathRef, message: `${profile} rendered height is ${display.height}px; consider split or a shorter presentation`, details: { display } });
          }
          if (display.width < 120 || display.height < 40) {
            warnings.push({ code: "PROFILE_THIN_DISPLAY", path: outputPathRef, message: `${profile} rendered asset is unusually small and may contain unreadable text`, details: { display } });
          }
        }
        if (output.sha256) {
          const actualHash = await sha256File(outputPath);
          if (actualHash.toLowerCase() !== output.sha256.toLowerCase()) errors.push({ code: "OUTPUT_HASH_MISMATCH", path: `${outputPathRef}/sha256`, message: "Manifest output sha256 does not match the current output file", details: { expected: output.sha256, actual: actualHash } });
        }
      } catch (error) {
        errors.push({ code: "OUTPUT_NOT_FOUND_OR_INVALID", path: outputPathRef, message: error instanceof Error ? error.message : String(error) });
      }
      if (resolve(sourcePath) === outputPath) errors.push({ code: "OUTPUT_EQUALS_INPUT", path: outputPathRef, message: "Manifest output must not overwrite its source" });
    }
    if (asset.status === "produced" && asset.outputs.length === 0) warnings.push({ code: "ASSET_HAS_NO_OUTPUTS", path: `${assetPath}/outputs`, message: "Produced asset has no outputs" });
  }
  return { ok: errors.length === 0, command: "validate", manifest: manifestPath, ...(planPath ? { plan: planPath } : {}), ...(profile ? { profile } : {}), ...(final ? { final } : {}), errors, warnings, assets: manifest.assets.length, ...(profile ? { profileChecks } : {}) };
}
