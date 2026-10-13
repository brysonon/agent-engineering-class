export type EvidenceStatus = "sufficient" | "limited" | "none";

export interface TalkRecord {
  id: string;
  title: string;
  speaker: string;
  role: string | null;
  summary: string | null;
  canonicalUrl: string;
  session: string | null;
  paragraphs: string[];
}

export interface PassageRecord {
  id: string;
  talkId: string;
  text: string;
  paragraphStart: number;
  paragraphEnd: number;
  overlapParagraph: number | null;
  embedding: number[];
}

export interface CorpusIndex {
  schemaVersion: number;
  conference: string;
  embeddingModel: string;
  importedAt: string;
  talks: TalkRecord[];
  passages: PassageRecord[];
}

export interface ConferenceAnswer {
  evidenceStatus: EvidenceStatus;
  answer: string;
  themes: Array<{ title: string; synthesis: string; passageIds: string[] }>;
  closingNote: string;
}

export interface AnswerResponse {
  requestId: string;
  question: string;
  evidenceStatus: EvidenceStatus;
  answer: string;
  themes: Array<{ title: string; synthesis: string; sourceIds: string[] }>;
  closingNote: string;
  usedTalkCount: number;
  sources: Array<{
    id: string;
    speaker: string;
    title: string;
    canonicalUrl: string;
    passages: Array<{
      id: string;
      excerpt?: string;
    }>;
  }>;
}
