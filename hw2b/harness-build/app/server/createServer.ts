import { randomUUID } from "node:crypto";
import path from "node:path";
import express, { type Request, type Response } from "express";
import rateLimit from "express-rate-limit";
import { MAX_QUESTION_CODEPOINTS, EXPECTED_TALK_COUNT } from "../shared/constants.js";
import type { AnswerResponse } from "../shared/contracts.js";
import { AppError, safeMessages, type ErrorCode } from "./errors.js";

export interface ServerDependencies {
  corpusReady: () => boolean;
  apiKeyReady: () => boolean;
  answer: (question: string, requestId: string) => Promise<AnswerResponse>;
  production?: boolean;
}

export function validateQuestion(value: unknown): string {
  if (typeof value !== "string") throw new AppError("invalid_request", 400, safeMessages.invalid_request);
  const question = value.trim();
  if (!question || [...question].length > MAX_QUESTION_CODEPOINTS) {
    throw new AppError("invalid_request", 400, safeMessages.invalid_request);
  }
  return question;
}

export function createServer(dependencies: ServerDependencies) {
  const app = express();
  app.disable("x-powered-by");
  app.use(express.json({ limit: "16kb", type: "application/json" }));
  const limiter = rateLimit({
    windowMs: 15 * 60_000, limit: 20, standardHeaders: true, legacyHeaders: false,
    handler: (_request, response) => response.status(429).json({ requestId: randomUUID(), code: "rate_limited", message: safeMessages.rate_limited })
  });

  app.get("/api/status", (_request, response) => {
    response.json({ corpusReady: dependencies.corpusReady(), apiConfigured: dependencies.apiKeyReady(), conference: "October 2026", talkCount: dependencies.corpusReady() ? EXPECTED_TALK_COUNT : 0 });
  });

  app.post("/api/answer", limiter, async (request: Request, response: Response) => {
    const requestId = randomUUID();
    const started = Date.now();
    try {
      if (!request.is("application/json")) throw new AppError("invalid_request", 400, safeMessages.invalid_request);
      const body = request.body as Record<string, unknown> | undefined;
      if (!body || Object.keys(body).some((key) => key !== "question")) throw new AppError("invalid_request", 400, safeMessages.invalid_request);
      const question = validateQuestion(body.question);
      if (!dependencies.corpusReady()) throw new AppError("corpus_not_imported", 503, safeMessages.corpus_not_imported);
      if (!dependencies.apiKeyReady()) throw new AppError("missing_api_key", 503, safeMessages.missing_api_key);
      const result = await dependencies.answer(question, requestId);
      console.info(JSON.stringify({ requestId, status: 200, questionLength: [...question].length, durationMs: Date.now() - started }));
      response.json(result);
    } catch (error) {
      const appError = error instanceof AppError ? error : new AppError("internal_error", 500, safeMessages.internal_error);
      console.error(JSON.stringify({ requestId, status: appError.status, code: appError.code, durationMs: Date.now() - started }));
      response.status(appError.status).json({ requestId, code: appError.code satisfies ErrorCode, message: appError.message });
    }
  });

  app.use((error: unknown, _request: Request, response: Response, _next: express.NextFunction) => {
    const requestId = randomUUID();
    const status = typeof error === "object" && error && "status" in error && error.status === 413 ? 413 : 400;
    response.status(status).json({ requestId, code: "invalid_request", message: safeMessages.invalid_request });
  });

  if (dependencies.production) {
    const clientDirectory = path.resolve("dist", "client");
    app.use(express.static(clientDirectory));
    app.get("/*splat", (_request, response) => response.sendFile(path.join(clientDirectory, "index.html")));
  }
  return app;
}
