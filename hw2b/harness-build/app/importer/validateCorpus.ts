import type { TalkRecord } from "../shared/contracts.js";
import { EXPECTED_TALK_COUNT, MIN_TALK_WORDS } from "../shared/constants.js";

export function wordCount(text: string): number {
  return text.match(/[\p{L}\p{N}]+(?:[’'][\p{L}\p{N}]+)*/gu)?.length ?? 0;
}

export function validateCorpus(talks: TalkRecord[], expected = EXPECTED_TALK_COUNT): void {
  const errors: string[] = [];
  if (talks.length !== expected) errors.push(`Expected ${expected} talks, received ${talks.length}.`);
  const ids = new Set<string>();
  const urls = new Set<string>();
  for (const talk of talks) {
    if (!talk.id || !talk.title || !talk.speaker || !talk.canonicalUrl || !talk.paragraphs.length) {
      errors.push(`Talk ${talk.id || "(unknown)"} is missing required data.`);
    }
    if (ids.has(talk.id)) errors.push(`Duplicate talk ID: ${talk.id}`);
    ids.add(talk.id);
    if (urls.has(talk.canonicalUrl)) errors.push(`Duplicate canonical URL: ${talk.canonicalUrl}`);
    urls.add(talk.canonicalUrl);
    try {
      const url = new URL(talk.canonicalUrl);
      if (url.protocol !== "https:" || url.hostname !== "www.churchofjesuschrist.org") {
        errors.push(`Talk ${talk.id} has a non-official URL.`);
      }
    } catch {
      errors.push(`Talk ${talk.id} has an invalid canonical URL.`);
    }
    const count = wordCount(talk.paragraphs.join(" "));
    if (count < MIN_TALK_WORDS) errors.push(`Talk ${talk.id} is suspiciously short (${count} words; minimum ${MIN_TALK_WORDS}).`);
  }
  if (errors.length) throw new Error(`Corpus validation failed:\n- ${errors.join("\n- ")}`);
}
