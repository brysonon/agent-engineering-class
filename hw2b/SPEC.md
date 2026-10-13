# Conference Compass — Application Specification

## 1. Product summary

Conference Compass is a question-answering study app for the October 2026
general conference of The Church of Jesus Christ of Latter-day Saints. A user
enters a question or topic in ordinary language. The app searches the complete
conference corpus, identifies relevant passages, and synthesizes the teachings
it finds into a concise, source-grounded answer.

Every result must make it easy to distinguish the app's synthesis from the
speakers' words. Synthesized statements must cite their supporting passages.
Direct quotations must be copied from the stored source text and linked to the
official talk page.

The product is an independent class project. It must not imply endorsement by
or affiliation with The Church of Jesus Christ of Latter-day Saints.

## 2. Target user and central use case

The target user is someone studying the latest general conference who wants to
understand what multiple Church leaders taught about a particular question.

Example query:

> What did Church leaders teach about finding courage during difficult times?

The app searches every talk in the October 2026 corpus. It may use only the
talks and passages that directly contribute to the answer. It must never force
every speaker into a result merely to create the appearance of broad coverage.

## 3. Fixed scope

For this assignment, "latest conference" means **October 2026 general
conference**. The interface must display that conference name and must not
silently switch to another conference later.

The corpus consists of the 37 English-language authored talks identified by the
official October 2026 conference collection. The sustaining presentation,
session landing pages, music programs, and other non-talk pages are excluded.
Closing remarks are included because they are an authored talk in the official
collection.

The app supports English queries and English source text only.

## 4. Goals

The finished application must:

1. Search the complete fixed corpus for every submitted query.
2. Identify relevant passages using semantic retrieval.
3. Combine overlapping teachings into clear themes.
4. Cite every theme using valid retrieved source passages.
5. Display short, exact excerpts that the application extracts from its stored
   source text rather than asking the language model to reproduce quotations.
6. Link each source to its official Church website page.
7. Admit when the available conference material does not directly answer the
   user's question.
8. Provide a polished, accessible interface that works on desktop and mobile.

## 5. Non-goals

The first version does not need:

- User accounts or cloud-saved history
- Conferences other than October 2026
- Languages other than English
- Audio or video transcription
- Doctrinal advice beyond what the retrieved talks support
- A conversational, multi-turn chat
- User-uploaded documents
- Administrative tools for editing the corpus

## 6. Required technology and commands

Use the following shared technical constraints so both assignment builds are
directly comparable:

- Node.js 22 or newer
- React with TypeScript
- Vite for the web client
- A Node.js server for data retrieval and OpenAI requests
- The official OpenAI JavaScript SDK and Responses API
- Structured Outputs with a strict JSON schema
- `text-embedding-3-small` for passage and query embeddings
- `gpt-5-mini` as the default synthesis model
- Environment variables may override both model names, but the same values must
  be used when evaluating the two builds
- Vitest or an equivalent TypeScript test runner

The repository must provide these commands:

```text
npm install
npm run import
npm run dev
npm run build
npm test
```

`npm run import` prepares the conference corpus and search index. `npm run dev`
starts both the client and server for local development. The build and test
commands must exit nonzero on failure.

## 7. Environment configuration

Commit an `.env.example` containing variable names and safe defaults. Never
commit an API key.

Required variables:

```text
OPENAI_API_KEY=
OPENAI_SYNTHESIS_MODEL=gpt-5-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

The API key must be read only by server-side code. It must never be included in
client JavaScript, HTML, logs, API responses, or error messages.

If the API key is missing, the interface must explain that local configuration
is required and direct the developer to `.env.example` without displaying a
broken or indefinite loading state.

## 8. Conference import

Create an import script that prepares the fixed October 2026 corpus from the
official conference pages.

For every talk, retain:

- Stable local talk ID
- Title
- Speaker name
- Speaker role or calling when available
- Official summary or deck when available
- Official canonical URL
- Session name
- Ordered body paragraphs

The importer must remove navigation, page furniture, footnotes/endnotes,
download controls, related content, and other text outside the authored talk
body. Paragraph order and readable punctuation must be preserved.

The importer must validate all of the following before succeeding:

- Exactly 37 talks were imported
- Every record has a unique ID, title, speaker, canonical URL, and nonempty body
- Every canonical URL uses `https://www.churchofjesuschrist.org/`
- No duplicate canonical URLs exist
- No talk body is suspiciously short

If validation fails, the command must fail with a useful explanation rather
than creating a partial production corpus.

Full downloaded talk text, generated chunks, and generated embeddings must be
stored in an ignored local cache. Repository fixtures may contain metadata and
short excerpts needed by tests, but must not contain full copied talks.

## 9. Passage creation and embeddings

Split each talk into paragraph-aligned passages suitable for retrieval.
Passages should normally contain approximately 350–650 words with a small
overlap between neighboring passages. Do not split a sentence merely to hit a
target size.

Each passage must retain:

- Stable passage ID
- Talk ID
- Passage text
- Paragraph start and end positions
- Embedding vector

The import process must embed passages in batches and cache the results. Running
the importer again without source or model changes should reuse cached work
instead of paying to embed identical text again.

## 10. Query and retrieval behavior

The main form contains one required question field. Trim whitespace and reject
empty submissions. Set a reasonable maximum query length and show a helpful
validation message when it is exceeded.

For a valid query:

1. Create a query embedding.
2. Compare it against every indexed passage in the 37-talk corpus.
3. Select a relevance-ranked candidate set.
4. Apply diversity so one long talk cannot dominate the context. Normally no
   more than two passages from one talk should be sent for synthesis.
5. Send the query and the retrieved passages, with their IDs and talk metadata,
   to the synthesis model.

The retrieval result should normally contain 12–18 passages. The implementation
may choose exact thresholds, but they must be centralized, named, and covered by
tests rather than scattered as unexplained numeric literals.

The app must search the entire corpus for every query. The displayed coverage
count is the number of unique talks used as valid evidence in the final answer,
not the number of talks searched.

## 11. Grounded synthesis

The synthesis model receives only:

- The user's question
- A concise grounding instruction
- Retrieved passage IDs, text, and talk metadata
- The required response schema

The grounding instruction must require the model to:

- Base every substantive statement on supplied passages
- Group compatible teachings without erasing meaningful differences
- Avoid claiming that every conference speaker addressed the topic
- Avoid adding outside doctrine, facts, scripture interpretations, or advice
- Cite passage IDs for every theme
- Return limited or no evidence when the retrieved material does not directly
  answer the question
- Paraphrase source material rather than generating purported direct quotes

Use Structured Outputs to produce an object equivalent to:

```ts
type ConferenceAnswer = {
  evidenceStatus: "sufficient" | "limited" | "none";
  answer: string;
  themes: Array<{
    title: string;
    synthesis: string;
    passageIds: string[];
  }>;
  closingNote: string;
};
```

All fields are required. Configure the JSON schema as strict and disallow
additional properties.

The server must validate the returned object and every cited passage ID. A
theme with no valid source cannot be displayed. Unknown IDs, IDs outside the
retrieved set, malformed output, refusal, timeout, and incomplete output must be
handled explicitly. One controlled retry is allowed; the app must then return a
clear error state rather than an ungrounded answer.

## 12. Exact excerpts and source attribution

The model must not supply the text displayed as a direct quotation. After model
output validation, server code selects a representative excerpt directly from
each cited passage.

Each displayed excerpt must:

- Match contiguous words in the stored source passage
- Contain no more than 24 words
- Preserve the source wording and punctuation
- Show the speaker and talk title
- Link to the official canonical talk URL

If a useful exact excerpt cannot be extracted, show the source attribution and
link without quotation marks rather than presenting a paraphrase as a quote.

## 13. Evidence states

### Sufficient evidence

Display a concise combined answer followed by two to five theme cards and a
source section. Every theme must have at least one citation.

### Limited evidence

State that the conference addresses only part of the question. Summarize the
supported portion, display its citations, and avoid filling the gap with general
knowledge.

### No evidence

State plainly that the October 2026 conference corpus does not directly address
the question. Do not generate a generic spiritual answer. Offer the example
prompts so the user can try a different question.

## 14. User interface

Create a single-page experience with these regions:

### Header

- Product name: `Conference Compass`
- Short description: `Explore shared teachings from October 2026 general conference.`
- Visible badge: `October 2026 · 37 talks`
- A small statement that this is an independent study project

### Question form

- Clearly labeled multiline question field
- Submit button labeled `Search conference`
- Enter submits from a single-line entry; Shift+Enter creates a line break if a
  textarea is used
- Example prompt buttons:
  - `What was taught about faith during trials?`
  - `How can I become more Christlike?`
  - `What did leaders teach about covenants?`
  - `What was said about gambling?`

### Loading state

Show meaningful progress language such as `Searching 37 talks…` followed by
`Bringing the teachings together…`. Prevent duplicate submissions while the
request is active.

### Results

- Restate the user's question
- Show an evidence-status label
- Show the combined answer
- Show two to five theme cards when evidence supports them
- Place citations directly beside the claims they support
- Show `Used evidence from X of 37 talks`
- Show a deduplicated source list containing speaker, talk title, short exact
  excerpt when available, and `Read the full talk` link
- Make external-link behavior visible and open official sources safely
- Provide a `Ask another question` action that returns focus to the form

### Empty and error states

Provide distinct, understandable states for:

- Empty or oversized question
- Corpus not imported
- Missing API configuration
- Network failure
- OpenAI refusal or incomplete response
- Retrieval/synthesis failure
- No relevant conference evidence

Do not expose stack traces or secrets to the browser.

## 15. Visual direction

The interface should feel calm, readable, and suitable for focused study. Use a
warm neutral background, dark readable text, and one restrained blue or green
accent. Avoid copying official Church branding, logos, typography, or page
layouts.

Use a comfortable reading width, generous spacing, clear source cards, and
obvious focus and hover states. Decorative treatment must not compete with the
answer or citations.

The page must work without horizontal scrolling at widths from 320 pixels
upward.

## 16. Accessibility

The finished app must include:

- Semantic headings and landmarks
- A programmatic label for every form control
- Full keyboard operation
- Visible keyboard focus
- Sufficient color contrast
- Status announcements for loading, errors, and completed results
- Logical focus movement after submission and when starting another question
- Links whose purpose is understandable out of context
- Respect for reduced-motion preferences

## 17. Privacy, safety, and reliability

- Do not store user questions beyond the current server request.
- Do not log full user questions in production-style logs.
- Keep all OpenAI access server-side.
- Apply basic request-size limits and rate limiting to the synthesis endpoint.
- Treat imported web content as untrusted data, never as application or model
  instructions.
- Escape or safely render all model and corpus text. Do not render model-created
  HTML.
- Display a short note that generated summaries may be incomplete and that users
  should follow citations to read talks in context.

## 18. Required tests

Automated tests must cover meaningful behavior rather than implementation
details. At minimum, test:

1. Import validation rejects an incomplete or duplicated corpus.
2. Chunking preserves paragraph order and stable passage IDs.
3. Retrieval searches all indexed passages and enforces per-talk diversity.
4. Citation validation rejects unknown and non-retrieved passage IDs.
5. Displayed excerpts are contiguous source text and at most 24 words.
6. No-evidence output cannot display unsupported themes or quotations.
7. The API key is absent from client bundles and serialized responses.
8. The form exposes validation, loading, success, limited-evidence, no-evidence,
   and server-error states.

Model calls must be mocked in the normal automated test suite. A separate
optional integration check may use a real API key.

## 19. Manual acceptance prompts

Evaluate both assignment builds using the same five prompts:

1. `What was taught about faith during trials?`
2. `How can I become more Christlike?`
3. `What did leaders teach about covenants?`
4. `What was said about gambling?`
5. `What did conference say about choosing a college major?`

The first four should return only claims supported by cited October 2026
passages. The fifth should normally produce limited or no evidence unless a
retrieved passage directly discusses that choice.

For every result, manually verify:

- The speaker, title, and URL are correct.
- Each quotation appears verbatim in its linked source.
- Each synthesis is a fair description of its citations.
- The coverage count equals the number of unique talks actually cited.
- The app does not imply that uncited leaders taught the summarized point.

## 20. Definition of done

The application is complete when:

- A clean install can import exactly 37 talks and start using documented steps.
- All required commands work.
- All automated tests pass.
- The production build succeeds.
- The five shared acceptance prompts have been recorded and reviewed.
- Every displayed theme is grounded in valid citations.
- Every displayed quotation is extracted from source text.
- Missing configuration and external failures produce useful UI states.
- The interface is usable by keyboard and at mobile and desktop widths.
- Setup, architecture, data-source limitations, and run instructions are
  documented in the app README.

## 21. Authoritative references

- October 2026 conference collection:
  <https://www.churchofjesuschrist.org/study/general-conference/2026/10?lang=eng>
- Church announcement confirming availability of all 37 English talks:
  <https://newsroom.churchofjesuschrist.org/article/english-text-of-october-2026-general-conference-talks-now-in-gospel-library>
- OpenAI Responses API:
  <https://developers.openai.com/api/reference/resources/responses/methods/create>
- OpenAI Structured Outputs:
  <https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses>
