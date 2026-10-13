import { describe, expect, it } from "vitest";
import type { TalkRecord } from "../shared/contracts.js";
import { assembleGroupedSources } from "./answerService.js";
import type { EvidencePassage } from "./synthesis.js";

describe("assembleGroupedSources", () => {
  it("groups two cited passages into one talk card with distinct exact excerpts", () => {
    const talk: TalkRecord = {
      id: "talk-1", title: "One Talk", speaker: "One Speaker", role: null, summary: null,
      canonicalUrl: "https://www.churchofjesuschrist.org/study/general-conference/2026/10/one?lang=eng",
      session: null, paragraphs: []
    };
    const evidence = new Map<string, EvidencePassage>([
      ["p1", { id: "p1", talkId: talk.id, text: "Faith gives courage during difficult trials.", paragraphStart: 0, paragraphEnd: 0, overlapParagraph: null, embedding: [1], score: 1, talk }],
      ["p2", { id: "p2", talkId: talk.id, text: "Hope helps disciples continue with patience.", paragraphStart: 1, paragraphEnd: 1, overlapParagraph: null, embedding: [1], score: .9, talk }]
    ]);
    const contexts = new Map([["p1", "faith courage"], ["p2", "hope patience"]]);
    const sources = assembleGroupedSources(["p1", "p2"], evidence, contexts, "faith and hope");
    expect(sources).toHaveLength(1);
    expect(sources[0]?.passages).toHaveLength(2);
    expect(sources[0]?.passages.map((passage) => passage.id)).toEqual(["p1", "p2"]);
    expect(sources[0]?.passages.every((passage) => passage.excerpt && evidence.get(passage.id)?.text.includes(passage.excerpt))).toBe(true);
    expect(sources.length).toBe(1); // the coverage count is derived from rendered groups
  });
});
