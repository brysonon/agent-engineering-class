import { readFile } from "node:fs/promises";
import path from "node:path";
import { z } from "zod";
import type { CorpusIndex, PassageRecord, TalkRecord } from "../shared/contracts.js";
import { CACHE_SCHEMA_VERSION, EXPECTED_TALK_COUNT } from "../shared/constants.js";

const TalkSchema = z.object({
  id: z.string().min(1), title: z.string().min(1), speaker: z.string().min(1),
  role: z.string().nullable(), summary: z.string().nullable(), canonicalUrl: z.string().url(),
  session: z.string().nullable(), paragraphs: z.array(z.string().min(1)).min(1)
});
const PassageSchema = z.object({
  id: z.string().min(1), talkId: z.string().min(1), text: z.string().min(1),
  paragraphStart: z.number().int().nonnegative(), paragraphEnd: z.number().int().nonnegative(),
  overlapParagraph: z.number().int().nonnegative().nullable(),
  embedding: z.array(z.number().finite()).min(1)
});
const IndexSchema = z.object({
  schemaVersion: z.literal(CACHE_SCHEMA_VERSION), conference: z.string(), embeddingModel: z.string().min(1),
  importedAt: z.string(), talks: z.array(TalkSchema).length(EXPECTED_TALK_COUNT), passages: z.array(PassageSchema).min(1)
});

export class CorpusStore {
  private index: CorpusIndex | null = null;
  private talks = new Map<string, TalkRecord>();
  private passages = new Map<string, PassageRecord>();

  constructor(private readonly cacheRoot: string) {}

  async load(): Promise<boolean> {
    try {
      const pointer = JSON.parse(await readFile(path.join(this.cacheRoot, "active.json"), "utf8")) as { version?: string };
      if (!pointer.version || !/^[a-zA-Z0-9-]+$/.test(pointer.version)) return false;
      const parsed = IndexSchema.parse(JSON.parse(await readFile(path.join(this.cacheRoot, "indexes", pointer.version, "index.json"), "utf8")));
      const talkIds = new Set(parsed.talks.map((talk) => talk.id));
      if (parsed.passages.some((passage) => !talkIds.has(passage.talkId))) return false;
      this.index = parsed;
      this.talks = new Map(parsed.talks.map((talk) => [talk.id, talk]));
      this.passages = new Map(parsed.passages.map((passage) => [passage.id, passage]));
      return true;
    } catch {
      return false;
    }
  }

  get ready(): boolean { return this.index !== null; }
  get embeddingModel(): string | null { return this.index?.embeddingModel ?? null; }
  get allPassages(): PassageRecord[] { return this.index?.passages ?? []; }
  getTalk(id: string): TalkRecord | undefined { return this.talks.get(id); }
  getPassage(id: string): PassageRecord | undefined { return this.passages.get(id); }
}
