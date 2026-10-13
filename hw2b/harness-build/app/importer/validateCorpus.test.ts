import { describe, expect, it } from "vitest";
import type { TalkRecord } from "../shared/contracts.js";
import { validateCorpus } from "./validateCorpus.js";

function talk(id: string): TalkRecord {
  return { id, title: `Title ${id}`, speaker: "Speaker", role: null, summary: null, canonicalUrl: `https://www.churchofjesuschrist.org/study/general-conference/2026/10/${id}?lang=eng`, session: null, paragraphs: [Array.from({ length: 320 }, (_, index) => `word${index}`).join(" ")] };
}

describe("validateCorpus", () => {
  it("rejects incomplete and duplicated corpora", () => {
    expect(() => validateCorpus([talk("a")], 2)).toThrow(/Expected 2 talks/);
    const duplicate = talk("same");
    expect(() => validateCorpus([duplicate, { ...duplicate }], 2)).toThrow(/Duplicate talk ID.*Duplicate canonical URL/s);
  });

  it("accepts closing-remarks length while rejecting genuinely short bodies", () => {
    const closing = talk("closing");
    closing.paragraphs = [Array.from({ length: 287 }, (_, index) => `word${index}`).join(" ")];
    expect(() => validateCorpus([closing], 1)).not.toThrow();
    closing.paragraphs = [Array.from({ length: 249 }, (_, index) => `word${index}`).join(" ")];
    expect(() => validateCorpus([closing], 1)).toThrow(/suspiciously short/);
  });
});
