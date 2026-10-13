import { MAX_EXCERPT_WORDS } from "../shared/constants.js";

const WORD = /[\p{L}\p{N}]+(?:[’'][\p{L}\p{N}]+)*/gu;
const STOP = new Set(["a","an","and","are","as","at","be","by","for","from","how","i","in","is","it","of","on","or","that","the","this","to","was","what","with"]);

function terms(text: string): Set<string> {
  return new Set((text.toLocaleLowerCase().match(WORD) ?? []).filter((word) => !STOP.has(word)));
}

export function countExcerptWords(text: string): number { return text.match(WORD)?.length ?? 0; }

export function extractExcerpt(passage: string, context: string): string | undefined {
  const wanted = terms(context);
  if (!wanted.size) return undefined;
  const sentenceMatches = [...passage.matchAll(/[^.!?]+[.!?]+|[^.!?]+$/gu)];
  let best: { text: string; score: number } | undefined;
  for (const sentenceMatch of sentenceMatches) {
    const sentence = sentenceMatch[0].trim();
    const words = [...sentence.matchAll(WORD)];
    if (!words.length) continue;
    const scoreWindow = (value: string) => [...terms(value)].filter((term) => wanted.has(term)).length;
    if (words.length <= MAX_EXCERPT_WORDS) {
      const score = scoreWindow(sentence);
      if (score > (best?.score ?? 0)) best = { text: sentence, score };
      continue;
    }
    for (let start = 0; start <= words.length - MAX_EXCERPT_WORDS; start += 1) {
      const first = words[start], last = words[start + MAX_EXCERPT_WORDS - 1];
      if (!first || !last || first.index === undefined || last.index === undefined) continue;
      const end = last.index + last[0].length;
      const candidate = sentence.slice(first.index, end);
      const score = scoreWindow(candidate);
      if (score > (best?.score ?? 0)) best = { text: candidate, score };
    }
  }
  if (!best || best.score < 1 || !passage.includes(best.text) || countExcerptWords(best.text) > MAX_EXCERPT_WORDS) return undefined;
  return best.text;
}
