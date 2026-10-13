import { describe, expect, it } from "vitest";
import { countExcerptWords, extractExcerpt } from "./excerpts.js";

describe("extractExcerpt", () => {
  it("returns an exact contiguous source substring no longer than 24 words", () => {
    const passage = "A brief opening sentence. Faith during difficult trials can become a steady source of courage when disciples remember Jesus Christ and continue forward with hope, patience, humility, prayer, love, service, and trust in God’s promises. Another sentence.";
    const excerpt = extractExcerpt(passage, "faith trials courage");
    expect(excerpt).toBeDefined();
    expect(passage.includes(excerpt!)).toBe(true);
    expect(countExcerptWords(excerpt!)).toBeLessThanOrEqual(24);
  });

  it("omits a quote when the context has no useful lexical overlap", () => {
    expect(extractExcerpt("Faith grows through prayer.", "quantum mechanics")).toBeUndefined();
  });
});
