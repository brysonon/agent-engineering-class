import { describe, expect, it, vi } from "vitest";
import request from "supertest";
import type { AnswerResponse } from "../shared/contracts.js";
import { createServer } from "./createServer.js";

const answer: AnswerResponse = { requestId: "r", question: "Faith?", evidenceStatus: "none", answer: "The corpus does not directly address this question.", themes: [], closingNote: "Try another topic.", usedTalkCount: 0, sources: [] };

describe("answer API", () => {
  it("returns safe, typed errors without serializing secrets", async () => {
    const sentinel = "sk-test-super-secret";
    const app = createServer({ corpusReady: () => true, apiKeyReady: () => false, answer: vi.fn() });
    const response = await request(app).post("/api/answer").set("content-type", "application/json").send({ question: "Faith?", extra: sentinel });
    expect(response.status).toBe(400);
    expect(JSON.stringify(response.body)).not.toContain(sentinel);
    expect(JSON.stringify(response.body)).not.toContain("OPENAI_API_KEY");
  });

  it("trims a valid question and returns the service DTO", async () => {
    const handler = vi.fn(async (question: string) => ({ ...answer, question }));
    const app = createServer({ corpusReady: () => true, apiKeyReady: () => true, answer: handler });
    const response = await request(app).post("/api/answer").set("content-type", "application/json").send({ question: "  Faith?  " });
    expect(response.status).toBe(200);
    expect(handler).toHaveBeenCalledWith("Faith?", expect.any(String));
    expect(response.body.question).toBe("Faith?");
  });

  it("returns JSON without a stack for malformed and oversized request bodies", async () => {
    const app = createServer({ corpusReady: () => true, apiKeyReady: () => true, answer: vi.fn() });
    const malformed = await request(app).post("/api/answer").set("content-type", "application/json").send("{");
    expect(malformed.status).toBe(400);
    expect(malformed.body.code).toBe("invalid_request");
    expect(JSON.stringify(malformed.body)).not.toContain("SyntaxError");
    const oversized = await request(app).post("/api/answer").set("content-type", "application/json").send(JSON.stringify({ question: "x".repeat(20_000) }));
    expect(oversized.status).toBe(413);
    expect(oversized.body.code).toBe("invalid_request");
  });
});
