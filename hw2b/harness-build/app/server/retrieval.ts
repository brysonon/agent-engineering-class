import type { PassageRecord } from "../shared/contracts.js";
import { MAX_PASSAGES_PER_TALK, RETRIEVAL_POOL, RETRIEVAL_TARGET } from "../shared/constants.js";

export interface RetrievedPassage extends PassageRecord { score: number }

export function cosineSimilarity(a: number[], b: number[]): number {
  if (a.length !== b.length || !a.length) return Number.NEGATIVE_INFINITY;
  let dot = 0, aa = 0, bb = 0;
  for (let i = 0; i < a.length; i += 1) {
    const av = a[i] ?? 0, bv = b[i] ?? 0;
    dot += av * bv; aa += av * av; bb += bv * bv;
  }
  return aa && bb ? dot / Math.sqrt(aa * bb) : Number.NEGATIVE_INFINITY;
}

export function retrieve(passages: PassageRecord[], queryVector: number[]): { passages: RetrievedPassage[]; scoredCount: number } {
  const ranked = passages.map((passage) => ({ ...passage, score: cosineSimilarity(passage.embedding, queryVector) }))
    .sort((a, b) => b.score - a.score || a.id.localeCompare(b.id))
    .slice(0, RETRIEVAL_POOL);
  const counts = new Map<string, number>();
  const selected: RetrievedPassage[] = [];
  for (const passage of ranked) {
    if ((counts.get(passage.talkId) ?? 0) >= MAX_PASSAGES_PER_TALK) continue;
    selected.push(passage);
    counts.set(passage.talkId, (counts.get(passage.talkId) ?? 0) + 1);
    if (selected.length === RETRIEVAL_TARGET) break;
  }
  return { passages: selected, scoredCount: passages.length };
}
