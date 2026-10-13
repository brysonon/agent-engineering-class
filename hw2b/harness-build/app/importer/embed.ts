import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import OpenAI from "openai";
import type { PassageWithoutEmbedding } from "./chunk.js";

function keyFor(model: string, text: string): string {
  return createHash("sha256").update(`v1\0${model}\0${text}`).digest("hex");
}

export async function embedPassages(
  passages: PassageWithoutEmbedding[],
  options: { apiKey: string; model: string; cacheRoot: string }
): Promise<{ vectors: number[][]; hits: number; misses: number }> {
  const directory = path.join(options.cacheRoot, "embeddings", options.model.replace(/[^a-z0-9_.-]/gi, "_"));
  await mkdir(directory, { recursive: true });
  const vectors: Array<number[] | undefined> = new Array(passages.length);
  const missing: Array<{ index: number; key: string; text: string }> = [];
  for (let index = 0; index < passages.length; index += 1) {
    const passage = passages[index];
    if (!passage) continue;
    const key = keyFor(options.model, passage.text);
    try {
      const parsed = JSON.parse(await readFile(path.join(directory, `${key}.json`), "utf8")) as number[];
      if (parsed.length && parsed.every(Number.isFinite)) vectors[index] = parsed;
      else throw new Error("bad vector");
    } catch {
      missing.push({ index, key, text: passage.text });
    }
  }
  const client = new OpenAI({ apiKey: options.apiKey, timeout: 45_000, maxRetries: 1 });
  for (let offset = 0; offset < missing.length; offset += 64) {
    const batch = missing.slice(offset, offset + 64);
    const result = await client.embeddings.create({ model: options.model, input: batch.map((entry) => entry.text) });
    if (result.data.length !== batch.length) throw new Error("Embedding provider returned the wrong vector count.");
    for (let i = 0; i < batch.length; i += 1) {
      const entry = batch[i];
      const vector = result.data[i]?.embedding;
      if (!entry || !vector?.length || !vector.every(Number.isFinite)) throw new Error("Embedding provider returned an invalid vector.");
      vectors[entry.index] = vector;
      await writeFile(path.join(directory, `${entry.key}.json`), JSON.stringify(vector), "utf8");
    }
  }
  if (vectors.some((vector) => !vector)) throw new Error("Embedding index is incomplete.");
  return { vectors: vectors as number[][], hits: passages.length - missing.length, misses: missing.length };
}
