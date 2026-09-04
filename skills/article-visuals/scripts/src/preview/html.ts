import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import sharp from "sharp";
import { atomicWriteFile, ensureFile } from "../core/fs.js";
import { VisualAssetsError } from "../core/errors.js";
import { manifestIssues, visualPlanIssues } from "../core/schemas.js";
import type { Manifest, ManifestAsset, ManifestOutput, VisualPlan, VisualPlanItem } from "../core/types.js";

function escapeHtml(value: unknown): string {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

async function dataUrl(path: string): Promise<string | undefined> {
  try {
    const data = await sharp(path, { failOn: "error" })
      .rotate()
      .resize({ width: 1200, withoutEnlargement: true })
      .webp({ quality: 84 })
      .toBuffer();
    return `data:image/webp;base64,${data.toString("base64")}`;
  } catch {
    return undefined;
  }
}

function outputValues(asset: ManifestAsset): ManifestOutput[] {
  return asset.outputs;
}

async function assetMarkup(asset: ManifestAsset, manifestPath: string, planItem?: VisualPlanItem): Promise<string> {
  const base = dirname(resolve(manifestPath));
  const source = resolve(base, asset.source);
  const sourceData = await dataUrl(source);
  const outputs = await Promise.all(outputValues(asset).map(async (output) => ({ output, data: await dataUrl(resolve(base, output.path)) })));
  const image = (title: string, path: string, data: string | undefined, size?: { width?: number; height?: number }) => data
    ? `<figure class="asset-image"><figcaption>${escapeHtml(title)} <code>${escapeHtml(path)}</code></figcaption><img src="${data}" alt="${escapeHtml(title)}" loading="lazy"/><small>${size?.width && size.height ? `${size.width} × ${size.height}` : ""}</small></figure>`
    : `<figure class="asset-image missing"><figcaption>${escapeHtml(title)} <code>${escapeHtml(path)}</code></figcaption><div>Missing local file</div></figure>`;
  const outputHtml = outputs.map(({ output, data }) => {
    return image("Output", output.path, data, { width: output.width, height: output.height });
  }).join("");
  const viewportLabels = [["Mobile", 375], ["WeChat content", 677], ["Desktop", 960]];
  const viewportHtml = viewportLabels.map(([label, width]) => `<div class="viewport" style="width:${width}px;max-width:100%"><label>${escapeHtml(label)} · ${width}px</label>${outputs.map(({ output, data }) => data ? `<img src="${data}" alt="${escapeHtml(output.path)}" loading="lazy"/>` : `<div class="missing">Missing local file: ${escapeHtml(output.path)}</div>`).join("") || "<p>No outputs</p>"}</div>`).join("");
  const context = planItem ? `<dl class="context"><div><dt>Position</dt><dd>${escapeHtml(planItem.position)}</dd></div><div><dt>Function</dt><dd>${escapeHtml(planItem.function)}</dd></div><div><dt>Serves</dt><dd>${escapeHtml(planItem.serves)}</dd></div><div><dt>Alt text</dt><dd>${escapeHtml(planItem.altText)}</dd></div><div><dt>Evidence</dt><dd>${escapeHtml(planItem.evidenceIds?.join(", ") || "—")}</dd></div><div><dt>Tradeoff</dt><dd>${escapeHtml(planItem.tradeoff || "—")}</dd></div></dl>` : "";
  return `<section class="asset" id="asset-${escapeHtml(asset.id)}"><h2>${escapeHtml(asset.id)}</h2><p class="purpose">${escapeHtml(asset.purpose)} · production: ${escapeHtml(asset.status)} · approval: ${escapeHtml(asset.approval ?? "unreviewed")}</p>${context}<div class="comparison"><div><h3>Original</h3>${image("Original", asset.source, sourceData, asset.originalSize)}</div><div><h3>Outputs</h3>${outputHtml || "<p>No outputs</p>"}</div></div><h3 class="viewport-heading">Viewport simulation</h3><div class="viewports">${viewportHtml}</div></section>`;
}

export async function generatePreview(manifestPath: string, visualPlanPath?: string): Promise<string> {
  await ensureFile(manifestPath, "MANIFEST_NOT_FOUND");
  let raw: unknown;
  try {
    raw = JSON.parse(await readFile(manifestPath, "utf8"));
  } catch (error) {
    throw new VisualAssetsError("MANIFEST_PARSE_FAILED", `Invalid manifest JSON: ${manifestPath}`, { cause: error instanceof Error ? error.message : String(error) });
  }
  const issues = manifestIssues(raw);
  if (issues.length > 0) throw new VisualAssetsError("MANIFEST_SCHEMA_INVALID", "Manifest does not match schema v1", { issues });
  const manifest = raw as Manifest;
  let visualPlan: VisualPlan | undefined;
  if (visualPlanPath) {
    await ensureFile(visualPlanPath, "VISUAL_PLAN_NOT_FOUND");
    let planRaw: unknown;
    try {
      planRaw = JSON.parse(await readFile(visualPlanPath, "utf8"));
    } catch (error) {
      throw new VisualAssetsError("VISUAL_PLAN_PARSE_FAILED", `Invalid visual plan JSON: ${visualPlanPath}`, { cause: error instanceof Error ? error.message : String(error) });
    }
    const planIssues = visualPlanIssues(planRaw);
    if (planIssues.length > 0) throw new VisualAssetsError("VISUAL_PLAN_SCHEMA_INVALID", "Visual plan does not match schema v1", { issues: planIssues });
    visualPlan = planRaw as VisualPlan;
  }
  const planItems = new Map(visualPlan?.items.map((item) => [item.id, item]) ?? []);
  const planOrder = new Map(visualPlan?.items.map((item, index) => [item.id, index]) ?? []);
  const orderedAssets = [...manifest.assets].sort((left, right) => (planOrder.get(left.id) ?? Number.MAX_SAFE_INTEGER) - (planOrder.get(right.id) ?? Number.MAX_SAFE_INTEGER));
  const assets = await Promise.all(orderedAssets.map((asset) => assetMarkup(asset, manifestPath, planItems.get(asset.id))));
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>visual-assets preview</title>
<style>
:root{color-scheme:light dark;font-family:ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#f6f7f9;color:#111827}
*{box-sizing:border-box}body{margin:0;padding:24px}main{max-width:1180px;margin:0 auto}h1{margin:0 0 8px;font-size:28px}h2{margin:0;font-size:20px}h3{font-size:14px;margin:0 0 10px;color:#4b5563}.intro{margin:0 0 22px;color:#6b7280}.asset{background:#fff;border:1px solid #d1d5db;border-radius:14px;padding:18px;margin:0 0 20px;box-shadow:0 3px 12px #00000010}.purpose{color:#6b7280;font-size:13px;margin:5px 0 12px}.context{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px 18px;margin:0 0 18px;padding:12px;border-radius:10px;background:#f3f4f6}.context div{min-width:0}.context dt{font-size:11px;font-weight:700;text-transform:uppercase;color:#6b7280}.context dd{margin:3px 0 0;font-size:13px;overflow-wrap:anywhere}.comparison{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:18px}.comparison>div{min-width:0}.asset-image{margin:0 0 14px;border:1px solid #e5e7eb;border-radius:10px;padding:10px;background:#fafafa;overflow:hidden}.asset-image figcaption{font-size:12px;margin-bottom:8px;color:#374151;word-break:break-all}.asset-image code{font-size:11px;color:#6b7280}.asset-image img{display:block;max-width:100%;height:auto;margin:0 auto}.asset-image small{display:block;color:#6b7280;font-size:11px;margin-top:6px}.missing div{padding:22px;color:#b91c1c;background:#fef2f2}.viewports{display:grid;grid-template-columns:375px 677px 960px;gap:12px;align-items:start;overflow-x:auto;padding-bottom:8px}.viewport{background:#fff;border:2px solid #9ca3af;border-radius:10px;padding:10px;min-height:80px}.viewport label{font-size:11px;color:#6b7280;display:block;margin-bottom:8px}.viewport img{display:block;max-width:100%;height:auto}
@media(max-width:760px){body{padding:12px}.comparison,.context{grid-template-columns:1fr}.asset{padding:12px}}
@media(prefers-color-scheme:dark){:root{background:#111827;color:#f9fafb}.asset{background:#1f2937;border-color:#374151}.context{background:#111827}.asset-image{background:#111827;border-color:#374151}.asset-image figcaption,.asset-image code{color:#d1d5db}.viewport{background:#111827;border-color:#6b7280}}
</style>
</head>
<body><main><h1>visual-assets preview</h1><p class="intro">Self-contained comparison · simulated content widths: mobile 375px, WeChat 677px, desktop 960px.</p>${assets.join("")}</main></body></html>`;
}

export async function writePreview(manifestPath: string, output: string, visualPlanPath?: string): Promise<void> {
  const html = await generatePreview(manifestPath, visualPlanPath);
  await atomicWriteFile(output, html);
}
