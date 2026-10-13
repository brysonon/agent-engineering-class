import path from "node:path";
import { config as loadDotEnv } from "dotenv";

let loaded = false;

export function loadEnvironment(): void {
  if (loaded) return;
  loaded = true;
  loadDotEnv({ path: [path.resolve(".env"), path.resolve("..", "..", ".env")], quiet: true });
}

export interface AppConfig {
  apiKey: string | undefined;
  synthesisModel: string;
  embeddingModel: string;
  port: number;
  cacheRoot: string;
}

export function getConfig(): AppConfig {
  loadEnvironment();
  const port = Number(process.env.PORT ?? 8787);
  return {
    apiKey: process.env.OPENAI_API_KEY?.trim() || undefined,
    synthesisModel: process.env.OPENAI_SYNTHESIS_MODEL?.trim() || "gpt-5-mini",
    embeddingModel: process.env.OPENAI_EMBEDDING_MODEL?.trim() || "text-embedding-3-small",
    port: Number.isInteger(port) && port > 0 ? port : 8787,
    cacheRoot: path.resolve(".cache", "conference-compass")
  };
}
