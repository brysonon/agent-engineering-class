# Conference Compass review

## Review outcome

Phase 5 final verification is **ready**. All four phase-3 findings below have been resolved and independently rechecked. No actionable finding remains; the historical findings are retained to show the acceptance conditions that were verified.

## Findings

### P1 — Model-authored direct quotations can be displayed as synthesis

**Evidence.** In a real production-served request for `What was said about gambling?`, the theme “Clear opposition from Church leaders” rendered a model-authored sentence containing the purported direct quotation `“We are against it,”`. The linked official “O Be Wise” page contains that language, but it appeared inside the synthesis paragraph rather than in a server-extracted source excerpt. This blurs the product’s required distinction between the app’s synthesis and speakers’ words and violates the grounded-synthesis requirement to paraphrase rather than generate quotations.

The prompt asks for paraphrase (`app/server/synthesis.ts:9`), but runtime validation checks only structure, theme counts, and passage-ID membership (`app/server/validation.ts:5-35`). `AnswerService` then returns model-authored `answer`, `synthesis`, and `closingNote` strings unchanged (`app/server/answerService.ts:70-73`), and the client displays theme synthesis as ordinary result text (`app/client/src/App.tsx:42-47`). The live integration check passed because it validates only `response.sources[].excerpt`, not quote-like language in model-owned fields (`app/server/integration.ts:21-31`). This is a concrete example of the current checks producing false confidence.

**Acceptance condition.** Model-owned answer, theme, and closing text must not display purported source quotations. Add server-side enforcement that rejects and retries such output, plus a regression test with a structured model response containing a direct quotation. Re-run the gambling prompt and verify that source wording appears only in server-derived source excerpts, each still contiguous and no more than 24 words.

### P2 — The source list is deduplicated by passage, not by talk

**Evidence.** The live gambling result displayed two source cards with the same speaker, talk title, and canonical URL for “O Be Wise.” The five-prompt integration run likewise returned 14 source cards from 10 talks for the faith prompt, 12 cards from 8 talks for the Christlike prompt, and 10 cards from 6 talks for covenants. The specification calls for a deduplicated source list whose entries are identified by speaker, talk title, and full-talk link.

`AnswerService` deduplicates cited passage IDs and creates one source record per passage (`app/server/answerService.ts:59-68`). The client then creates one full source card per record (`app/client/src/App.tsx:15-25`). Repeated passages from one talk therefore repeat the talk attribution and identical external link.

**Acceptance condition.** Render one source card and one full-talk link per unique talk/canonical URL. Preserve passage-level citation targets and distinct exact excerpts within the grouped talk card so each theme citation remains traceable. Add a test where two cited passages belong to one talk; the result must have one talk card, and the coverage count must equal the number of rendered unique talk cards.

### P2 — Error and retry flows lose keyboard focus

**Evidence.** Against a production server started without an API key, the readiness warning appeared correctly. Submitting with Enter produced the distinct missing-configuration error and an alert, but browser accessibility state showed focus on the page web area rather than the error heading or retry control. Clicking `Try again` removed the error panel and again left focus on the page web area instead of returning it to the question field.

Success and `Ask another question` focus are implemented, but the error branch has no focus target and its retry handler only changes state (`app/client/src/App.tsx:74,94,117`). This misses the specification’s logical focus-movement requirement for submission and starting another question.

**Acceptance condition.** Move focus to the error heading (or another logical error target) when a request fails, and move focus to the question field when `Try again` is activated. Cover both transitions with a keyboard-focused UI test.

### P3 — The implementation record contains a stale passage count

**Evidence.** `IMPLEMENTATION.md` first states that the importer creates 91 passages, then states that retrieval scores all 108 passages. The independent import produced 37 talks and 91 passages, with 91 embedding-cache hits and no misses; the active index also contains 91 unique passage IDs.

**Acceptance condition.** Correct the delivered-architecture description to 91 passages (or describe the count as corpus-generated rather than hard-code it) so the implementation record agrees with the active validated index and command results.

## Verification performed

- Loaded the project-local `reviewer` role and followed phase 3 of `WORKFLOW.md`.
- Read `../SPEC.md`, `PLAN.md`, `IMPLEMENTATION.md`, `README.md`, configuration, importer, server, client, and all automated tests.
- `pnpm test`: passed, 8 files and 17 tests.
- `pnpm run typecheck`: passed for both TypeScript projects.
- `pnpm run build`: passed; production client and server artifacts were generated.
- `pnpm run import`: passed with 37 talks, 91 passages, 91 cache hits, and 0 misses.
- Active-index inspection: 37 unique talk IDs, 37 unique official canonical URLs, 91 unique passage IDs, uniform 1,536-dimension embeddings, and no missing session/role/summary fields.
- `pnpm run test:integration`: completed all five required live API prompts. Evidence states were sufficient/sufficient/sufficient/sufficient/none; the college-major prompt returned zero themes, sources, and cited talks.
- Started the built production server and verified `/` returns the app, `/api/status` reports ready/configured with 37 talks, invalid content types return 400, and `X-Powered-By` is absent.
- Used the served UI by keyboard: Shift+Enter inserted a line, Enter submitted, duplicate controls were disabled while loading, the two loading messages appeared, success moved focus to the results heading, and `Ask another question` returned focus to the textarea.
- Spot-checked the gambling result against its live official “O Be Wise” page. The speaker, title, canonical URL, and displayed server excerpts matched the official talk, and the excerpts were exact stored substrings within the 24-word limit.
- Started a production server without an API key and verified the dedicated readiness and request-error messages without any secret or stack exposure.

## Review limits

- The live integration script mechanically verifies citation membership, excerpt exactness, and coverage counts. Semantic entailment remains a manual judgment; this review inspected the gambling result in detail but did not manually audit every theme from all five nondeterministic model responses.
- The browser harness available to this reviewer did not expose a viewport override, so 320-pixel behavior was assessed from the responsive CSS rather than a real 320-pixel browser session. The desktop served layout was visually inspected.
- System `npm` was unavailable. The documented bundled `pnpm` runtime executed the equivalent project scripts; a fresh `npm install` was not repeated in this review.

## Phase 5 final verification

All recorded acceptance conditions passed:

- **P1 quotation boundary — resolved.** `validateSynthesis` now examines the answer, closing note, theme titles, and theme synthesis for direct-quotation markers and raises a retryable `synthesis_invalid` error. The focused mock test proved that a first response containing `“We are against it.”` is rejected, a second provider request is made with the grounding correction, and only the paraphrased response is accepted. The live gambling integration check and a separate request through the built production `/api/answer` route both passed with five themes and no quotation marker in any model-owned field. The only displayed quotations are the two server-derived exact excerpts.
- **P2 talk-level source deduplication — resolved.** The server groups cited passages by canonical talk URL and derives coverage from those groups. The focused server/client tests proved that two cited passage IDs remain distinct anchors and excerpts under one talk card with one full-talk link. The live built-server gambling response contained one `O Be Wise` source card, two passage anchors, one unique canonical URL, one full-talk link, and `usedTalkCount: 1`. Both excerpts were present, exact stored-source slices, and 24 words each.
- **P2 error/retry focus — resolved.** The error heading is programmatically focusable and receives focus after a failed request. Keyboard navigation reaches `Try again`, and activating it returns focus to the populated question textarea. The focused Testing Library keyboard test passed this complete sequence.
- **P3 stale passage count — resolved.** `IMPLEMENTATION.md` now consistently states that retrieval scores all 91 passages. A repeat real import independently produced 37 talks and 91 passages with 91 embedding-cache hits and zero misses.

Final command and runtime evidence:

- Focused regressions: 3 test files and 8 tests passed (`synthesis.test.ts`, `answerService.test.ts`, and `App.test.tsx`).
- Full mocked suite: 10 test files and 23 tests passed.
- `pnpm run typecheck`: passed for the client and server TypeScript projects.
- `pnpm run build`: passed; Vite emitted the production client and server TypeScript compiled.
- `pnpm run import`: passed with 37 talks, 91 passages, 91 cache hits, and zero misses.
- Targeted live `INTEGRATION_PROMPT=4` check: sufficient evidence, five themes, one source card, two cited passages, one covered talk, and two exact excerpts.
- Built production server: `/` returned 200 with the app title; `/api/status` reported corpus ready, API configured, and 37 talks; `X-Powered-By` remained absent.

Final verification limits remain the same in substance: semantic entailment still requires human judgment, system `npm` was unavailable, and a fresh clean install was not repeated. The browser provider was unavailable during phase 5, so the repaired focus/rendering paths were verified with the focused DOM/keyboard tests and the production-served JSON contract rather than another interactive browser session. Phase 3 had already established the desktop served layout and keyboard baseline. These limits do not leave an actionable acceptance failure.
