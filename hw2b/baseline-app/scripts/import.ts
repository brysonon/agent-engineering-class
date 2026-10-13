import "dotenv/config";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import * as cheerio from "cheerio";
import OpenAI from "openai";
import { chunkTalk, type Passage, type Talk } from "../server/core.js";

const ROOT = "https://www.churchofjesuschrist.org";
const COLLECTION = `${ROOT}/study/general-conference/2026/10?lang=eng`;
const cacheDir = path.resolve(".cache");
const htmlDir = path.join(cacheDir, "html");
await mkdir(htmlDir, { recursive: true });

async function cachedFetch(url: string, filename: string) {
  const destination = path.join(htmlDir, filename);
  try {
    return await readFile(destination, "utf8");
  } catch {
    const response = await fetch(url, {
      signal: AbortSignal.timeout(30_000),
      headers: { "User-Agent": "ConferenceCompassClassProject/1.0" },
    });
    if (!response.ok) throw new Error(`${url} returned HTTP ${response.status}`);
    const html = await response.text();
    await writeFile(destination, html);
    return html;
  }
}

const landing = await cachedFetch(COLLECTION, "collection.html");
const landingPage = cheerio.load(landing);
const paths = [...new Set(
  landingPage("a[href]").map((_, element) => landingPage(element).attr("href") ?? "").get()
    .map((href) => href.split("?")[0])
    .filter((href) => /^\/study\/general-conference\/2026\/10\/\d/.test(href))
    .filter((href) => !href.endsWith("/11christofferson")),
)].sort();

if (paths.length !== 37) throw new Error(`Expected 37 authored talks, found ${paths.length}.`);

const sessionFor = (id: string) => id.startsWith("1") ? "Saturday Morning" : id.startsWith("2") ? "Saturday Afternoon" : id.startsWith("4") ? "Sunday Morning" : "Sunday Afternoon";

async function parseTalk(relativeUrl: string): Promise<Talk> {
  const id = relativeUrl.split("/").at(-1)!;
  const html = await cachedFetch(`${ROOT}${relativeUrl}?lang=eng`, `${id}.html`);
  const $ = cheerio.load(html);
  let speaker = "";
  try {
    for (const element of $('script[type="application/ld+json"]').toArray()) {
      const data = JSON.parse($(element).text());
      const author = data?.mainEntity?.author?.name ?? data?.author?.name;
      if (author) { speaker = author; break; }
    }
  } catch { /* fall through to visible metadata */ }

  const title = $('meta[name="title"]').attr("content")?.trim() || $("title").text().trim();
  const summary = $('meta[name="description"]').attr("content")?.trim() ?? "";
  const url = $('link[rel="canonical"]').attr("href")?.trim() || `${ROOT}${relativeUrl}?lang=eng`;
  const role = $(".author-role, .subtitle, [data-aid='author-role']").first().text().replace(/\s+/g, " ").trim();
  let paragraphs = $("article .body-block p, article .body p, main .body-block p").map((_, element) => $(element).text().replace(/\s+/g, " ").trim()).get().filter((text) => text.length > 20);
  if (!paragraphs.length) {
    paragraphs = $("article p").map((_, element) => $(element).text().replace(/\s+/g, " ").trim()).get().filter((text) => text.length > 20);
  }
  const notesIndex = paragraphs.findIndex((text) => text === "Notes");
  if (notesIndex >= 0) paragraphs = paragraphs.slice(0, notesIndex);
  paragraphs = paragraphs.filter((text) => !/^By (Elder|President|Sister|Bishop|Brother)\b/.test(text));
  const wordCount = paragraphs.join(" ").split(/\s+/).length;
  if (!title || !speaker || !url.startsWith(`${ROOT}/`) || wordCount < 250) {
    throw new Error(`Invalid talk ${id}: title=${Boolean(title)} speaker=${Boolean(speaker)} words=${wordCount}`);
  }
  return { id, title, speaker, role, summary, url, session: sessionFor(id), paragraphs };
}

const talks: Talk[] = [];
let cursor = 0;
async function worker() {
  while (cursor < paths.length) {
    const relativeUrl = paths[cursor++];
    const talk = await parseTalk(relativeUrl);
    talks.push(talk);
    console.log(`Fetched ${talks.length}/37: ${talk.title}`);
  }
}
await Promise.all(Array.from({ length: 4 }, worker));
talks.sort((a, b) => a.id.localeCompare(b.id, undefined, { numeric: true }));

if (new Set(talks.map((talk) => talk.id)).size !== 37 || new Set(talks.map((talk) => talk.url)).size !== 37) {
  throw new Error("Talk IDs and canonical URLs must be unique.");
}

const apiKey = process.env.OPENAI_API_KEY;
if (!apiKey) throw new Error("OPENAI_API_KEY is required to create the search index.");
const openai = new OpenAI({ apiKey });
const embeddingModel = process.env.OPENAI_EMBEDDING_MODEL || "text-embedding-3-small";
const barePassages = talks.flatMap((talk) => chunkTalk(talk));
const existingPath = path.join(cacheDir, "passages.json");
let previous = new Map<string, Passage>();
try {
  const saved = JSON.parse(await readFile(existingPath, "utf8")) as Passage[];
  previous = new Map(saved.map((passage) => [passage.id, passage]));
} catch { /* first import */ }

const passages: Passage[] = [];
for (let index = 0; index < barePassages.length; index += 64) {
  const batch = barePassages.slice(index, index + 64);
  const reusable = batch.every((item) => previous.get(item.id)?.text === item.text && previous.get(item.id)?.embedding.length);
  if (reusable) {
    passages.push(...batch.map((item) => previous.get(item.id)!));
    continue;
  }
  const response = await openai.embeddings.create({ model: embeddingModel, input: batch.map((item) => item.text) });
  passages.push(...batch.map((item, offset) => ({ ...item, embedding: response.data[offset].embedding })));
  console.log(`Embedded ${Math.min(index + batch.length, barePassages.length)}/${barePassages.length} passages`);
}

await writeFile(path.join(cacheDir, "talks.json"), `${JSON.stringify(talks, null, 2)}\n`);
await writeFile(existingPath, `${JSON.stringify(passages)}\n`);
await writeFile(path.join(cacheDir, "index-meta.json"), `${JSON.stringify({ conference: "October 2026", talkCount: talks.length, passageCount: passages.length, embeddingModel }, null, 2)}\n`);
console.log(`Ready: ${talks.length} talks and ${passages.length} passages.`);
