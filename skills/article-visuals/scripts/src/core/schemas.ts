import { z } from "zod";
import type { Manifest, Recipe, VisualPlan } from "./types.js";

const OperationSchema = z.object({
  op: z.string().min(1),
}).passthrough();

export const RecipeSchema = z.object({
  version: z.literal(1),
  input: z.string().min(1),
  output: z.union([
    z.string().min(1),
    z.object({ path: z.string().min(1).optional(), dir: z.string().min(1).optional(), pattern: z.string().min(1).optional() }).passthrough(),
  ]).optional(),
  outputs: z.array(z.union([
    z.string().min(1),
    z.object({ path: z.string().min(1).optional(), dir: z.string().min(1).optional(), pattern: z.string().min(1).optional() }).passthrough(),
  ])).optional(),
  operations: z.array(OperationSchema).min(1),
}).passthrough();

const SizeSchema = z.object({
  width: z.number().int().positive(),
  height: z.number().int().positive(),
}).passthrough();

const ManifestOutputSchema = z.object({
  path: z.string().min(1),
  width: z.number().int().positive(),
  height: z.number().int().positive(),
  sha256: z.string().regex(/^[a-f0-9]{64}$/i),
  bytes: z.number().int().nonnegative(),
}).passthrough();

const ManifestAssetSchema = z.object({
  id: z.string().min(1),
  purpose: z.string().min(1),
  source: z.string().min(1),
  sourceSha256: z.string().regex(/^[a-f0-9]{64}$/i),
  originalSize: SizeSchema,
  recipe: z.record(z.unknown()),
  outputs: z.array(ManifestOutputSchema).min(1),
  status: z.enum(["produced", "stale", "failed"]),
  approval: z.enum(["unreviewed", "approved", "rejected"]),
}).passthrough();

export const ManifestSchema = z.object({
  version: z.literal(1),
  run: z.object({
    id: z.string().min(1),
    createdAt: z.string().min(1),
  }).passthrough(),
  article: z.object({
    path: z.string().min(1),
    version: z.union([z.string().min(1), z.number()]),
    sha256: z.string().regex(/^[a-f0-9]{64}$/i),
  }).passthrough(),
  assets: z.array(ManifestAssetSchema),
}).passthrough();

const VisualPlanItemSchema = z.object({
  id: z.string().min(1),
  position: z.string().min(1),
  function: z.enum(["evidence", "demonstration", "explanation", "comparison", "navigation", "atmosphere", "cover"]),
  serves: z.string().min(1),
  altText: z.string().min(1),
  preferredRoute: z.string().min(1),
  alternatives: z.array(z.string().min(1)),
  evidenceIds: z.array(z.string().min(1)).optional(),
  tradeoff: z.string().min(1).optional(),
  status: z.enum(["planned", "acquiring", "candidate", "approved", "placed", "blocked", "rejected"]),
}).passthrough();

export const VisualPlanSchema = z.object({
  version: z.literal(1),
  article: z.object({
    path: z.string().min(1),
    version: z.union([z.string().min(1), z.number()]),
  }).passthrough(),
  channels: z.array(z.string().min(1)).min(1),
  items: z.array(VisualPlanItemSchema),
}).passthrough();

export function parseRecipe(value: unknown): Recipe {
  const result = RecipeSchema.safeParse(value);
  if (!result.success) {
    throw new Error(JSON.stringify({ issues: result.error.issues }));
  }
  return result.data as unknown as Recipe;
}

export function parseManifest(value: unknown): Manifest {
  const result = ManifestSchema.safeParse(value);
  if (!result.success) {
    throw new Error(JSON.stringify({ issues: result.error.issues }));
  }
  return result.data as unknown as Manifest;
}

export function manifestIssues(value: unknown): Array<Record<string, unknown>> {
  const result = ManifestSchema.safeParse(value);
  return result.success ? [] : result.error.issues.map((issue) => ({
    code: issue.code,
    path: issue.path,
    message: issue.message,
  }));
}

export function parseVisualPlan(value: unknown): VisualPlan {
  const result = VisualPlanSchema.safeParse(value);
  if (!result.success) throw new Error(JSON.stringify({ issues: result.error.issues }));
  return result.data as VisualPlan;
}

export function visualPlanIssues(value: unknown): Array<Record<string, unknown>> {
  const result = VisualPlanSchema.safeParse(value);
  return result.success ? [] : result.error.issues.map((issue) => ({
    code: issue.code,
    path: issue.path,
    message: issue.message,
  }));
}
