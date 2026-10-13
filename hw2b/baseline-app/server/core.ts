export type Talk = {
  id: string;
  title: string;
  speaker: string;
  role: string;
  summary: string;
  url: string;
  session: string;
  paragraphs: string[];
};

export type Passage = {
  id: string;
  talkId: string;
  text: string;
  paragraphStart: number;
  paragraphEnd: number;
  embedding: number[];
};

export type ModelAnswer = {
  evidenceStatus: "sufficient" | "limited" | "none";
  answer: string;
  themes: Array<{ title: string; synthesis: string; passageIds: string[] }>;
  closingNote: string;
};

const words = (value: string) => value.trim().split(/\s+/).filter(Boolean);

export function chunkTalk(talk: Talk, minWords = 350, maxWords = 650, overlapParagraphs = 1): Omit<Passage, "embedding">[] {
  const result: Omit<Passage, "embedding">[] = [];
  let start = 0;
  while (start < talk.paragraphs.length) {
    let end = start;
    let count = 0;
    while (end < talk.paragraphs.length) {
      const next = words(talk.paragraphs[end]).length;
      if (count >= minWords && count + next > maxWords) break;
      count += next;
      end += 1;
      if (count >= maxWords) break;
    }
    if (end === start) end += 1;
    const paragraphEnd = end - 1;
    result.push({
      id: `${talk.id}-p${start}-${paragraphEnd}`,
      talkId: talk.id,
      text: talk.paragraphs.slice(start, end).join("\n\n"),
      paragraphStart: start,
      paragraphEnd,
    });
    if (end >= talk.paragraphs.length) break;
    start = Math.max(start + 1, end - overlapParagraphs);
  }
  return result;
}

export function cosine(a: number[], b: number[]) {
  if (a.length !== b.length || a.length === 0) return -1;
  let dot = 0;
  let left = 0;
  let right = 0;
  for (let index = 0; index < a.length; index += 1) {
    dot += a[index] * b[index];
    left += a[index] ** 2;
    right += b[index] ** 2;
  }
  return left && right ? dot / Math.sqrt(left * right) : -1;
}

export function selectPassages(passages: Passage[], queryEmbedding: number[], limit = 16, perTalk = 2) {
  const counts = new Map<string, number>();
  return passages
    .map((passage) => ({ passage, score: cosine(passage.embedding, queryEmbedding) }))
    .sort((a, b) => b.score - a.score)
    .filter(({ passage }) => {
      const count = counts.get(passage.talkId) ?? 0;
      if (count >= perTalk) return false;
      counts.set(passage.talkId, count + 1);
      return true;
    })
    .slice(0, limit);
}

export function validateModelAnswer(answer: ModelAnswer, allowedIds: Set<string>): ModelAnswer {
  const themes = answer.themes
    .map((theme) => ({ ...theme, passageIds: [...new Set(theme.passageIds.filter((id) => allowedIds.has(id)))] }))
    .filter((theme) => theme.passageIds.length > 0);
  if (answer.evidenceStatus === "none") return { ...answer, themes: [], answer: answer.answer.trim() };
  if (!themes.length) throw new Error("The model returned no valid citations.");
  return { ...answer, themes, answer: answer.answer.trim() };
}

const excerptStopWords = new Set(["about", "after", "again", "also", "and", "are", "because", "been", "being", "but", "can", "did", "does", "for", "from", "had", "has", "have", "how", "into", "its", "may", "more", "not", "our", "should", "that", "the", "their", "them", "there", "these", "they", "this", "through", "was", "were", "what", "when", "where", "which", "who", "will", "with", "would", "you", "your"]);

const terms = (value: string) => new Set(value.toLowerCase().match(/[a-z’']{3,}/g)?.filter((term) => !excerptStopWords.has(term)) ?? []);

export function exactExcerpt(text: string, maxWords = 24, focus = "") {
  const normalized = text.replace(/\s+/g, " ").trim();
  const focusTerms = terms(focus);
  const candidates = normalized.split(/(?<=[.!?])\s+(?=[A-Z“‘])/).filter((sentence) => {
    const wordCount = sentence.split(/\s+/).length;
    return wordCount >= 5 && !/^(By |See |Notes\b|\d+[.:])/.test(sentence);
  });
  const sentence = candidates
    .map((candidate, index) => ({ candidate, index, score: [...terms(candidate)].filter((term) => focusTerms.has(term)).length }))
    .sort((left, right) => right.score - left.score || left.index - right.index)[0]?.candidate ?? normalized;
  const tokens = sentence.split(/\s+/).filter(Boolean);
  if (tokens.length <= maxWords) return sentence;
  return `${tokens.slice(0, maxWords).join(" ").replace(/[,:;—-]+$/, "")}…`;
}
