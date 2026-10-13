# Conference Compass — Baseline Build

This is the one-prompt implementation of the shared [`../SPEC.md`](../SPEC.md).
It searches a fixed October 2026 general conference corpus, asks an OpenAI model
to synthesize only retrieved evidence, and attaches exact source excerpts.

## Setup

1. Copy `.env.example` to `.env` and add `OPENAI_API_KEY`.
2. Install dependencies with `npm install`.
3. Run `npm run import` once to fetch, validate, chunk, and embed 37 talks.
4. Start the client and API with `npm run dev`.

Use `npm test` for offline unit tests and `npm run build` for a production client
build. The downloaded corpus and generated embedding index live under ignored
`.cache/`. Generated answers may be incomplete; follow citations to read each
talk in context.
