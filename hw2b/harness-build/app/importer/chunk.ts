import { createHash } from "node:crypto";
import type { PassageRecord, TalkRecord } from "../shared/contracts.js";
import { wordCount } from "./validateCorpus.js";

const TARGET_WORDS = 500;
const MIN_WORDS = 350;
const MAX_WORDS = 650;

export type PassageWithoutEmbedding = Omit<PassageRecord, "embedding">;

export function chunkTalk(talk: TalkRecord): PassageWithoutEmbedding[] {
  const segments: Array<{ start: number; end: number }> = [];
  const paragraphWords = talk.paragraphs.map(wordCount);
  const totalWords = paragraphWords.reduce((sum, count) => sum + count, 0);
  let segmentsLeft = Math.max(1, Math.min(
    Math.floor(totalWords / MIN_WORDS),
    Math.max(Math.ceil(totalWords / MAX_WORDS), Math.round(totalWords / TARGET_WORDS))
  ));
  let start = 0;
  while (start < talk.paragraphs.length) {
    const remaining = paragraphWords.slice(start).reduce((sum, count) => sum + count, 0);
    if (segmentsLeft <= 1) {
      segments.push({ start, end: talk.paragraphs.length });
      break;
    }
    const target = remaining / segmentsLeft;
    let running = 0;
    let bestEnd = -1;
    let bestDistance = Number.POSITIVE_INFINITY;
    for (let end = start + 1; end < talk.paragraphs.length; end += 1) {
      running += paragraphWords[end - 1] ?? 0;
      const after = remaining - running;
      if (running >= MIN_WORDS && running <= MAX_WORDS && after >= MIN_WORDS * (segmentsLeft - 1)) {
        const distance = Math.abs(target - running);
        if (distance < bestDistance) { bestEnd = end; bestDistance = distance; }
      }
      if (running > MAX_WORDS) break;
    }
    if (bestEnd < 0) {
      bestEnd = start + 1;
      while (bestEnd < talk.paragraphs.length && paragraphWords.slice(start, bestEnd).reduce((sum, count) => sum + count, 0) < TARGET_WORDS) bestEnd += 1;
    }
    segments.push({ start, end: bestEnd });
    start = bestEnd;
    segmentsLeft -= 1;
  }

  return segments.map((segment, index) => {
    const overlap = index > 0 ? segment.start - 1 : null;
    const textStart = overlap ?? segment.start;
    const text = talk.paragraphs.slice(textStart, segment.end).join("\n\n");
    const hash = createHash("sha256").update(text).digest("hex").slice(0, 8);
    return {
      id: `${talk.id}:p${segment.start}-${segment.end - 1}:${hash}`,
      talkId: talk.id,
      text,
      paragraphStart: segment.start,
      paragraphEnd: segment.end - 1,
      overlapParagraph: overlap
    };
  });
}
