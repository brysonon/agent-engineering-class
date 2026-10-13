# HW2b: Building the Same App Two Ways

## What I built

I built **Conference Compass**, an app that searches the 37 authored talks from
October 2026 general conference. A user enters a question, and the app finds
relevant passages, brings similar teachings together, and links every theme to
the official talks that support it.

I used a fixed conference instead of a changing “latest conference” so both
builds would use exactly the same source material. The official collection has
38 numbered content pages: 37 authored talks and the sustaining presentation.
The importer excludes the sustaining presentation and keeps all 37 talks,
including the short closing remarks.

The app uses `text-embedding-3-small` to search the locally imported passages
and `gpt-5-mini` with Structured Outputs to organize the evidence. The model can
paraphrase and return passage IDs, but it cannot create the displayed
quotations or source information. The server copies short excerpts directly
from the cited passage and supplies the trusted speaker, title, and official
link.

## How I completed the assignment

First, I wrote one detailed specification in `SPEC.md`. It defines the corpus,
import process, models, retrieval rules, source requirements, interface states,
security boundaries, accessibility requirements, and five shared evaluation
questions. I froze the specification before either build so the comparison
would be fair.

For the first version, I gave the agent only this build prompt:

> Build the app described in ../SPEC.md.

That produced the app in `baseline-app/`.

For the second version, I made a `myteam` harness in `harness-build/`. It has an
orchestrator and separate Planner, Developer, and Reviewer roles. The roles are
connected by this Markdown workflow:

1. The Planner reads the specification and writes `PLAN.md`.
2. The Developer reads the specification and plan, builds the app, and records
   the results in `IMPLEMENTATION.md`.
3. The Reviewer independently tests the app and writes prioritized findings in
   `REVIEW.md`.
4. The Developer fixes the confirmed findings.
5. The Reviewer verifies the fixes and decides whether the app is ready.

The two versions were then checked with the same conference, model defaults,
browser, and five questions.

## What the development experiences were like

The one-prompt build was fast and direct. It created a working full-stack app
with a polished interface, a 37-talk importer, semantic search, citations, and
four useful unit tests. Because there was no planning or review handoff, I had
to discover weaknesses by running the app myself. The first import rejected the
legitimate closing remarks as too short. The first result excerpts also picked
up page material such as bylines and notes. Both problems were fixed after real
corpus and browser testing.

The harness build took longer before code appeared because the planner first
mapped the specification to components and checks. That extra structure paid
off during review. The reviewer found issues that had passed the developer's
tests: model-written prose included a short direct quotation, two passages from
one talk produced duplicate talk cards, keyboard focus was lost after an error,
and one documentation count was stale. The developer fixed all four findings,
expanded the test suite, and the reviewer completed a second verification pass.

I enjoyed the harness workflow more because each handoff left clear evidence of
what had been decided, built, tested, and fixed. The baseline was more exciting
at the beginning because results appeared quickly, but the harness was easier
to trust by the end. The most useful part was having a reviewer with permission
to reject the build instead of assuming a passing build command meant the app
was finished.

## Comparison of the resulting apps

Both apps work. They import exactly 37 talks, use the same OpenAI models, return
sourced conference summaries, build successfully, and fit both desktop and
320-pixel screens without horizontal overflow. Both correctly found the one
talk that directly discusses gambling. Both also avoided claiming that every
speaker discussed the user's topic.

The harness app is the better final product. It handled the unrelated college
major question more cautiously: the observed harness run returned no evidence,
no themes, and no sources, while the baseline returned a limited answer from six
talks. A limited answer is allowed by the specification, but the harness result
made the corpus boundary clearer.

The harness also has stronger source presentation. Several cited passages from
the same talk are grouped into one talk card and one official link, while each
passage keeps its own citation anchor and exact excerpt. The baseline lists one
card per passage, so the same talk can appear more than once. The baseline can
also append a visual ellipsis inside a displayed quotation; that ellipsis is not
part of the source text. The harness keeps visual quotation marks outside the
stored excerpt and verifies that every excerpt is a contiguous source substring
of no more than 24 words.

After the review fixes, the harness gambling result had five themes, one **O Be
Wise** source card, two passage anchors, two exact excerpts, and a coverage count
of one talk. Browser checks confirmed that model-written answer and theme text
contained no quotation markers. The error heading received focus after a failed
request, `Try again` returned focus to the question box, and the mobile page had
zero horizontal overflow.

## Code comparison

The baseline is much smaller: 8 TypeScript/TSX/CSS source files and about 465
source lines. Its four tests cover chunking, retrieval diversity, citation
filtering, and excerpts. This makes it easy to read, but several responsibilities
are combined in the same files and important behavior depends mainly on the
model following its prompt.

The harness has 36 TypeScript/TSX/CSS source files and about 1,375 source lines.
Its importer, corpus store, retrieval, synthesis, validation, excerpt selection,
API boundary, and React interface are separated into modules. Its final suite
has 23 tests across 10 files. Those tests cover the 37-talk invariant, short
closing remarks, passage boundaries, exhaustive retrieval, citation membership,
quotation rejection and retry, exact excerpts, talk-level source grouping,
request validation, client secret scanning, evidence states, loading behavior,
and keyboard focus.

The harness therefore has better code for this specification, even though it is
larger. Its rules are enforced in server code instead of being left only in a
model prompt. The clearest example is the quotation boundary: the original
harness prompt said to paraphrase, but the reviewer still found quoted wording
in a live answer. The final validator now rejects quote markers in every
model-owned prose field and makes one controlled retry. A regression test proves
that the first invalid response is rejected and the second paraphrased response
is accepted.

## Shared evaluation results

| Question | One-prompt baseline | Harness build |
| --- | --- | --- |
| Faith during trials | Sufficient; 4 themes; 11 talks | Sufficient; 5 themes; 10 talks |
| Becoming more Christlike | Sufficient; 3 themes; 11 talks | Sufficient; 5 themes; 9 talks |
| Covenants | Sufficient; 4 themes; 9 talks | Sufficient; 5 themes; 6 talks |
| Gambling | Sufficient; 1 talk | Sufficient; 1 talk |
| Choosing a college major | Limited; 4 themes; 6 talks | None; 0 themes; 0 talks |

These are observed model runs, so theme and citation counts can vary on a later
run. The mechanical checks do not depend on those exact counts: cited IDs must
come from retrieved passages, coverage must equal unique cited talks, and every
displayed excerpt must be copied from the stored source.

## Obstacles I encountered

- The official collection page contains 38 numbered items because the
  sustaining presentation is listed with 37 authored talks. The importer needed
  an explicit authored-talk boundary.
- A generic minimum-length check rejected valid closing remarks. The baseline
  threshold was lowered after checking the source, and the harness uses a
  tested 250-word lower bound that still catches broken extraction.
- Current `myteam` releases 0.3.21 and 0.2.24 import the Unix-only `fcntl` module
  and fail on Windows. Pinning the project environment to `myteam==0.2.9`
  allowed the role workflow to run.
- Valid citations did not automatically guarantee good presentation. Real
  results exposed irrelevant excerpt selection, duplicate source cards, and a
  direct quotation hidden inside model-written synthesis.
- The class runtime did not have system `npm`, so I used the bundled `pnpm`
  runtime to run the equivalent install, test, import, and build scripts.

## What I learned

I learned that a detailed prompt and a passing build are only the beginning of
an agent-built application. The baseline produced a surprising amount from one
instruction, but real data immediately found assumptions that the unit tests
missed.

I also learned that grounding has several layers. Retrieval must search the
whole index, the model may cite only retrieved passages, source metadata must
come from trusted records, coverage must be calculated rather than generated,
and displayed quotations must be sliced from the source. Even after all of
those rules, a human reviewer can still catch semantic or presentation problems
that mechanical citation checks cannot prove.

The role workflow made review actionable. `REVIEW.md` did not merely say that
something looked wrong; each finding included evidence and a condition the fix
had to satisfy. This gave the developer a concrete target and gave the final
reviewer a repeatable verification step.

## Why this matters in agent engineering

Agents are good at producing a complete first version quickly, but speed can
hide weak assumptions. A development harness adds explicit memory and control
points around the agent: the specification defines success, the plan breaks it
into responsibilities, the implementation record preserves evidence, and the
review can stop the workflow when behavior is wrong.

This experiment showed that more roles do not automatically make the first
version correct. The first harness implementation still had four review
findings. The benefit was that the workflow made those findings visible and
required a fix and verification cycle. The better result came from the feedback
loop, not simply from using more agents.

## Final verification

- Baseline: 37 talks and 110 passages imported; 4 tests passed; type checking
  and production build passed; desktop and 320-pixel Edge checks passed.
- Harness: 37 talks and 91 passages imported; repeat import had 91 cache hits;
  23 tests passed; type checking and production build passed; five live prompts
  passed the grounding checks; reviewer status is **ready**.
- Final harness Edge check: one gambling talk card, two passage excerpts, no
  quotation markers in model prose, correct error/retry focus, and zero mobile
  overflow.
- The API key remained server-side and no key was copied into the client build.

## How many hours I spent

**Actual total: _____ hours.**

I need to replace this blank with my real total before submitting. I should
include the time spent choosing the idea, writing the specification, building
both versions, debugging the import, running the five prompts, reviewing the
apps, and writing this report. The assignment requires at least 3 hours.
