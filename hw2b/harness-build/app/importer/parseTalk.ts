import * as cheerio from "cheerio";
import type { TalkRecord } from "../shared/contracts.js";

const SESSION_BY_PREFIX: Record<string, string> = {
  "1": "Saturday Morning Session",
  "2": "Saturday Afternoon Session",
  "4": "Sunday Morning Session",
  "5": "Sunday Afternoon Session"
};

function clean(value: string): string {
  return value.replace(/\s+/gu, " ").trim().normalize("NFC");
}

export function parseTalk(html: string, requestedUrl: string): TalkRecord | null {
  const $ = cheerio.load(html);
  const article = $("article[data-content-type='general-conference-talk']").first();
  if (!article.length) return null;

  article.find(".note-ref, sup.marker, .notes, .footnotes, script, style").remove();
  const title = clean(article.find("h1").first().text());
  const rawSpeaker = clean(article.find(".author-name").first().text());
  const speaker = rawSpeaker.replace(/^By\s+/iu, "");
  const role = clean(article.find(".author-role").first().text()) || null;
  const summary = clean(article.find(".kicker").first().text()) || null;
  const paragraphs = article.find(".body-block p").toArray()
    .map((node) => clean($(node).text()))
    .filter(Boolean);
  const canonicalHref = $("link[rel='canonical']").attr("href") ?? requestedUrl;
  const canonical = new URL(canonicalHref, requestedUrl);
  canonical.protocol = "https:";
  canonical.hostname = "www.churchofjesuschrist.org";
  canonical.search = "?lang=eng";
  canonical.hash = "";
  const slug = canonical.pathname.split("/").filter(Boolean).at(-1) ?? "";

  if (!title || !speaker || !slug || !paragraphs.length) return null;
  return {
    id: `2026-10-${slug}`,
    title,
    speaker,
    role,
    summary,
    canonicalUrl: canonical.toString(),
    session: SESSION_BY_PREFIX[slug[0] ?? ""] ?? null,
    paragraphs
  };
}

export function isExcludedNonTalk(talk: TalkRecord): boolean {
  return /sustaining of general authorities/i.test(talk.title);
}
