# Shared Acceptance Checklist

Both builds used the same October 2026 conference, default model names, API
configuration, evaluation prompts, and browser sizes.

| Check | Baseline | Harness | Notes |
| --- | --- | --- | --- |
| Imports exactly 37 authored talks | Pass | Pass | Sustaining presentation excluded; closing remarks included |
| Production build succeeds | Pass | Pass | TypeScript and Vite passed |
| Automated tests pass | Pass: 4 tests | Pass: 23 tests | Harness tests span 10 files |
| Empty question is rejected accessibly | Pass | Pass | Error text is announced and focus stays/moves logically |
| Missing API configuration has a useful state | Pass | Pass | Both explain how to configure the key |
| Loading state prevents duplicate submission | Pass | Pass | Harness also has an active-request guard |
| Source title, speaker, and official link are correct | Pass | Pass | Gambling result spot-checked against **O Be Wise** |
| Source list is deduplicated by talk | Needs fix | Pass | Baseline creates one card per passage; harness groups passages under one talk card |
| Model prose is paraphrased rather than quoted | Prompt only | Pass | Harness validates quote markers and retries |
| Every displayed excerpt is verbatim and 24 words or fewer | Needs fix | Pass | Baseline can place a generated ellipsis inside the displayed quotation |
| Coverage count equals unique cited talks | Pass | Pass | Harness derives coverage from rendered talk groups |
| Unrelated question returns limited/no evidence | Pass: limited | Pass: none | Both avoid claiming direct conference coverage |
| Keyboard navigation and focus are usable | Pass | Pass | Harness review specifically tested error and retry focus |
| Layout works at 320 px and desktop width | Pass | Pass | Edge reported zero horizontal overflow |
| Browser client contains no API key | Pass | Pass | Harness also scans the production bundle in tests |

## Shared prompt results

| Prompt | Baseline | Harness |
| --- | --- | --- |
| What was taught about faith during trials? | Sufficient; 4 themes; 11 talks | Sufficient; 5 themes; 10 talks |
| How can I become more Christlike? | Sufficient; 3 themes; 11 talks | Sufficient; 5 themes; 9 talks |
| What did leaders teach about covenants? | Sufficient; 4 themes; 9 talks | Sufficient; 5 themes; 6 talks |
| What was said about gambling? | Sufficient; 1 talk | Sufficient; 1 talk |
| What did conference say about choosing a college major? | Limited; 4 themes; 6 talks | None; 0 themes; 0 talks |

Counts are observations from the recorded runs and may vary because synthesis is
nondeterministic. Citation membership, exact excerpts, and coverage counts are
validated independently of those exact theme counts.
