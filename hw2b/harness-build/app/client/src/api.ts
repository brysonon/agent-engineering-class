import type { AnswerResponse } from "../../shared/contracts";

export class ApiError extends Error {
  constructor(public readonly code: string, message: string) { super(message); }
}

export async function fetchStatus(): Promise<{ corpusReady: boolean; apiConfigured: boolean }> {
  const response = await fetch("/api/status");
  if (!response.ok) throw new Error("status unavailable");
  return response.json() as Promise<{ corpusReady: boolean; apiConfigured: boolean }>;
}

export async function askConference(question: string): Promise<AnswerResponse> {
  let response: Response;
  try {
    response = await fetch("/api/answer", {
      method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ question })
    });
  } catch {
    throw new ApiError("network_error", "The server could not be reached. Check that npm run dev is running, then try again.");
  }
  const payload = await response.json().catch(() => null) as { code?: string; message?: string } | AnswerResponse | null;
  if (!response.ok) {
    const error = payload as { code?: string; message?: string } | null;
    throw new ApiError(error?.code ?? "server_error", error?.message ?? "The search failed. Please try again.");
  }
  return payload as AnswerResponse;
}
