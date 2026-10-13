import dotenv from "dotenv";
import express from "express";
import { readFile } from "node:fs/promises";
import path from "node:path";
import OpenAI from "openai";
import { z } from "zod";
import { exactExcerpt, selectPassages, validateModelAnswer, type ModelAnswer, type Passage, type Talk } from "./core.js";

dotenv.config();
dotenv.config({ path: path.resolve("../../.env"), override: false });

const app = express();
app.disable("x-powered-by");
app.use(express.json({ limit: "8kb" }));

const questionSchema = z.object({ question: z.string().trim().min(3).max(500) });
const answerSchema = z.object({
  evidenceStatus: z.enum(["sufficient", "limited", "none"]),
  answer: z.string(),
  themes: z.array(z.object({ title: z.string(), synthesis: z.string(), passageIds: z.array(z.string()) })).max(5),
  closingNote: z.string(),
});

let talks: Talk[] = [];
let passages: Passage[] = [];
let corpusError = "";
try {
  [talks, passages] = await Promise.all([
    readFile(path.resolve(".cache/talks.json"), "utf8").then(JSON.parse),
    readFile(path.resolve(".cache/passages.json"), "utf8").then(JSON.parse),
  ]);
  if (talks.length !== 37 || !passages.length) throw new Error("The index is incomplete.");
} catch (error) {
  corpusError = error instanceof Error ? error.message : "Conference index unavailable.";
}
const talksById = new Map(talks.map((talk) => [talk.id, talk]));
const passagesById = new Map(passages.map((passage) => [passage.id, passage]));

app.get("/api/status", (_request, response) => {
  response.json({ ready: !corpusError && Boolean(process.env.OPENAI_API_KEY), corpusReady: !corpusError, configured: Boolean(process.env.OPENAI_API_KEY), talkCount: talks.length });
});

app.post("/api/search", async (request, response) => {
  const parsed = questionSchema.safeParse(request.body);
  if (!parsed.success) return response.status(400).json({ error: "Enter a question between 3 and 500 characters." });
  if (corpusError) return response.status(503).json({ error: "The conference corpus has not been imported. Run npm run import." });
  if (!process.env.OPENAI_API_KEY) return response.status(503).json({ error: "OpenAI is not configured. Add OPENAI_API_KEY as shown in .env.example." });

  try {
    const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
    const embedding = await openai.embeddings.create({ model: process.env.OPENAI_EMBEDDING_MODEL || "text-embedding-3-small", input: parsed.data.question });
    const selected = selectPassages(passages, embedding.data[0].embedding);
    const evidence = selected.map(({ passage }) => {
      const talk = talksById.get(passage.talkId)!;
      return { passageId: passage.id, title: talk.title, speaker: talk.speaker, text: passage.text };
    });
    const schema = {
      type: "object",
      additionalProperties: false,
      required: ["evidenceStatus", "answer", "themes", "closingNote"],
      properties: {
        evidenceStatus: { type: "string", enum: ["sufficient", "limited", "none"] },
        answer: { type: "string" },
        themes: { type: "array", maxItems: 5, items: { type: "object", additionalProperties: false, required: ["title", "synthesis", "passageIds"], properties: { title: { type: "string" }, synthesis: { type: "string" }, passageIds: { type: "array", items: { type: "string" } } } } },
        closingNote: { type: "string" },
      },
    } as const;
    const result = await openai.responses.create({
      model: process.env.OPENAI_SYNTHESIS_MODEL || "gpt-5-mini",
      instructions: "Use only the supplied passages. Group compatible teachings into 2-5 concise themes. Cite passage IDs for every theme. Do not create direct quotations or add outside doctrine. If the passages do not directly answer the question, return limited or none. Never claim that every speaker addressed a topic.",
      input: JSON.stringify({ question: parsed.data.question, passages: evidence }),
      text: { format: { type: "json_schema", name: "conference_answer", strict: true, schema } },
    });
    const raw = answerSchema.parse(JSON.parse(result.output_text)) as ModelAnswer;
    const answer = validateModelAnswer(raw, new Set(selected.map(({ passage }) => passage.id)));
    const citedIds = [...new Set(answer.themes.flatMap((theme) => theme.passageIds))];
    const focusById = new Map<string, string>();
    for (const theme of answer.themes) for (const id of theme.passageIds) focusById.set(id, `${theme.title} ${theme.synthesis}`);
    const sources = citedIds.map((id) => {
      const passage = passagesById.get(id)!;
      const talk = talksById.get(passage.talkId)!;
      return { passageId: id, talkId: talk.id, title: talk.title, speaker: talk.speaker, role: talk.role, url: talk.url, excerpt: exactExcerpt(passage.text, 24, focusById.get(id)) };
    });
    response.json({ ...answer, coverage: new Set(sources.map((source) => source.talkId)).size, totalTalks: 37, sources });
  } catch (error) {
    console.error("Search failed:", error instanceof Error ? error.message : "Unknown error");
    response.status(502).json({ error: "The conference answer could not be completed. Please try again." });
  }
});

if (process.env.NODE_ENV === "production") app.use(express.static(path.resolve("dist")));
const port = Number(process.env.PORT || 8787);
app.listen(port, "127.0.0.1", () => console.log(`Conference Compass API: http://127.0.0.1:${port}`));
