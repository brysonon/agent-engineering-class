import { describe, expect, it } from "vitest";
import { chunkTalk, exactExcerpt, selectPassages, validateModelAnswer, type Passage, type Talk } from "../server/core";

const talk = (id: string, paragraphs = ["one two three four five", "six seven eight nine ten", "eleven twelve thirteen fourteen fifteen"]): Talk => ({ id, title: id, speaker: "Speaker", role: "", summary: "", url: `https://www.churchofjesuschrist.org/${id}`, session: "Saturday", paragraphs });

describe("conference core", () => {
  it("chunks in paragraph order with stable IDs", () => {
    const chunks = chunkTalk(talk("alpha"), 5, 9, 1);
    expect(chunks[0].id).toBe("alpha-p0-0");
    expect(chunks[1].paragraphStart).toBe(1);
    expect(chunks.map((chunk) => chunk.text).join(" ")).toContain("one two three");
  });

  it("selects from the full list while limiting one talk", () => {
    const passages: Passage[] = [
      { id: "a1", talkId: "a", text: "", paragraphStart: 0, paragraphEnd: 0, embedding: [1, 0] },
      { id: "a2", talkId: "a", text: "", paragraphStart: 0, paragraphEnd: 0, embedding: [.99, .01] },
      { id: "b1", talkId: "b", text: "", paragraphStart: 0, paragraphEnd: 0, embedding: [.8, .2] },
    ];
    expect(selectPassages(passages, [1, 0], 3, 1).map((item) => item.passage.id)).toEqual(["a1", "b1"]);
  });

  it("removes unknown citations and rejects unsupported themes", () => {
    const answer = { evidenceStatus: "sufficient" as const, answer: "Answer", closingNote: "", themes: [{ title: "Theme", synthesis: "Text", passageIds: ["valid", "fake"] }] };
    expect(validateModelAnswer(answer, new Set(["valid"])).themes[0].passageIds).toEqual(["valid"]);
    expect(() => validateModelAnswer({ ...answer, themes: [{ ...answer.themes[0], passageIds: ["fake"] }] }, new Set(["valid"]))).toThrow();
  });

  it("extracts contiguous excerpts no longer than 24 words", () => {
    const text = `This opening sentence discusses something unrelated. ${Array.from({ length: 40 }, (_, index) => `faithword${index}`).join(" ")}.`;
    const excerpt = exactExcerpt(text, 24, "faithword5 faithword12");
    expect(excerpt.replace("…", "").split(/\s+/)).toHaveLength(24);
    expect(text.includes(excerpt.replace("…", ""))).toBe(true);
    expect(excerpt).toContain("faithword0");
  });
});
