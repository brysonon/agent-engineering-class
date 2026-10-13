# Conference Compass

Conference Compass is an independent study app for the fixed October 2026 general conference corpus. It semantically searches all 37 English authored talks, asks an OpenAI model to organize only the retrieved evidence, validates every citation, and displays exact source excerpts selected by server code.

This class project is not affiliated with or endorsed by The Church of Jesus Christ of Latter-day Saints.

## Requirements

- Node.js 22 or newer
- Network access for the official conference pages and OpenAI
- An OpenAI API key with access to `text-embedding-3-small` and `gpt-5-mini`

## Setup on Windows

From this `harness-build` directory:

```powershell
npm install
Copy-Item .env.example .env
```

Add the API key to `.env`, then prepare the local corpus and start the app:

```powershell
npm run import
npm run dev
```

Open <http://localhost:5173>. The API runs at <http://localhost:8787>. A repository-root `.env` is also read for class-harness integration; a local `.env` takes precedence and remains the normal setup path.

Available commands:

```powershell
npm run import          # fetch, validate, chunk, embed, and atomically activate the corpus
npm run dev             # run Vite and the API together
npm run typecheck       # check client and server TypeScript
npm test                # run the mocked automated suite
npm run build           # create dist/client and dist/server
npm start               # serve the built client and API
npm run test:integration # optional: run the five real-API acceptance prompts
```

If npm is not installed in the class runtime, the bundled pnpm command can run the same scripts.

## Architecture

The importer discovers talk pages from the fixed official collection, rejects non-talk pages, validates exactly 37 talks, chunks by paragraph, and caches content-addressed embeddings. It builds a versioned staged index and changes `active.json` only after every invariant passes. Full official text, generated passages, and embeddings stay in ignored `.cache/conference-compass` files.

The Node server loads the validated active index, embeds each question, scores every passage, and chooses up to 16 passages with no more than two from one talk. It sends only the question and those delimited passages to the OpenAI Responses API using a strict Structured Outputs schema. Server-side validation rejects malformed evidence states, citations outside the retrieved set, and quotation markers in model-authored prose; retryable violations receive one controlled retry. The server derives excerpts from stored source text, joins trusted source metadata, groups cited passages into one source card per official talk, calculates unique cited-talk coverage, and returns a fixed response DTO.

The React client contains no OpenAI code or corpus index. It renders text through React, provides keyboard submission and focus movement including error/retry transitions, announces loading/results/errors, distinguishes sufficient, limited, and no-evidence results, and links passage citations to exact evidence anchors inside deduplicated official talk cards.

## Data and operational limits

The importer depends on the current structure and availability of the official October 2026 collection. It fails loudly if parsing no longer yields the required corpus. Exact citation membership is mechanically enforced, while whether a synthesis perfectly captures a passage remains a model-quality question; users are told to read citations in context. The rate limiter is process-local and intended for this local class project. Questions remain request-local and are not written or logged in full.
