import { describe, expect, it } from "vitest";
import { containsDirectQuoteMarkers, validateSynthesis } from "./validation.js";

const base = { answer: "Supported answer", closingNote: "Read the talks in context." };

describe("validateSynthesis", () => {
  it("rejects unknown and non-retrieved citations", () => {
    expect(() => validateSynthesis({ ...base, evidenceStatus: "limited", themes: [{ title: "Theme", synthesis: "Claim", passageIds: ["unknown"] }] }, new Set(["known"]))).toThrow();
  });

  it("prevents no-evidence output from carrying unsupported themes", () => {
    expect(() => validateSynthesis({ ...base, evidenceStatus: "none", themes: [{ title: "Theme", synthesis: "Claim", passageIds: ["known"] }] }, new Set(["known"]))).toThrow();
    expect(validateSynthesis({ ...base, evidenceStatus: "none", themes: [] }, new Set()).themes).toEqual([]);
  });

  it.each([
    { field: "answer", value: "A leader taught, “We are against it.”" },
    { field: "closingNote", value: "Remember: \"We are against it.\"" }
  ])("rejects direct quotation markers in model-owned $field text", ({ field, value }) => {
    const candidate = { ...base, evidenceStatus: "limited", themes: [{ title: "Theme", synthesis: "A paraphrased claim.", passageIds: ["known"] }], [field]: value };
    expect(() => validateSynthesis(candidate, new Set(["known"]))).toThrow();
  });

  it("rejects quote markers in theme titles and synthesis while allowing contractions", () => {
    const answer = { ...base, evidenceStatus: "limited", themes: [{ title: "‘Official phrase’", synthesis: "A paraphrased claim.", passageIds: ["known"] }] };
    expect(() => validateSynthesis(answer, new Set(["known"]))).toThrow();
    answer.themes[0]!.title = "Wise choices";
    answer.themes[0]!.synthesis = "Leaders said 'we are against it.'";
    expect(() => validateSynthesis(answer, new Set(["known"]))).toThrow();
    expect(containsDirectQuoteMarkers("Disciples don't need to lose hope.")).toBe(false);
  });
});
