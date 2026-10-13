import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import path from "node:path";
import { createHash, randomUUID } from "node:crypto";
import type { CorpusIndex, TalkRecord } from "../shared/contracts.js";
import { CACHE_SCHEMA_VERSION, CONFERENCE_NAME } from "../shared/constants.js";
import { getConfig } from "../server/config.js";
import { chunkTalk } from "./chunk.js";
import { embedPassages } from "./embed.js";
import { discoverTalkUrls, fetchText } from "./fetchConference.js";
import { isExcludedNonTalk, parseTalk } from "./parseTalk.js";
import { validateCorpus } from "./validateCorpus.js";

async function cachedFetch(url: string, directory: string): Promise<string> {
  const key = createHash("sha256").update(url).digest("hex");
  const file = path.join(directory, `${key}.html`);
  try { return await readFile(file, "utf8"); } catch { /* fetch below */ }
  const html = await fetchText(url);
  await writeFile(file, html, "utf8");
  return html;
}

async function mapConcurrent<T, R>(values: T[], limit: number, mapper: (value: T) => Promise<R>): Promise<R[]> {
  const result = new Array<R>(values.length);
  let cursor = 0;
  await Promise.all(Array.from({ length: Math.min(limit, values.length) }, async () => {
    while (cursor < values.length) {
      const index = cursor++;
      const value = values[index];
      if (value !== undefined) result[index] = await mapper(value);
    }
  }));
  return result;
}

async function main(): Promise<void> {
  const config = getConfig();
  if (!config.apiKey) throw new Error("OPENAI_API_KEY is required. Copy .env.example to .env or configure the repository-root .env.");
  const sourceDirectory = path.join(config.cacheRoot, "sources");
  const indexesDirectory = path.join(config.cacheRoot, "indexes");
  await mkdir(sourceDirectory, { recursive: true });
  await mkdir(indexesDirectory, { recursive: true });
  const collectionHtml = await cachedFetch("https://www.churchofjesuschrist.org/study/general-conference/2026/10?lang=eng", sourceDirectory);
  const urls = discoverTalkUrls(collectionHtml);
  console.log(`Discovered ${urls.length} candidate pages from the official collection.`);
  const parsed = await mapConcurrent(urls, 4, async (url) => parseTalk(await cachedFetch(url, sourceDirectory), url));
  const talks = parsed.filter((talk): talk is TalkRecord => Boolean(talk)).filter((talk) => !isExcludedNonTalk(talk));
  validateCorpus(talks);
  const chunks = talks.flatMap(chunkTalk);
  const embedded = await embedPassages(chunks, { apiKey: config.apiKey, model: config.embeddingModel, cacheRoot: config.cacheRoot });
  const passages = chunks.map((chunk, index) => ({ ...chunk, embedding: embedded.vectors[index] ?? [] }));
  const index: CorpusIndex = {
    schemaVersion: CACHE_SCHEMA_VERSION,
    conference: CONFERENCE_NAME,
    embeddingModel: config.embeddingModel,
    importedAt: new Date().toISOString(),
    talks,
    passages
  };
  const version = `${Date.now()}-${randomUUID().slice(0, 8)}`;
  const stage = path.join(indexesDirectory, `${version}.staging`);
  const finalDirectory = path.join(indexesDirectory, version);
  await mkdir(stage, { recursive: true });
  await writeFile(path.join(stage, "index.json"), JSON.stringify(index), "utf8");
  await rename(stage, finalDirectory);
  const pointerTemp = path.join(config.cacheRoot, `active.${randomUUID()}.tmp`);
  await writeFile(pointerTemp, JSON.stringify({ version }), "utf8");
  await rename(pointerTemp, path.join(config.cacheRoot, "active.json"));
  console.log(`Imported ${talks.length} talks and ${passages.length} passages.`);
  console.log(`Embedding cache: ${embedded.hits} hits, ${embedded.misses} misses.`);
  console.log(`Activated index ${version}.`);
}

main().catch((error: unknown) => {
  console.error(error instanceof Error ? error.message : "Import failed.");
  process.exitCode = 1;
});
