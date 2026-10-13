import { z } from "zod";
import type { ConferenceAnswer } from "../shared/contracts.js";
import { AppError, safeMessages } from "./errors.js";

export const ConferenceAnswerSchema = z.object({
  evidenceStatus: z.enum(["sufficient", "limited", "none"]),
  answer: z.string().trim().min(1).max(4000),
  themes: z.array(z.object({
    title: z.string().trim().min(1).max(160),
    synthesis: z.string().trim().min(1).max(2000),
    passageIds: z.array(z.string().min(1)).min(1).max(8)
  }).strict()).max(5),
  closingNote: z.string().trim().min(1).max(1000)
}).strict();

// Double quotation marks and opening single quotation marks indicate purported
// source wording. Apostrophes inside ordinary contractions remain allowed.
const DIRECT_QUOTE_MARKER = /["“”„‟«»‹›‘]/u;
const PAIRED_STRAIGHT_SINGLE_QUOTES = /(?:^|[\s([{])'[^'\n]{2,}'(?=$|[\s.,;:!?)}\]])/u;

export function containsDirectQuoteMarkers(text: string): boolean {
  return DIRECT_QUOTE_MARKER.test(text) || PAIRED_STRAIGHT_SINGLE_QUOTES.test(text);
}

export function validateSynthesis(value: unknown, retrievedIds: Set<string>): ConferenceAnswer {
  const result = ConferenceAnswerSchema.safeParse(value);
  if (!result.success) throw new AppError("synthesis_invalid", 502, safeMessages.synthesis_invalid);
  const answer = result.data;
  if (answer.evidenceStatus === "sufficient" && (answer.themes.length < 2 || answer.themes.length > 5)) {
    throw new AppError("synthesis_invalid", 502, safeMessages.synthesis_invalid);
  }
  if (answer.evidenceStatus === "limited" && (answer.themes.length < 1 || answer.themes.length > 5)) {
    throw new AppError("synthesis_invalid", 502, safeMessages.synthesis_invalid);
  }
  if (answer.evidenceStatus === "none" && answer.themes.length !== 0) {
    throw new AppError("synthesis_invalid", 502, safeMessages.synthesis_invalid);
  }
  const modelText = [answer.answer, answer.closingNote, ...answer.themes.flatMap((theme) => [theme.title, theme.synthesis])];
  if (modelText.some(containsDirectQuoteMarkers)) {
    throw new AppError("synthesis_invalid", 502, safeMessages.synthesis_invalid);
  }
  for (const theme of answer.themes) {
    const unique = new Set(theme.passageIds);
    if (unique.size !== theme.passageIds.length || theme.passageIds.some((id) => !retrievedIds.has(id))) {
      throw new AppError("synthesis_invalid", 502, safeMessages.synthesis_invalid);
    }
  }
  return answer;
}

export const CONFERENCE_ANSWER_JSON_SCHEMA = {
  type: "object",
  additionalProperties: false,
  required: ["evidenceStatus", "answer", "themes", "closingNote"],
  properties: {
    evidenceStatus: { type: "string", enum: ["sufficient", "limited", "none"] },
    answer: { type: "string" },
    themes: {
      type: "array", maxItems: 5,
      items: {
        type: "object", additionalProperties: false,
        required: ["title", "synthesis", "passageIds"],
        properties: {
          title: { type: "string" }, synthesis: { type: "string" },
          passageIds: { type: "array", minItems: 1, items: { type: "string" } }
        }
      }
    },
    closingNote: { type: "string" }
  }
} as const;
