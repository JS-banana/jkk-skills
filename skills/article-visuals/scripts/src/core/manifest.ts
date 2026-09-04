import { randomUUID } from "node:crypto";
import { readJson, atomicWriteFile, ensureFile, relativePath, resolvePath, sha256File } from "./fs.js";
import { VisualAssetsError } from "./errors.js";
import { manifestIssues, visualPlanIssues } from "./schemas.js";
import type { Manifest, VisualPlan } from "./types.js";
import { dirname, resolve } from "node:path";

export async function initManifest(manifestPathValue: string, articlePathValue: string, articleVersion: string): Promise<{ ok: true; command: "init"; manifest: string; article: Record<string, unknown> }> {
  const manifestPath = resolve(manifestPathValue);
  const articlePath = resolvePath(articlePathValue, dirname(manifestPath));
  await ensureFile(articlePath, "ARTICLE_NOT_FOUND");
  try {
    await ensureFile(manifestPath);
    throw new VisualAssetsError("MANIFEST_EXISTS", `Manifest already exists: ${manifestPath}`, { path: manifestPath });
  } catch (error) {
    if (error instanceof VisualAssetsError && error.code !== "INPUT_NOT_FOUND") throw error;
    if (!(error instanceof VisualAssetsError)) throw error;
    // A missing manifest is the only expected path through this branch.
  }
  if (!articleVersion.trim()) throw new VisualAssetsError("ARTICLE_VERSION_REQUIRED", "Article version must not be empty");
  const article = {
    path: relativePath(manifestPath, articlePath),
    version: articleVersion,
    sha256: await sha256File(articlePath),
  };
  const manifest: Manifest = {
    version: 1,
    run: { id: randomUUID(), createdAt: new Date().toISOString() },
    article,
    assets: [],
  };
  await atomicWriteFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
  return { ok: true, command: "init", manifest: manifestPath, article };
}

export async function reviewManifest(manifestPathValue: string, ids: string[], decision: "approved" | "rejected", visualPlanPathValue?: string): Promise<{ ok: true; command: "review"; manifest: string; plan?: string; decision: string; assets: string[] }> {
  if (ids.length === 0 || ids.some((id) => !id.trim())) throw new VisualAssetsError("ASSET_IDS_REQUIRED", "review requires one or more asset IDs");
  const manifestPath = resolve(manifestPathValue);
  const raw = await readJson(manifestPath);
  const issues = manifestIssues(raw);
  if (issues.length > 0) throw new VisualAssetsError("MANIFEST_SCHEMA_INVALID", "Manifest does not match schema v1", { issues });
  const manifest = raw as Manifest;
  const visualPlanPath = visualPlanPathValue ? resolve(visualPlanPathValue) : undefined;
  let visualPlan: VisualPlan | undefined;
  if (visualPlanPath) {
    const planRaw = await readJson(visualPlanPath);
    const planIssues = visualPlanIssues(planRaw);
    if (planIssues.length > 0) throw new VisualAssetsError("VISUAL_PLAN_SCHEMA_INVALID", "Visual plan does not match schema v1", { issues: planIssues });
    visualPlan = planRaw as VisualPlan;
  }
  const uniqueIds = [...new Set(ids.map((id) => id.trim()))];
  const missing = uniqueIds.filter((id) => !manifest.assets.some((asset) => asset.id === id));
  if (missing.length > 0) throw new VisualAssetsError("ASSET_NOT_FOUND", "One or more asset IDs do not exist", { missing });
  if (visualPlan) {
    const missingPlanItems = uniqueIds.filter((id) => !visualPlan.items.some((item) => item.id === id));
    if (missingPlanItems.length > 0) throw new VisualAssetsError("VISUAL_PLAN_ITEM_MISSING", "One or more asset IDs do not exist in the visual plan", { missing: missingPlanItems });
  }
  for (const asset of manifest.assets) {
    if (!uniqueIds.includes(asset.id)) continue;
    asset.approval = decision;
  }
  if (visualPlan && visualPlanPath) {
    for (const item of visualPlan.items) {
      if (uniqueIds.includes(item.id)) item.status = decision === "approved" ? "approved" : "rejected";
    }
    await atomicWriteFile(visualPlanPath, `${JSON.stringify(visualPlan, null, 2)}\n`);
  }
  await atomicWriteFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
  return { ok: true, command: "review", manifest: manifestPath, ...(visualPlanPath ? { plan: visualPlanPath } : {}), decision, assets: uniqueIds };
}

export async function rebaseVisualRun(manifestPathValue: string, visualPlanPathValue: string, articlePathValue: string, articleVersion: string): Promise<{ ok: true; command: "rebase"; manifest: string; plan: string; article: Record<string, unknown>; resetAssets: string[] }> {
  if (!articleVersion.trim()) throw new VisualAssetsError("ARTICLE_VERSION_REQUIRED", "Article version must not be empty");
  const manifestPath = resolve(manifestPathValue);
  const visualPlanPath = resolve(visualPlanPathValue);
  const articlePath = resolvePath(articlePathValue, dirname(manifestPath));
  await ensureFile(articlePath, "ARTICLE_NOT_FOUND");
  const manifestRaw = await readJson(manifestPath);
  const manifestSchemaIssues = manifestIssues(manifestRaw);
  if (manifestSchemaIssues.length > 0) throw new VisualAssetsError("MANIFEST_SCHEMA_INVALID", "Manifest does not match schema v1", { issues: manifestSchemaIssues });
  const planRaw = await readJson(visualPlanPath);
  const planSchemaIssues = visualPlanIssues(planRaw);
  if (planSchemaIssues.length > 0) throw new VisualAssetsError("VISUAL_PLAN_SCHEMA_INVALID", "Visual plan does not match schema v1", { issues: planSchemaIssues });
  const manifest = manifestRaw as Manifest;
  const visualPlan = planRaw as VisualPlan;
  const previousArticle = { ...manifest.article };
  const article = { path: relativePath(manifestPath, articlePath), version: articleVersion, sha256: await sha256File(articlePath) };
  manifest.article = article;
  manifest.run = { ...manifest.run, rebasedAt: new Date().toISOString(), rebasedFrom: previousArticle };
  const resetAssets: string[] = [];
  for (const asset of manifest.assets) {
    if (asset.approval === "rejected") continue;
    asset.approval = "unreviewed";
    resetAssets.push(asset.id);
  }
  visualPlan.article = { path: relativePath(visualPlanPath, articlePath), version: articleVersion };
  for (const item of visualPlan.items) {
    if (item.status === "approved" || item.status === "placed") item.status = "candidate";
  }
  await atomicWriteFile(visualPlanPath, `${JSON.stringify(visualPlan, null, 2)}\n`);
  await atomicWriteFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
  return { ok: true, command: "rebase", manifest: manifestPath, plan: visualPlanPath, article, resetAssets };
}
