import type OpenAI from "openai";
import { describe, expect, it, vi } from "vitest";
import type { TalkRecord } from "../shared/contracts.js";
import { Synthesizer, type EvidencePassage } from "./synthesis.js";

const talk: TalkRecord = {
  id: "talk-1", title: "O Be Wise", speaker: "A Speaker", role: null, summary: null,
  canonicalUrl: "https://www.churchofjesuschrist.org/study/general-conference/2026/10/example?lang=eng",
  session: "Sunday Afternoon Session", paragraphs: ["Source text"]
};
const evidence: EvidencePassage[] = [{
  id: "passage-1", talkId: talk.id, text: "The source opposes gambling and explains its harms.",
  paragraphStart: 0, paragraphEnd: 0, overlapParagraph: null, embedding: [1], score: 1, talk
}];

function response(output: unknown) {
  return { status: "completed", output: [], output_text: JSON.stringify(output) };
}

describe("Synthesizer", () => {
  it("retries a structured response containing a model-authored direct quotation", async () => {
    const create = vi.fn()
      .mockResolvedValueOnce(response({
        evidenceStatus: "limited", answer: "The talk directly opposes gambling.",
        themes: [{ title: "Opposition", synthesis: "The speaker said, “We are against it.”", passageIds: ["passage-1"] }],
        closingNote: "Read the talk in context."
      }))
      .mockResolvedValueOnce(response({
        evidenceStatus: "limited", answer: "The talk directly opposes gambling.",
        themes: [{ title: "Opposition", synthesis: "The speaker opposes gambling and describes its harms.", passageIds: ["passage-1"] }],
        closingNote: "Read the talk in context."
      }));
    const client = { responses: { create } } as unknown as OpenAI;
    const result = await new Synthesizer("unused", "gpt-5-mini", client).synthesize("What was said about gambling?", evidence);
    expect(create).toHaveBeenCalledTimes(2);
    expect(String(create.mock.calls[1]?.[0]?.input)).toContain("did not satisfy the strict grounding contract");
    expect(result.themes[0]?.synthesis).toBe("The speaker opposes gambling and describes its harms.");
  });
});
