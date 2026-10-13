import * as cheerio from "cheerio";
import { COLLECTION_URL } from "../shared/constants.js";

const ORIGIN = "https://www.churchofjesuschrist.org";
const TALK_PATH = /^\/study\/general-conference\/2026\/10\/[^/?#]+$/;

export async function fetchText(url: string, attempts = 3): Promise<string> {
  let lastError: unknown;
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      const response = await fetch(url, {
        headers: { "user-agent": "ConferenceCompassClassProject/1.0 (+local educational importer)" },
        signal: AbortSignal.timeout(30_000)
      });
      if (!response.ok) throw new Error(`HTTP ${response.status} for ${url}`);
      return await response.text();
    } catch (error) {
      lastError = error;
      if (attempt < attempts) await new Promise((resolve) => setTimeout(resolve, 300 * attempt));
    }
  }
  throw lastError;
}

export function discoverTalkUrls(html: string): string[] {
  const $ = cheerio.load(html);
  const urls = new Set<string>();
  $("a[href]").each((_index, element) => {
    const href = $(element).attr("href");
    if (!href) return;
    const parsed = new URL(href, ORIGIN);
    if (parsed.origin !== ORIGIN || !TALK_PATH.test(parsed.pathname)) return;
    parsed.search = "?lang=eng";
    parsed.hash = "";
    urls.add(parsed.toString());
  });
  return [...urls].sort();
}

export async function fetchCollection(): Promise<{ html: string; urls: string[] }> {
  const html = await fetchText(COLLECTION_URL);
  return { html, urls: discoverTalkUrls(html) };
}
