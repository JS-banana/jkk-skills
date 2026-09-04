export interface PointSpec {
  x: number;
  y: number;
  space?: "pixel" | "normalized";
  unit?: "pixel" | "normalized";
}

export interface RectSpec {
  x?: number;
  y?: number;
  left?: number;
  top?: number;
  width: number;
  height: number;
  space?: "pixel" | "normalized";
  unit?: "pixel" | "normalized";
  mode?: "pixel" | "normalized";
  normalized?: { x: number; y: number; width: number; height: number };
  pixel?: { x: number; y: number; width: number; height: number };
}

export interface OperationSpec {
  op: string;
  [key: string]: unknown;
}

export interface OutputSpec {
  path?: string;
  dir?: string;
  pattern?: string;
}

export interface Recipe {
  version: 1;
  input: string;
  output?: string | OutputSpec;
  outputs?: Array<string | OutputSpec>;
  operations: OperationSpec[];
  id?: string;
  assetId?: string;
  purpose?: string;
  article?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface ImageDimensions {
  width: number;
  height: number;
}

export interface ImageOutputRecord extends ImageDimensions {
  path: string;
  sha256: string;
  bytes: number;
  index?: number;
}

export interface TransformResult {
  ok: true;
  command: "transform";
  input: string;
  sourceSha256: string;
  originalSize: ImageDimensions;
  recipe: Recipe;
  outputs: ImageOutputRecord[];
  asset: ManifestAsset;
}

export interface ManifestOutput extends ImageDimensions {
  path: string;
  sha256?: string;
  bytes?: number;
  purpose?: string;
}

export interface ManifestAsset {
  id: string;
  purpose: string;
  source: string;
  sourceSha256: string;
  originalSize: ImageDimensions;
  recipe: Recipe;
  outputs: ManifestOutput[];
  /** Production lifecycle. approval is deliberately separate from rendering. */
  status: "produced" | "stale" | "failed";
  approval?: "unreviewed" | "approved" | "rejected";
  error?: { code: string; message: string };
}

export interface Manifest {
  version: 1;
  run: Record<string, unknown>;
  article: Record<string, unknown>;
  assets: ManifestAsset[];
  [key: string]: unknown;
}

export type VisualFunction = "evidence" | "demonstration" | "explanation" | "comparison" | "navigation" | "atmosphere" | "cover";
export type VisualPlanStatus = "planned" | "acquiring" | "candidate" | "approved" | "placed" | "blocked" | "rejected";

export interface VisualPlanItem {
  id: string;
  position: string;
  function: VisualFunction;
  serves: string;
  altText: string;
  preferredRoute: string;
  alternatives: string[];
  evidenceIds?: string[];
  tradeoff?: string;
  status: VisualPlanStatus;
}

export interface VisualPlan {
  version: 1;
  article: { path: string; version: string | number };
  channels: string[];
  items: VisualPlanItem[];
}

export interface ResolvedRect {
  left: number;
  top: number;
  width: number;
  height: number;
}

export interface InspectResult {
  ok: true;
  command: "inspect";
  input: string;
  sha256: string;
  bytes: number;
  format?: string;
  width: number;
  height: number;
  rawWidth?: number;
  rawHeight?: number;
  space?: string;
  channels?: number;
  hasAlpha?: boolean;
  density?: number;
  orientation?: number;
  isAnimated?: boolean;
  pages?: number;
  pageHeight?: number;
}
