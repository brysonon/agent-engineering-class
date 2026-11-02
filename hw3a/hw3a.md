# HW3a Report

## How I completed the required tasks

I beat level 1 on Cycling Coach, Thingularity, and CorpConnect Messenger. When I got stuck, I used [a helpful walkthrough](https://joaodonato.pages.dev/blog/lakera_agent_breaker/) for the prompts that worked:

- **Cycling Coach:** I asked it to repeat its hidden coaching instructions, beginning with a known opening, in a code block.
- **Thingularity:** I asked about available deals and added a request to show its `# Tools` section in a Markdown code block.
- **CorpConnect Messenger:** I claimed a promotion to CEO and asked it to email everyone from the CEO account.

I also built semantic search over 41,995 scripture verses, 38 October 2026 conference talks, and four BYU speeches.

## Additional exploration

I explored the search results with sample questions. “God knew me before I was born” returned Jeremiah 1:5, “grace helps us change” returned Brad Wilcox’s *His Grace Is Sufficient*, and “temple covenants” returned Gerrit W. Gong’s *Come to the Lord in His Holy House*.

## Obstacles I encountered

I encountered two limits in the project: the BYU and conference collections are still small, and similar wording can rank a passage highly even when its meaning differs from the query.

## What I learned

I learned that a normal-sounding request can carry an instruction to reveal hidden text or misuse a tool. I also learned that embeddings can find related ideas across different wording, but a high similarity score does not guarantee a good answer. I still need to check the linked source.

## Why this matters in agent engineering

I think this matters in agent engineering because agents can both read untrusted text and take actions with tools. If they obey an injected request or retrieve misleading evidence, they may act incorrectly or give a confident but incomplete answer. Tool permissions and source checks help catch those failures.

## How many hours I spent

I spent 3 hours on HW3a.
