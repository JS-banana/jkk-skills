export type ErrorDetails = Record<string, unknown> | unknown[] | string | number | boolean | null;

/** Stable, machine-readable failures emitted by the CLI. */
export class VisualAssetsError extends Error {
  readonly code: string;
  readonly details?: ErrorDetails;
  readonly exitCode: number;

  constructor(code: string, message: string, details?: ErrorDetails, exitCode = 1) {
    super(message);
    this.name = "VisualAssetsError";
    this.code = code;
    this.details = details;
    this.exitCode = exitCode;
  }
}

export function errorFromUnknown(error: unknown, fallbackCode = "INTERNAL_ERROR"): VisualAssetsError {
  if (error instanceof VisualAssetsError) return error;
  if (error instanceof Error) {
    return new VisualAssetsError(fallbackCode, error.message);
  }
  return new VisualAssetsError(fallbackCode, String(error));
}

export function assertCondition(
  condition: unknown,
  code: string,
  message: string,
  details?: ErrorDetails,
): asserts condition {
  if (!condition) throw new VisualAssetsError(code, message, details);
}
