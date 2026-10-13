# Conference Compass implementation record

## Delivered architecture

The application follows the independent plan: a Vite/React/TypeScript client, an Express/TypeScript server, an official-site importer, OpenAI `text-embedding-3-small` retrieval, and `gpt-5-mini` synthesis through the Responses API with strict Structured Outputs. The browser receives no key, embeddings, full corpus, prompt, raw provider response, or model-provided attribution.

The importer downloads official HTML into the ignored cache, discovers 42 conference/session candidates, parses 38 talk-shaped pages, excludes the sustaining presentation by its official title, and validates the remaining 37 authored talks including Closing Remarks. It creates 91 deterministic paragraph-aligned passages. Every ordinary passage contains at least 350 words; the only shorter passage is the complete 287-word Closing Remarks talk, and overlap brings the observed maximum to 689 words. Index activation is versioned and staged; failures before activation preserve the preceding pointer. Embeddings are keyed by schema version, model, and normalized passage text.

Retrieval scores all 91 passages on every query, ranks a top-60 pool, selects up to 16 passages, and enforces a two-passage-per-talk limit. Synthesis validates strict structure, evidence-state theme counts, unique citations, membership in the exact retrieved set, and the absence of direct-quotation markers in model-authored answer, theme-title, theme-synthesis, and closing text. A retryable violation receives one controlled retry. Trusted talk metadata is joined afterward. Exact excerpts use original character slices and are rechecked for contiguous membership and the 24-word limit.

The client includes all specified header/form/example copy, Enter and Shift+Enter behavior, validation, two-stage loading announcements, a duplicate-request guard, sufficient/limited/no-evidence layouts, claim-adjacent passage citation links, one source card/link per canonical talk with distinct passage excerpt anchors, accurate coverage, configuration and provider errors, success/reset/error/retry focus movement, visible focus styles, responsive layouts, and reduced-motion handling.

## Verification results

Environment: Windows PowerShell, Node.js `v24.19.0`. npm was not installed in this class runtime, so the provided bundled pnpm command was used for installation and every script. The standard `npm ...` commands remain the repository interface and use package-manager-neutral scripts.

| Check | Result |
|---|---|
| Dependency install | Passed; 257 initial packages plus `cross-env`, pnpm lockfile created |
| `pnpm run typecheck` | Passed for client and server TypeScript projects |
| `pnpm test` | Passed after phase-4 fixes: 10 files, 23 tests |
| Final real import | Passed: 37 talks, 91 passages; final chunk rebuild reused 11 embeddings and created 80 changed embeddings |
| Repeat real import | Passed: 37 talks, 91 passages, 91 cache hits, 0 misses; pointer replacement succeeded on Windows |
| `pnpm run test:integration` | Passed all five real Responses API prompts and excerpt/coverage invariants |
| `pnpm run build` | Passed after phase-4 fixes; Vite emitted a 228.38 kB client JS bundle (71.68 kB gzip), then server TypeScript compiled |
| Built production server | Passed; `/api/status` returned corpus ready, API configured, and 37 talks; `/` returned 200 with the app title |

The initial real import rejected valid Closing Remarks at 287 words because the planned suspicious-length floor was 300. The centralized floor is now 250, with a regression test accepting a 287-word authored talk and rejecting 249 words. This is a corpus-based adjustment explicitly anticipated by the plan, not a title-specific bypass.

Automated tests cover incomplete and duplicate corpus rejection; the closing-talk length boundary; stable paragraph-order chunking and ordinary-passage size; exhaustive retrieval and talk diversity; unknown citation rejection; no-evidence source exclusion; quote-marker rejection in every model-owned prose field and the resulting controlled retry; exact contiguous 24-word excerpts; grouping two passage citations into one canonical-talk source card with two anchors and one coverage unit; safe API serialization, malformed/oversized bodies, trimmed input, and a real client-build secret scan; and UI validation, loading, success, limited, no-evidence, server-error, error-heading focus, and keyboard retry focus states. Provider calls are mocked in the normal suite.

## Live acceptance results

The optional integration check used the repository-root key without printing or copying it. The initial implementation run sent the five frozen prompts through real query embeddings and `gpt-5-mini`. For every returned passage, the check confirmed that it exists in the active index, any excerpt is an exact contiguous substring containing at most 24 words, and `usedTalkCount` equals the number of unique cited talks.

| Prompt | Evidence | Themes | Cited passages | Talks | Exact excerpts checked |
|---|---:|---:|---:|---:|---:|
| Faith during trials | sufficient | 5 | 14 | 10 | 14 |
| Becoming more Christlike | sufficient | 5 | 13 | 9 | 13 |
| Covenants | sufficient | 5 | 9 | 6 | 9 |
| Gambling | sufficient | 5 | 2 | 1 | 2 |
| Choosing a college major | none | 0 | 0 | 0 | 0 |

The gambling evidence came from the official talk “O Be Wise.” The college-major prompt correctly produced no generic answer, themes, sources, quotations, or claimed coverage. The first three prompts cited several talks without claiming universal conference coverage.

## Phase 4 review fixes

All confirmed findings in `REVIEW.md` were addressed:

- Model-authored answer, theme title, theme synthesis, and closing text are rejected when they contain double quotation marks, opening single quotation marks, guillemets, or paired straight single-quote markers. Ordinary apostrophes in contractions remain valid. The existing synthesis loop retries once with the same evidence and a contract reminder. Only server-derived `source.passages[].excerpt` values may be rendered as quotations.
- Response sources are grouped by canonical talk URL. Each group renders one speaker/title/full-talk link and retains every cited passage ID as its own anchor with its own optional exact excerpt. `usedTalkCount` is derived directly from the rendered talk groups.
- Request failures focus a programmatically focusable error heading. Keyboard navigation reaches `Try again`, and activation restores focus to the populated question textarea.
- The stale retrieval count was corrected from 108 to the active validated count of 91 passages.

The targeted real gambling check passed after these fixes: evidence was sufficient with five themes, one rendered “O Be Wise” source card, two cited passage anchors, one covered talk, and two exact server-derived excerpts. The integration guard confirmed that answer/theme/closing prose contained no direct-quotation markers, while both displayed quotations were contiguous stored-source slices of at most 24 words.

## Remaining limits

- Structural grounding and citation membership are enforced, but automated checks cannot prove perfect semantic entailment. The UI therefore keeps citations beside claims and advises reading full talks in context.
- Official-site markup and availability are external dependencies. Cached official text cannot be committed, so a clean setup requires network access and an API key.
- The in-memory rate limiter is appropriate for the local single-process project; a distributed deployment would need shared state.
- Browser behavior is covered through jsdom state tests and responsive CSS inspection. No screen-reader-specific or device-lab session was performed in this implementation phase.
