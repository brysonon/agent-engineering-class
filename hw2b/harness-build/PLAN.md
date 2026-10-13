# Conference Compass implementation plan

## 1. Scope and design decisions

Conference Compass will be a single-page React application backed by a Node.js API. It will answer one English question at a time from a fixed, locally imported October 2026 English conference corpus. The browser will never receive an OpenAI key, embeddings, full passage collections, or model instructions. The server will retrieve evidence, ask the model for a structured synthesis, validate it, derive exact excerpts from stored source text, and return a presentation-safe result.

The implementation will use Node.js 22+, TypeScript in ESM mode, React, Vite, Express, the official OpenAI JavaScript SDK, Zod for runtime validation, Cheerio for import-time HTML parsing, and Vitest with Testing Library and Supertest. `tsx` will run TypeScript development and import entry points. `concurrently` will start Vite and the API in development in a Windows-safe way. The root `package.json` will own all required commands so they work from `harness-build/`.

The following values will be named in one shared server configuration module and covered by tests:

- maximum question length: 1,000 Unicode code points;
- request JSON body limit: 16 KiB;
- request rate limit: 20 synthesis requests per 15 minutes per IP, with an in-memory store suitable for this local project;
- retrieval target: 16 passages;
- retrieval ranking pool: the best 60 passages after scoring the full index;
- maximum passages per talk in synthesis context: 2;
- passage target size: 500 words, normally bounded to 350–650 words;
- passage overlap: one complete paragraph when doing so does not create a duplicate passage;
- OpenAI request timeout: 45 seconds;
- synthesis attempts: at most 2 total;
- displayed excerpt limit: 24 words;
- sufficient-evidence themes: 2–5; limited-evidence themes: 1–5; no-evidence themes: 0.

The retrieval target is intentionally independent of the evidence status. The best 16 diverse passages are supplied even for weak queries; the grounded synthesis contract decides whether they directly answer the question. This avoids treating a cosine score as a universal doctrinal-relevance cutoff.

## 2. Planned file layout

```text
harness-build/
├── .env.example
├── .gitignore
├── README.md
├── package.json
├── tsconfig.base.json
├── vitest.config.ts
├── app/
│   ├── client/
│   │   ├── index.html
│   │   └── src/
│   │       ├── main.tsx
│   │       ├── App.tsx
│   │       ├── api.ts
│   │       ├── styles.css
│   │       ├── components/
│   │       │   ├── Header.tsx
│   │       │   ├── QuestionForm.tsx
│   │       │   ├── StatusPanel.tsx
│   │       │   ├── Results.tsx
│   │       │   ├── ThemeCard.tsx
│   │       │   └── SourceList.tsx
│   │       └── test/
│   │           └── App.test.tsx
│   ├── server/
│   │   ├── index.ts
│   │   ├── createServer.ts
│   │   ├── config.ts
│   │   ├── errors.ts
│   │   ├── corpusStore.ts
│   │   ├── retrieval.ts
│   │   ├── synthesis.ts
│   │   ├── validation.ts
│   │   ├── excerpts.ts
│   │   ├── rateLimit.ts
│   │   ├── logging.ts
│   │   └── test/
│   │       ├── api.test.ts
│   │       ├── retrieval.test.ts
│   │       ├── synthesis.test.ts
│   │       ├── excerpts.test.ts
│   │       └── clientSecretScan.test.ts
│   ├── importer/
│   │   ├── index.ts
│   │   ├── fetchConference.ts
│   │   ├── parseCollection.ts
│   │   ├── parseTalk.ts
│   │   ├── normalize.ts
│   │   ├── chunk.ts
│   │   ├── embed.ts
│   │   ├── validateCorpus.ts
│   │   ├── cache.ts
│   │   └── test/
│   │       ├── fixtures/
│   │       ├── validateCorpus.test.ts
│   │       └── chunk.test.ts
│   └── shared/
│       ├── contracts.ts
│       ├── schemas.ts
│       └── constants.ts
└── .cache/                         # ignored; created by npm run import
    └── conference-compass/
        ├── active.json             # points at one fully validated index version
        ├── sources/                # downloaded official HTML and parsed full talks
        ├── embeddings/             # content/model-keyed embedding cache
        └── indexes/<version>/      # corpus, passages, vectors, and import manifest
```

Full talk text, source HTML, chunks, and embeddings will remain under ignored `.cache/`. Test fixtures may include invented text, official metadata, and only short source excerpts. The import manifest will record import time, collection URL, source hashes, model name, counts, and schema version, but no API key.

## 3. Runtime architecture and data flow

1. On `npm run import`, the importer loads server-only environment variables, fetches the fixed official collection and talk pages, parses and validates 37 authored talks, chunks them, reuses or creates passage embeddings, validates the complete output, and activates the new version.
2. On server startup, `CorpusStore` reads `.cache/conference-compass/active.json`, validates the index schema and the 37-talk invariant, and loads talk metadata, passage text, and vectors into read-only memory. A missing or invalid active index leaves the API running in a `corpus_not_imported` state so the UI can explain how to recover.
3. The client validates a trimmed question, disables resubmission, announces progress, and sends `POST /api/answer` with `{ question }`.
4. The server validates content type, body size, question length, corpus readiness, API configuration, and rate limit before any OpenAI request.
5. The server embeds the question with the configured embedding model. Retrieval computes similarity against every loaded passage, sorts deterministically, then applies diversity over the top-60 pool until it has up to 16 passages and no more than two from a talk.
6. The server sends only the trimmed question, grounding instruction, retrieved passage IDs/text/talk metadata, and strict response schema to `gpt-5-mini` (or the configured override) via the Responses API.
7. The server parses and validates the structured output, rejects invalid evidence-state/theme combinations and any citation not in the retrieved set, and performs one controlled retry for a retryable malformed, incomplete, timed-out, or citation-invalid response. A refusal is surfaced as a distinct safe error; it is not transformed into an answer.
8. After validation, the server removes no-source themes, derives exact excerpts from the cited stored passages, deduplicates sources, calculates the unique cited-talk count, and serializes a safe response contract. For sufficient and limited results, the validated union of theme passage IDs also supports a citation cluster placed directly beside the combined answer; no-evidence limitation text needs no evidence citation. If validation would leave a sufficient/limited answer without support, the request fails rather than degrading into an ungrounded answer.
9. React renders plain text nodes only. Theme citation controls point to source cards in the result, and source cards link to canonical official URLs.

The API response will contain the submitted trimmed question; evidence status; combined answer; validated theme titles, syntheses, and source references; closing note; deduplicated sources; and `usedTalkCount`. It will not contain embeddings, prompts, stack traces, internal OpenAI output, or configuration values.

## 4. Trust boundaries and safety controls

There are four explicit trust boundaries:

1. **Official web pages entering the importer.** Official pages are still untrusted input. Parsing will use expected structural selectors and metadata rather than executing page scripts. Text will be normalized as data. Imported phrases that resemble instructions will never be included in the system/developer grounding instruction; passages will be clearly delimited and described as quoted source data that must not alter instructions.
2. **Browser input entering the API.** Express will accept only JSON for the answer route, cap the request body, validate one known field, trim it, count Unicode code points, reject additional/invalid values, rate-limit requests, and avoid logging the full question.
3. **OpenAI output entering application state.** Strict Structured Outputs are necessary but not sufficient. Zod and semantic citation checks will run server-side. The model cannot provide URLs, speaker names, coverage counts, or excerpt text used by the UI; those are joined from trusted imported records.
4. **Server data entering the browser.** The API returns a fixed JSON contract and generic error codes/messages. React renders strings without `dangerouslySetInnerHTML`. Canonical URLs must have been validated at import and are emitted only from the corpus store. External links use `target="_blank"` with `rel="noopener noreferrer"` and visible external-link wording/icon text.

The OpenAI client exists only in `app/server` and `app/importer`. Vite client code will have no access to `process.env`, and no variable named with a `VITE_` prefix will hold a secret. Production-style logging will include a request ID, timings, status/error code, and question length, but never the full question, authorization headers, model prompts, corpus passages, or raw provider errors. Questions live only in request-local memory and are not written to disk.

## 5. Conference importer

### Discovery and parsing

The collection URL is fixed to `https://www.churchofjesuschrist.org/study/general-conference/2026/10?lang=eng`. The importer will identify English talk links from the collection's structured page data or semantic talk-card links, normalize relative URLs against the official origin, strip fragments and irrelevant tracking parameters, retain `lang=eng`, and deduplicate normalized canonical URLs before fetching.

Talk parsing will prefer embedded structured content/metadata when it supplies the required fields and ordered paragraphs; otherwise it will use narrowly scoped selectors within the main article. It will extract title, speaker, role/calling when present, summary/deck when present, session, canonical URL, and ordered body paragraphs. Body extraction will explicitly exclude headers, navigation, footnotes/endnotes, media/download controls, related links, and footer content. It will preserve paragraph order and textual punctuation while normalizing only insignificant whitespace and Unicode normalization (`NFC`).

A page qualifies as a talk only when it has authored-talk metadata, a speaker, and a nonempty article body. The collection, session pages, sustaining presentation, and music pages will therefore be excluded; closing remarks remain eligible as authored content. The importer will report discovered, accepted, and excluded URLs with exclusion reasons so a site-layout change is diagnosable.

Stable talk IDs will derive from the canonical conference path slug, prefixed with `2026-10-`; collisions fail validation rather than receiving order-dependent suffixes. The importer will use bounded concurrency, a descriptive user agent, timeouts, and retry with backoff for transient fetch failures.

### Validation and atomic activation

Before embeddings or activation, validation requires exactly 37 records; unique stable IDs and canonical URLs; required title, speaker, URL, and body fields; the exact HTTPS hostname `www.churchofjesuschrist.org`; ordered nonempty paragraphs; and a minimum body length of 300 words. The minimum is a named heuristic and will include talk ID/title and observed count in an error. Optional role, summary, and session values remain nullable rather than fabricated.

The importer builds into a new versioned directory. It never mutates the active index in place. Only after talk validation, chunk validation, embedding dimensionality checks, and complete-index validation succeed will it write a temporary `active.json` and replace the pointer. Failed imports leave the previous active version usable and return a nonzero exit code with actionable errors. This transaction design also prevents a partial corpus from becoming production input.

### Passage creation and embedding cache

Chunking is deterministic and operates on paragraph arrays. It greedily adds whole paragraphs toward 500 words, normally closing a passage between 350 and 650 words. It will allow an overlong single paragraph to exceed 650 rather than cut a sentence. Neighboring passages repeat one whole boundary paragraph when possible; paragraph start/end positions describe the non-overlap coverage, while an explicit overlap position records repeated context. Tests will prove all original paragraphs appear in order without loss.

Passage IDs will be `talkId:p<start>-<end>:<contentHash8>`, using zero-based paragraph positions and a SHA-256 prefix over normalized passage text. The hash prevents stale citations from silently referring to changed content, while identical inputs reproduce identical IDs.

Embedding cache keys will combine schema version, exact configured embedding model name, and SHA-256 of normalized passage text. The importer batches cache misses within the provider input limits, validates vector count/dimensions/numeric finiteness, and writes each completed batch safely. Re-running with unchanged text and model reuses all vectors; changing the model or passage text invalidates only affected keys. The final index stores passage records and vectors in aligned, schema-validated arrays.

## 6. Retrieval

The query embedding must use the same configured model recorded by the active index; a mismatch produces a configuration error directing the developer to rerun the importer. Retrieval normalizes vectors and computes cosine similarity over every indexed passage for every request. The implementation will expose the number scored in test instrumentation so a test can assert it equals the entire index length.

Scores are sorted descending with passage ID as a deterministic tie-breaker. From the top 60, a diversity pass repeatedly selects the highest-ranked eligible passage while enforcing at most two passages per talk until reaching 16 or exhausting eligible passages. The resulting order and original scores are retained for server use but scores are not presented as doctrinal confidence to users. The model receives passage IDs, talk IDs, title, speaker, canonical URL, session, and passage text in explicit data delimiters.

## 7. Grounded structured synthesis and citation validation

The Responses API request will use the configured synthesis model and a strict JSON schema with all fields required and `additionalProperties: false` at every object level. The schema matches `ConferenceAnswer` and restricts `evidenceStatus` to `sufficient`, `limited`, or `none`; theme arrays to at most five entries; nonempty titles/syntheses; and nonempty, unique `passageIds` for each theme. The model instruction will require passage-level support for every substantive statement, careful grouping of compatible ideas, preservation of meaningful differences, no assertion of universal speaker coverage, no outside facts/doctrine/advice, and paraphrase rather than direct quotation.

Server semantic validation will enforce:

- every cited ID belongs to the exact retrieved set for this request;
- each displayed theme has at least one valid unique citation;
- `sufficient` has 2–5 themes, `limited` has 1–5, and `none` has no themes;
- `none` contains no source citations or quotations and uses a plain corpus-limitation answer;
- answer and closing-note strings are present and bounded to reasonable response lengths;
- source metadata and links always come from the corpus, never model fields;
- the unique coverage count is calculated from citations after validation.

The first retryable failure triggers one new request containing the same evidence plus a concise statement of the contract violation, without treating the invalid text as evidence. The second failure maps to a stable error code. Provider refusal maps to `model_refusal`; incomplete output to `model_incomplete`; timeout to `provider_timeout`; bad structured/citation output to `synthesis_invalid`; and other upstream failures to `synthesis_failed`. Browser messages remain useful but contain no raw provider body.

## 8. Exact-excerpt strategy

The model will never return display quotation text. For each distinct cited passage, the server will deterministically select a representative substring from the stored passage after synthesis validation:

1. Segment the passage into sentences while retaining original character offsets.
2. Score sentences by case-insensitive lexical overlap with the user question, theme title, and theme synthesis after removing a small fixed English stop-word list. Question terms receive the greatest weight.
3. Prefer the highest-scoring complete sentence containing 6–24 words.
4. If the best useful sentence exceeds 24 words, choose the highest-scoring contiguous window of at most 24 word spans and slice the original string from the first span start to the last span end. Visual ellipses, if used, are rendered outside the quoted string.
5. Verify before serialization that the excerpt is an exact contiguous substring of the stored passage and contains no more than 24 words. If no candidate has meaningful lexical overlap, omit `excerpt` and return attribution/link only.

Word counting and substring validation will share one utility with the automated tests so punctuation and contractions are handled consistently. Excerpts retain source capitalization and punctuation because they are character slices, not reconstructed token joins. The deduplicated source list keys entries by passage ID, while repeated citations in themes reference the same source anchor. Each source includes trusted speaker, talk title, canonical URL, and optional excerpt. The UI places quotation marks only around a verified excerpt.

## 9. UI behavior and accessibility

The page will use a warm neutral background, dark text, a restrained blue-green accent, a reading column around 72rem, and responsive one-column layouts below tablet widths. CSS will use fluid spacing and `min-width: 0` so the interface has no horizontal scroll at 320px. It will use system typography and no official branding, logos, or copied layouts.

The header always shows `Conference Compass`, the required description, `October 2026 · 37 talks`, and an independent-study-project statement. The form uses a labeled textarea, the required button label, a visible character counter near the limit, and the four exact example prompt buttons. Enter submits; Shift+Enter inserts a line break. Empty and oversized values produce inline text associated through `aria-describedby`, and focus moves to the invalid field.

During a request, form controls are disabled and an `aria-live="polite"` status region first announces `Searching 37 talks…`, then changes on a short client timer to `Bringing the teachings together…`. The timer represents UI progress only and does not claim a completed server phase. Duplicate submissions are blocked both by UI state and an active-request guard; a new submission aborts no existing request because controls remain disabled.

On success, focus moves to the result heading (`tabIndex=-1`). Results restate the question; show evidence-status text; render the answer and closing note as plain text; place the union-of-theme citation cluster beside a sufficient/limited combined answer; show 2–5 themes for sufficient evidence or supported themes for limited evidence; place citation links beside each theme; state `Used evidence from X of 37 talks`; and show a deduplicated source list. `Ask another question` clears results, restores the original form area, and focuses the textarea.

No-evidence success has its own result state, plainly says the corpus does not directly answer the question, shows no themes or quotations, and repeats the example prompts. Error panels distinguish `corpus_not_imported`, `missing_api_key`, network failure, model refusal/incomplete output, rate limiting, and retrieval/synthesis failure, with recovery guidance where available. Missing-key and corpus errors point to `.env.example` and `npm run import` respectively. All status changes use an appropriate live region; unexpected errors use `role="alert"`.

Semantic `header`, `main`, `form`, `section`, headings, lists, buttons, and links will support keyboard and screen-reader use. CSS will provide visible `:focus-visible` styles, contrast meeting WCAG AA, 44px practical touch targets, hover states that do not carry meaning alone, and a `prefers-reduced-motion` rule that disables nonessential transitions. External links will say `Read the full talk (opens in a new tab)` or have equivalent accessible text.

Every result includes a concise note that generated summaries may be incomplete and citations should be read in context.

## 10. Error model and operational behavior

The API will return a request ID, stable machine-readable error code, and safe message with an appropriate HTTP status. Expected mappings are: validation `400`; missing corpus/API configuration `503`; rate limit `429`; provider timeout `504`; refusal/incomplete/invalid synthesis `502`; and unexpected internal failure `500`. The client maps codes to distinct copy and falls back safely for network/non-JSON responses.

The server will expose a lightweight `GET /api/status` reporting only readiness booleans and the fixed conference/talk count when loaded. It will not report environment values. The client may use it at startup to show configuration guidance without entering an indefinite loading state.

Production build will compile the client and server separately. The Node server will serve the Vite output and API routes. Development will run Vite and the API together; Vite proxies `/api` to the server. Shutdown handlers will close the HTTP listener without assuming Unix signals are the only termination path.

## 11. Windows development plan

Windows is a required development environment, not an afterthought:

- all documented commands run from PowerShell at `harness-build\` and use `npm run ...`; no Bash-only environment assignment or shell syntax will be required;
- package scripts invoke Node-based CLIs (`tsx`, `vite`, `concurrently`, `vitest`) and use `cross-env` only if a script must set an environment variable;
- filesystem paths use `node:path` (`path.join`, `path.resolve`) and file URLs use `pathToFileURL`; code will not concatenate `/` or assume POSIX roots;
- cache activation uses ordinary files/directories rather than symlinks, and closes file handles before rename/replacement to avoid Windows locking failures;
- temporary build directories live under the target cache directory so activation does not cross volumes;
- process startup and shutdown will not depend on Bash, `fork`, `fcntl`, executable shebangs, or Unix-only signals; `concurrently --kill-others-on-fail` handles paired development processes;
- tests use OS temporary directories and normalize path assertions rather than hard-code slash direction;
- source and generated JSON use UTF-8, parsing normalizes Unicode to NFC, and tests include curly quotation marks and em dashes common in talk text;
- `.gitattributes` will keep source text predictable while code never relies on a particular working-tree line ending;
- README examples will show PowerShell commands for copying `.env.example` (`Copy-Item .env.example .env`) and setting up the project;
- command verification will be performed in the actual project-local Windows environment using Node 22+ and the pinned project tooling.

## 12. Verification sequence

The developer should implement and verify in this order so later layers depend on proven invariants:

1. Establish package scripts, TypeScript builds, environment parsing, shared schemas, `.gitignore`, and safe `.env.example`.
2. Implement parsing against small fixtures, corpus validation, deterministic chunking, and embedding-cache behavior; run importer unit tests before contacting official pages.
3. Run `npm run import` against the official collection, record exactly 37 talks, manually spot-check paragraph boundaries/metadata for talks from multiple sessions plus closing remarks, rerun to prove embedding cache hits, and confirm a failed staged import cannot replace the active index.
4. Implement `CorpusStore` and retrieval; test full-index scoring, deterministic ranking, and per-talk diversity with controlled vectors.
5. Implement strict synthesis schema, semantic citation validation, retry/error mapping, and deterministic excerpts with mocked OpenAI responses.
6. Implement API limits, rate limiting, logging redaction, secret containment, and route tests.
7. Implement the React state machine and accessible interface; test validation, loading, all three evidence states, configuration errors, provider errors, keyboard submission, focus movement, and source rendering.
8. Run `npm test`, `npm run build`, inspect the built client for the test API-key sentinel and environment variable names/values, and start the production server from built artifacts.
9. Test at 320px, a representative mobile width, and desktop width; perform keyboard-only navigation, visible-focus, live-region, reduced-motion, contrast, and horizontal-overflow checks.
10. With a real key only in the optional manual check, run the five specified prompts. Record retrieved/cited IDs, evidence status, unique coverage count, and reviewer observations without recording full user questions in application logs.
11. For every manual result, open each official link and verify speaker/title/URL, exact excerpt text, fair synthesis, unique cited-talk count, and absence of claims about uncited leaders. The college-major prompt should be limited/none unless its citations directly address that choice.
12. Finish README and `IMPLEMENTATION.md` with exact Windows setup/run commands, architecture, source/cache limitations, actual command results, acceptance results, and remaining limitations.

## 13. Requirement-to-check matrix

| Requirement | Planned component/control | Verification |
|---|---|---|
| Fixed October 2026 English scope and visible 37-talk identity | Import URL constant, corpus invariant, header badge/description | Import integration count; UI assertion for exact conference text and badge |
| Exactly 37 authored talks; exclude non-talk pages; include closing remarks | Collection/talk classifiers and `validateCorpus` | Fixture rejection tests; real import report and manual closing-remarks spot-check |
| Required talk metadata and ordered body only | `parseTalk`, normalized `TalkRecord`, scoped body selectors | Parser fixtures with page furniture/footnotes; manual multi-session source comparison |
| Unique IDs/URLs, official HTTPS host, nonempty and non-short body | `validateCorpus`, stable slug ID, 300-word named minimum | Tests for missing, duplicate, wrong-host, and short records; importer nonzero exit |
| No partial production corpus | Versioned staging plus validated `active.json` activation | Forced failure test confirms old active index remains unchanged |
| Full text/chunks/embeddings ignored | `.gitignore` and `.cache/conference-compass` | `git status --ignored`; repository scan for full source fixtures |
| 350–650-word paragraph-aligned passages with overlap | Deterministic `chunk.ts`, one-paragraph overlap | Boundary/order/no-loss tests including long paragraph and punctuation |
| Stable passage IDs and retained offsets/embedding | Content-hashed ID and passage schema | Repeat-run equality test; schema/offset/vector validation |
| Batched embeddings and unchanged-work cache reuse | Model/text-hash cache and batch embedder | Mock call-count tests; second real import reports zero passage cache misses |
| Query trims/rejects empty and oversized input | Shared 1,000-code-point validation client/server | Unit and UI tests for whitespace, boundary, over-limit, Unicode |
| Search every indexed passage | Exhaustive cosine loop before top-pool selection | Retrieval test asserts scored count equals complete synthetic index |
| Normally 12–18 candidates, per-talk diversity | Target 16, pool 60, max two/talk constants | Retrieval tests for target count, ties, dominance, and small corpus behavior |
| Required OpenAI SDK/models and environment overrides | Server/import OpenAI adapter and config parser | Adapter request assertions; config-default/override tests; active-index model mismatch test |
| Responses API strict Structured Outputs | `synthesis.ts` strict schema with no extra properties | Mock request snapshot and malformed/additional-property response tests |
| Ground every synthesis and theme in retrieved passages | Server citation membership/evidence-state validation; union-of-theme citations beside combined answer | Unknown/non-retrieved/empty citation tests; unsupported theme rejection; UI assertion for answer-adjacent citations |
| Handle malformed, refusal, timeout, incomplete output | Typed provider errors and one controlled retry | Mock tests for retry count and each stable API error code |
| Limited/no evidence avoids generic answers | Semantic state invariants and dedicated UI branches | No-evidence tests require zero themes/sources/quotes; acceptance prompts 4–5 review |
| Exact source excerpts, no more than 24 words | Server-side offset slicing and pre-serialization assertion | Contiguous substring, punctuation, contractions, long sentence, and 24-word tests |
| Trusted attribution and official links | Corpus metadata join; model cannot set source metadata | Malicious model-field test; URL-host import test; manual link verification |
| Deduplicated sources and accurate X-of-37 count | Passage source map and unique cited talk set | Repeated-passage/talk tests; manual count comparison |
| Required UI regions, copy, examples, and actions | Header, form, results, theme/source components | Testing Library assertions against exact required labels/prompts and reset action |
| Meaningful progress and no duplicate submission | Client request state/guard and live status | Deferred-promise UI test verifies messages, disabling, and one network call |
| Distinct validation/config/network/provider/corpus errors | Typed API/client state machine | UI tests for each error response and network rejection |
| Mobile/desktop, calm independent visual design | Responsive CSS, no official assets, fluid layout | 320px/mobile/desktop manual inspection and horizontal-overflow check |
| Accessible semantics, keyboard, focus, announcements, motion | Landmarks, labels, live regions, focus management, CSS media query | Automated accessibility-oriented queries plus keyboard/manual screen-reader checks |
| API key server-only and absent from output | Server/import env boundary, fixed response DTO, no `VITE_` secret | Sentinel scan of `dist/client`; serialized error/response tests; repository secret scan |
| No question persistence or production full-question logs | Request-local state and metadata-only logger | Logger spy test and cache/log inspection after request |
| Request limits/rate limiting/safe rendering | Express body cap, limiter, React text rendering | Oversize/429 route tests and hostile corpus/model string rendering test |
| Required commands and failure codes | Root `package.json` scripts | Clean `npm install`; run import/dev/build/test; deliberate failing-test/build checks as appropriate |
| Five shared acceptance prompts | Manual acceptance worksheet in implementation notes | Record evidence status, citations, excerpts, fairness, and counts for all five |
| Documentation and independent-project disclaimer | README and persistent header/footer copy | README checklist; UI text assertion |

## 14. Risks and requirements needing explicit handling

- **Official page shape may change or require client-rendered data.** The importer needs fixture-backed parsing for both structured data and semantic HTML plus loud diagnostics. It must fail rather than guess when selectors stop yielding 37 valid talks.
- **The specification does not define a canonical 37-URL manifest.** Discovery will be tied to the frozen collection URL and strict authored-talk validation. The successful real import manifest should be retained locally for review; only metadata/short test excerpts may be committed. If the collection yields a different count, import stops and the discrepancy is reported rather than silently adding/removing pages.
- **“Suspiciously short” is qualitative.** This plan chooses 300 words as a centralized initial threshold. It must be checked against the real shortest authored talk; if a valid talk is shorter, the developer should adjust the named threshold with a documented corpus-based reason and a regression test, not add a one-off bypass.
- **The official site may restrict automated requests.** Fetches should use modest bounded concurrency, retries, caching, and a descriptive user agent. The importer must not scrape alternate unofficial sources to make the count pass.
- **Exact excerpt usefulness is subjective.** The deterministic lexical strategy prioritizes auditability. It deliberately omits a quote when overlap is not meaningful, which the specification permits, while retaining attribution and link.
- **Model output can be structurally valid but semantically overstated.** Citation membership cannot prove entailment. The grounding prompt, constrained context, manual five-prompt review, and visible read-in-context note mitigate this; the limitation must be documented.
- **Rate limiting is process-local.** That is appropriate for the local class-project server. A multi-instance deployment would require a shared limiter and trusted proxy configuration; this is outside the stated first-version scope and should be documented.
- **October 2026 content availability is external.** A clean install still requires network access and an API key to create embeddings. Cached full content cannot be committed under the specification, so setup documentation must state these prerequisites clearly.

No frozen-spec edit is required. Any implementation deviation from the concrete constants or architecture above should be recorded in `IMPLEMENTATION.md` with its reason and corresponding test update.
