import { describe, expect, it } from "vitest";
import type { TalkRecord } from "../shared/contracts.js";
import { chunkTalk } from "./chunk.js";

describe("chunkTalk", () => {
  it("preserves paragraph order and produces stable IDs", () => {
    const paragraphs = Array.from({ length: 12 }, (_, index) => `Paragraph ${index} “curly quote”—${" word".repeat(99)}`);
    const talk: TalkRecord = { id: "talk", title: "Title", speaker: "Speaker", role: null, summary: null, canonicalUrl: "https://www.churchofjesuschrist.org/study/x", session: null, paragraphs };
    const first = chunkTalk(talk);
    const second = chunkTalk(talk);
    expect(first.map((passage) => passage.id)).toEqual(second.map((passage) => passage.id));
    expect(first.length).toBeGreaterThan(1);
    for (const [index, passage] of first.entries()) {
      const textStart = index > 0 ? passage.paragraphStart - 1 : passage.paragraphStart;
      const included = paragraphs.slice(textStart, passage.paragraphEnd + 1);
      expect(passage.text).toBe(included.join("\n\n"));
      expect(passage.text.split(/\s+/u).length).toBeGreaterThanOrEqual(350);
      expect(passage.overlapParagraph).toBe(index > 0 ? passage.paragraphStart - 1 : null);
    }
    expect(first.at(-1)?.paragraphEnd).toBe(paragraphs.length - 1);
  });
});
