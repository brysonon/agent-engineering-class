import OpenAI from "openai";
import type { AnswerResponse } from "../shared/contracts.js";
import { AppError, safeMessages } from "./errors.js";
import { extractExcerpt } from "./excerpts.js";
import { CorpusStore } from "./corpusStore.js";
import { retrieve } from "./retrieval.js";
import { Synthesizer, type EvidencePassage } from "./synthesis.js";

export function assembleGroupedSources(
  citedIds: string[],
  evidenceById: Map<string, EvidencePassage>,
  contexts: Map<string, string>,
  question: string
): AnswerResponse["sources"] {
  const groups = new Map<string, AnswerResponse["sources"][number]>();
  for (const id of citedIds) {
    const passage = evidenceById.get(id);
    if (!passage) throw new AppError("synthesis_invalid", 502, safeMessages.synthesis_invalid);
    const excerpt = extractExcerpt(passage.text, contexts.get(id) ?? question);
    const key = passage.talk.canonicalUrl;
    let group = groups.get(key);
    if (!group) {
      group = {
        id: passage.talk.id,
        speaker: passage.talk.speaker,
        title: passage.talk.title,
        canonicalUrl: passage.talk.canonicalUrl,
        passages: []
      };
      groups.set(key, group);
    }
    group.passages.push({ id, ...(excerpt ? { excerpt } : {}) });
  }
  return [...groups.values()];
}

export class AnswerService {
  private readonly openai: OpenAI;
  private readonly synthesizer: Synthesizer;
  constructor(
    private readonly store: CorpusStore,
    apiKey: string,
    private readonly embeddingModel: string,
    synthesisModel: string
  ) {
    this.openai = new OpenAI({ apiKey, timeout: 45_000, maxRetries: 1 });
    this.synthesizer = new Synthesizer(apiKey, synthesisModel);
  }

  async answer(question: string, requestId: string): Promise<AnswerResponse> {
    if (this.store.embeddingModel !== this.embeddingModel) {
      throw new AppError("corpus_not_imported", 503, "The corpus model configuration changed. Run npm run import again.");
    }
    let embedding: number[];
    try {
      const result = await this.openai.embeddings.create({ model: this.embeddingModel, input: question });
      embedding = result.data[0]?.embedding ?? [];
      if (!embedding.length) throw new Error("empty embedding");
    } catch (error) {
      const name = error instanceof Error ? error.name : "";
      if (/timeout|abort/i.test(name)) throw new AppError("provider_timeout", 504, safeMessages.provider_timeout);
      throw new AppError("synthesis_failed", 502, safeMessages.synthesis_failed);
    }
    const retrieval = retrieve(this.store.allPassages, embedding);
    if (retrieval.scoredCount !== this.store.allPassages.length || !retrieval.passages.length) {
      throw new AppError("synthesis_failed", 502, safeMessages.synthesis_failed);
    }
    const evidence: EvidencePassage[] = retrieval.passages.map((passage) => {
      const talk = this.store.getTalk(passage.talkId);
      if (!talk) throw new AppError("corpus_not_imported", 503, safeMessages.corpus_not_imported);
      return { ...passage, talk };
    });
    const answer = await this.synthesizer.synthesize(question, evidence);
    const answerText = answer.evidenceStatus === "none"
      ? "The October 2026 general conference corpus does not directly address this question."
      : answer.answer;
    const closingNote = answer.evidenceStatus === "none"
      ? "Try one of the example conference questions to explore another topic."
      : answer.closingNote;
    const byId = new Map(evidence.map((passage) => [passage.id, passage]));
    const contexts = new Map<string, string>();
    for (const theme of answer.themes) {
      for (const id of theme.passageIds) {
        contexts.set(id, `${question} ${theme.title} ${theme.synthesis}`);
      }
    }
    const citedIds = [...new Set(answer.themes.flatMap((theme) => theme.passageIds))];
    const sources = assembleGroupedSources(citedIds, byId, contexts, question);
    const usedTalkCount = sources.length;
    return {
      requestId, question, evidenceStatus: answer.evidenceStatus, answer: answerText,
      themes: answer.themes.map((theme) => ({ title: theme.title, synthesis: theme.synthesis, sourceIds: theme.passageIds })),
      closingNote, usedTalkCount, sources
    };
  }
}
