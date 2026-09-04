#!/usr/bin/env node
import { errorFromUnknown, VisualAssetsError } from "./core/errors.js";
import { atomicWriteFile, readJson, resolvePath } from "./core/fs.js";
import { inspectImage } from "./core/image.js";
import { parseRecipe } from "./core/schemas.js";
import { validateManifest, type ValidationProfile } from "./core/validate.js";
import { initManifest, rebaseVisualRun, reviewManifest } from "./core/manifest.js";
import { createAnalysisBoard } from "./operations/board.js";
import { transformRecipe } from "./operations/transform.js";
import { generatePreview } from "./preview/html.js";

interface Args {
  command: string;
  values: Record<string, string | boolean>;
  positionals: string[];
}

function parseArgs(argv: string[]): Args {
  const [command = "help", ...rest] = argv;
  const values: Record<string, string | boolean> = {};
  const positionals: string[] = [];
  for (let index = 0; index < rest.length; index += 1) {
    const current = rest[index];
    if (!current.startsWith("--")) {
      positionals.push(current);
      continue;
    }
    const key = current.slice(2);
    if (!key) throw new VisualAssetsError("INVALID_ARGUMENT", "Flag name must not be empty");
    const next = rest[index + 1];
    if (next && !next.startsWith("--")) {
      values[key] = next;
      index += 1;
    } else {
      values[key] = true;
    }
  }
  return { command, values, positionals };
}

function value(args: Args, name: string): string | undefined {
  const candidate = args.values[name];
  return typeof candidate === "string" ? candidate : undefined;
}

function requireValue(args: Args, name: string): string {
  const result = value(args, name);
  if (!result) throw new VisualAssetsError("ARGUMENT_REQUIRED", `Missing required argument --${name}`, { argument: name });
  return result;
}

function capabilities(): Record<string, unknown> {
  return {
    ok: true,
    name: "visual-assets",
    version: 1,
    engine: { runtime: "node", minimumNode: "22", image: "sharp/libvips" },
    commands: {
      capabilities: { usage: "capabilities --json", description: "Print this machine-readable capability document" },
      inspect: { usage: "inspect --input <image> --json", description: "Read image metadata and oriented dimensions" },
      "analysis-board": { usage: "analysis-board --input <image> --output <png>", description: "Write a coordinate-grid PNG for normalized region selection" },
      transform: { usage: "transform --recipe <recipe.json> [--input <image>] [--output <image>] [--manifest <manifest.json>] --json", description: "Replay a v1 image recipe with atomic, non-destructive outputs" },
      preview: { usage: "preview --manifest <manifest.json> [--plan <visual-plan.json>] [--output <preview.html>]", description: "Write a self-contained article-context and original/output comparison preview" },
      validate: { usage: "validate --manifest <manifest.json> [--plan <visual-plan.json>] [--profile wechat|desktop] [--final] --json", description: "Validate manifest v1, optional visual-plan v1, local files, hashes and optional width/final approval profile" },
      init: { usage: "init --manifest <manifest.json> --article <article.md> --version <version> --json", description: "Initialize a manifest with article path/version/hash binding (run before transform --manifest)" },
      review: { usage: "review --manifest <manifest.json> [--plan <visual-plan.json>] (--approve <id,...> | --reject <id,...>) --json", description: "Approve or reject asset IDs and optionally synchronize visual-plan statuses" },
      rebase: { usage: "rebase --manifest <manifest.json> --plan <visual-plan.json> --article <article.md> --version <version> --json", description: "Rebind a visual run to a changed article and reset retained assets for review" },
    },
    recipe: {
      version: 1,
      shape: { version: 1, input: "relative/or/absolute/image.png", output: "output.png", operations: [{ op: "crop", mode: "normalized", x: 0, y: 0, width: 1, height: 1 }] },
      operations: {
        crop: "pixel or normalized rectangle; out-of-bounds rejected",
        trim: "remove uniform border; optional background and threshold",
        resize: "width/height, fit; withoutEnlargement is true by default",
        pad: "target width+height or aspectRatio (number or e.g. 4:3); never crops",
        split: "vertical fan-out endpoint; maxPanelHeight (default 2048) and overlap",
        annotate: "annotations: box, highlight, arrow, number, blur, redact, zoom-inset",
      },
      invariants: ["input is never overwritten", "output is written to a temporary sibling then atomically renamed", "EXIF metadata is stripped by default and orientation is applied", "maximum image budget is 50,000,000 pixels"],
    },
    manifest: {
      version: 1,
      requiredAssetFields: ["id", "purpose", "source", "sourceSha256", "originalSize", "recipe", "outputs", "status"],
      lifecycle: { status: ["produced", "stale", "failed"], approval: ["unreviewed", "approved", "rejected"] },
      paths: "source and outputs are resolved relative to the manifest file",
    },
    visualPlan: {
      version: 1,
      requiredItemFields: ["id", "position", "function", "serves", "altText", "preferredRoute", "alternatives", "status"],
      finalStatuses: ["approved", "placed"],
      paths: "article path is resolved relative to the visual-plan file",
    },
    preview: { viewports: { mobile: 375, wechat: 677, desktop: 960 }, remoteAssets: false },
  };
}

function printHuman(valueToPrint: unknown): void {
  process.stdout.write(`${typeof valueToPrint === "string" ? valueToPrint : JSON.stringify(valueToPrint, null, 2)}\n`);
}

function printJson(valueToPrint: unknown): void {
  process.stdout.write(`${JSON.stringify(valueToPrint)}\n`);
}

function help(): string {
  return `visual-assets — recipe-driven article image assets (Node 22 + sharp/libvips)

Commands:
  capabilities --json
  inspect --input <image> --json
  analysis-board --input <image> --output <png>
  transform --recipe <recipe.json> [--input <image>] [--output <image>] [--manifest <manifest.json>] --json
  preview --manifest <manifest.json> [--plan <visual-plan.json>] [--output <preview.html>]
  validate --manifest <manifest.json> [--plan <visual-plan.json>] [--profile wechat|desktop] [--final] --json
  init --manifest <manifest.json> --article <article.md> --version <version> --json
  review --manifest <manifest.json> [--plan <visual-plan.json>] (--approve <id,...> | --reject <id,...>) --json
  rebase --manifest <manifest.json> --plan <visual-plan.json> --article <article.md> --version <version> --json

All JSON failures use {ok:false,error:{code,message,details}} and exit non-zero.
Run capabilities --json for the full recipe and manifest contract.
`;
}

async function loadRecipe(path: string): Promise<unknown> {
  const raw = await readJson(path);
  try {
    return parseRecipe(raw);
  } catch (error) {
    throw new VisualAssetsError("RECIPE_SCHEMA_INVALID", "Recipe does not match recipe v1", { path, cause: error instanceof Error ? error.message : String(error) });
  }
}

async function main(args: Args): Promise<unknown> {
  switch (args.command) {
    case "help":
    case "--help":
    case "-h":
      return help();
    case "capabilities":
      return capabilities();
    case "inspect": {
      const input = resolvePath(requireValue(args, "input"));
      return inspectImage(input);
    }
    case "analysis-board": {
      const input = resolvePath(requireValue(args, "input"));
      const output = resolvePath(requireValue(args, "output"));
      return createAnalysisBoard(input, output);
    }
    case "transform": {
      const recipePath = resolvePath(requireValue(args, "recipe"));
      const recipe = await loadRecipe(recipePath);
      const inputOverride = value(args, "input");
      const outputOverride = value(args, "output");
      const manifestPath = value(args, "manifest");
      return transformRecipe(recipe, {
        recipePath,
        ...(inputOverride ? { inputOverride: resolvePath(inputOverride) } : {}),
        ...(outputOverride ? { outputOverride: resolvePath(outputOverride) } : {}),
        ...(manifestPath ? { manifestPath: resolvePath(manifestPath) } : {}),
      });
    }
    case "preview": {
      const manifestPath = resolvePath(requireValue(args, "manifest"));
      const plan = value(args, "plan");
      const planPath = plan ? resolvePath(plan) : undefined;
      const html = await generatePreview(manifestPath, planPath);
      const output = value(args, "output");
      if (output) {
        const outputPath = resolvePath(output);
        await atomicWriteFile(outputPath, html);
        return { ok: true, command: "preview", manifest: manifestPath, ...(planPath ? { plan: planPath } : {}), output: outputPath, bytes: Buffer.byteLength(html) };
      }
      return html;
    }
    case "validate": {
      const manifestPath = resolvePath(requireValue(args, "manifest"));
      const plan = value(args, "plan");
      const planPath = plan ? resolvePath(plan) : undefined;
      const profileValue = value(args, "profile");
      if (profileValue && profileValue !== "wechat" && profileValue !== "desktop") throw new VisualAssetsError("INVALID_PROFILE", "--profile must be wechat or desktop", { profile: profileValue });
      return validateManifest(manifestPath, profileValue as ValidationProfile | undefined, args.values.final === true, planPath);
    }
    case "init": {
      const manifestPath = resolvePath(requireValue(args, "manifest"));
      const articlePath = requireValue(args, "article");
      const version = requireValue(args, "version");
      return initManifest(manifestPath, articlePath, version);
    }
    case "review": {
      const manifestPath = resolvePath(requireValue(args, "manifest"));
      const plan = value(args, "plan");
      const planPath = plan ? resolvePath(plan) : undefined;
      const approve = value(args, "approve");
      const reject = value(args, "reject");
      if ((approve && reject) || (!approve && !reject)) throw new VisualAssetsError("REVIEW_DECISION_REQUIRED", "review requires exactly one of --approve or --reject");
      const ids = String(approve ?? reject).split(",").map((id) => id.trim()).filter(Boolean);
      return reviewManifest(manifestPath, ids, approve ? "approved" : "rejected", planPath);
    }
    case "rebase": {
      const manifestPath = resolvePath(requireValue(args, "manifest"));
      const planPath = resolvePath(requireValue(args, "plan"));
      const articlePath = requireValue(args, "article");
      const version = requireValue(args, "version");
      return rebaseVisualRun(manifestPath, planPath, articlePath, version);
    }
    default:
      throw new VisualAssetsError("UNKNOWN_COMMAND", `Unknown command: ${args.command}`, { command: args.command });
  }
}

let parsed: Args | undefined;
try {
  parsed = parseArgs(process.argv.slice(2));
} catch (error) {
  const normalized = errorFromUnknown(error);
  const payload = { ok: false, error: { code: normalized.code, message: normalized.message, ...(normalized.details === undefined ? {} : { details: normalized.details }) } };
  process.stderr.write(`${JSON.stringify(payload)}\n`);
  process.exitCode = normalized.exitCode;
}

if (parsed) {
  main(parsed).then((result) => {
    if (parsed?.command === "help" || parsed?.command === "--help" || parsed?.command === "-h") {
      printHuman(result);
    } else if (parsed?.command === "preview" && typeof result === "string") {
      printHuman(result);
    } else {
      printJson(result);
    }
    if (parsed?.command === "validate" && result && typeof result === "object" && "ok" in result && (result as { ok: boolean }).ok === false) process.exitCode = 1;
  }).catch((error: unknown) => {
    const normalized = errorFromUnknown(error);
    const payload = { ok: false, error: { code: normalized.code, message: normalized.message, ...(normalized.details === undefined ? {} : { details: normalized.details }) } };
    process.stderr.write(`${JSON.stringify(payload)}\n`);
    process.exitCode = normalized.exitCode;
  });
}
