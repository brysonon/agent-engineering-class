import { describe, expect, it } from "vitest";
import type { PassageRecord } from "../shared/contracts.js";
import { retrieve } from "./retrieval.js";

describe("retrieve", () => {
  it("scores the full index and limits each talk to two passages", () => {
    const passages: PassageRecord[] = Array.from({ length: 40 }, (_, index) => ({
      id: `p${index}`, talkId: index < 20 ? "dominant" : `talk-${index}`,
      text: "text", paragraphStart: 0, paragraphEnd: 0, overlapParagraph: null,
      embedding: index < 20 ? [1, 0] : [1, index / 1000]
    }));
    const result = retrieve(passages, [1, 0]);
    expect(result.scoredCount).toBe(40);
    expect(result.passages).toHaveLength(16);
    expect(result.passages.filter((passage) => passage.talkId === "dominant")).toHaveLength(2);
  });
});
