export type ErrorCode =
  | "invalid_request" | "corpus_not_imported" | "missing_api_key" | "model_refusal"
  | "model_incomplete" | "provider_timeout" | "synthesis_invalid" | "synthesis_failed"
  | "rate_limited" | "internal_error";

export class AppError extends Error {
  constructor(public readonly code: ErrorCode, public readonly status: number, message: string) {
    super(message);
  }
}

export const safeMessages: Record<ErrorCode, string> = {
  invalid_request: "Enter a question between 1 and 1,000 characters.",
  corpus_not_imported: "The conference corpus is not ready. Run npm run import, then restart the server.",
  missing_api_key: "OpenAI configuration is required. Follow .env.example, then restart the server.",
  model_refusal: "The synthesis service could not answer this request. Try a different conference study question.",
  model_incomplete: "The synthesis service returned an incomplete response. Please try again.",
  provider_timeout: "The synthesis service took too long to respond. Please try again.",
  synthesis_invalid: "The retrieved teachings could not be assembled into a grounded answer. Please try again.",
  synthesis_failed: "The synthesis service is temporarily unavailable. Please try again.",
  rate_limited: "Too many searches were submitted. Wait a few minutes and try again.",
  internal_error: "Conference Compass encountered an unexpected error. Please try again."
};
