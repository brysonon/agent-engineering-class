import { createServer } from "./createServer.js";
import { getConfig } from "./config.js";
import { CorpusStore } from "./corpusStore.js";
import { AnswerService } from "./answerService.js";

const config = getConfig();
const store = new CorpusStore(config.cacheRoot);
await store.load();
const service = config.apiKey ? new AnswerService(store, config.apiKey, config.embeddingModel, config.synthesisModel) : null;
const app = createServer({
  corpusReady: () => store.ready,
  apiKeyReady: () => Boolean(config.apiKey),
  answer: (question, requestId) => {
    if (!service) throw new Error("Service unavailable");
    return service.answer(question, requestId);
  },
  production: process.env.NODE_ENV === "production"
});
const server = app.listen(config.port, () => console.log(`Conference Compass API listening on http://localhost:${config.port}`));
for (const signal of ["SIGINT", "SIGTERM"] as const) {
  process.on(signal, () => server.close(() => process.exit(0)));
}
