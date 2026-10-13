import { randomUUID } from "node:crypto";
import { getConfig } from "./config.js";
import { CorpusStore } from "./corpusStore.js";
import { AnswerService } from "./answerService.js";
import { countExcerptWords } from "./excerpts.js";
import { containsDirectQuoteMarkers } from "./validation.js";

const prompts = [
  "What was taught about faith during trials?",
  "How can I become more Christlike?",
  "What did leaders teach about covenants?",
  "What was said about gambling?",
  "What did conference say about choosing a college major?"
];

const config = getConfig();
if (!config.apiKey) throw new Error("OPENAI_API_KEY is required for integration checks.");
const store = new CorpusStore(config.cacheRoot);
if (!await store.load()) throw new Error("Run the importer before integration checks.");
const service = new AnswerService(store, config.apiKey, config.embeddingModel, config.synthesisModel);

const requestedPrompt = Number(process.env.INTEGRATION_PROMPT ?? 0);
const selected = requestedPrompt >= 1 && requestedPrompt <= prompts.length
  ? [{ prompt: prompts[requestedPrompt - 1]!, index: requestedPrompt - 1 }]
  : prompts.map((prompt, index) => ({ prompt, index }));

for (const selectedPrompt of selected) {
  const { index } = selectedPrompt;
  const response = await service.answer(selectedPrompt.prompt, randomUUID());
  const modelOwnedText = [response.answer, response.closingNote, ...response.themes.flatMap((theme) => [theme.title, theme.synthesis])];
  if (modelOwnedText.some(containsDirectQuoteMarkers)) throw new Error(`Prompt ${index + 1} returned quotation markers in synthesis.`);
  for (const source of response.sources) {
    for (const sourcePassage of source.passages) {
      const passage = store.getPassage(sourcePassage.id);
      if (!passage) throw new Error(`Prompt ${index + 1} cited a missing passage.`);
      if (sourcePassage.excerpt && (!passage.text.includes(sourcePassage.excerpt) || countExcerptWords(sourcePassage.excerpt) > 24)) {
        throw new Error(`Prompt ${index + 1} returned a non-exact excerpt.`);
      }
    }
  }
  if (response.sources.length !== response.usedTalkCount) throw new Error(`Prompt ${index + 1} returned an incorrect grouped coverage count.`);
  console.log(JSON.stringify({
    prompt: index + 1,
    evidenceStatus: response.evidenceStatus,
    themes: response.themes.length,
    sourceCards: response.sources.length,
    passages: response.sources.reduce((count, source) => count + source.passages.length, 0),
    usedTalkCount: response.usedTalkCount,
    excerptChecks: response.sources.flatMap((source) => source.passages).filter((passage) => passage.excerpt).length,
    sourceTitles: response.sources.map((source) => source.title)
  }));
}
