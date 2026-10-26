# HW2e Write-up

## What I did
- **Downloaded the October 2026 General Conference** with `download_gc_talks.py`: 38 talks, about 43k words, one `.txt` per talk in `talks/`.
- **Ingested it into a local ChromaDB** (`ingest.py`) using `ingest_folder` from `chroma_demo.py`: 257 chunks of ~1,200 characters with `text-embedding-3-small`. Cost was under a cent.
- **Built a chatbot** (`chat.py`) that uses RAG as a tool instead of stuffing results into every prompt. The model gets three tools:
    * `search_talks(query)`: semantic search that returns the top 3 *whole* talks.
    * `list_talks()` and `read_talk(filename)`: for questions like "what did President Oaks say," since searching for a speaker's name doesn't work with embeddings.
    * It works one question at a time (`python chat.py "question"`) or as an interactive chat that keeps history for follow-ups.
- **Wrote a system prompt** (`system_prompt.md`) telling the model to always search first, search again with different wording if it misses, quote only exact words, cite speaker and talk, and say plainly when the conference didn't cover something.
- **Built an eval** (`eval.py`) with 12 questions. Ten have a talk I expect it to find, and two (AI, foreordination) the conference never addresses directly. For each answer it checks:
    * whether the agent found the expected talk
    * whether every quoted phrase appears word for word in the talks
    * whether that quote is credited to the right speaker

## Changes to the demo code
- `query_whole_documents` returns one row per *chunk*, so the same talk can come back several times. For "Why do we need prophets today?", 3 of the 5 results were the same Sikahema talk, which would send the whole talk to the model three times. `gc_search.py` pulls extra chunks and keeps only the best one from each talk.

## Results

| | Found expected talk | Quotes verbatim in the talks | Cost (12 questions) |
| --- | --- | --- | --- |
| No RAG (same model, no tools) | - | 5/30 | $0.007 |
| RAG, prompt v1 | 10/10 | 58/60 | $0.025 |
| RAG, prompt v2 | 9/10 | 50/51* | $0.027 |
| OpenAI web search instead of RAG | (see below) | 31/35 | $0.047 + search fees |

\*The one "miss" was a talk title in single quotes, which the checker didn't skip, so v2 was actually 51/51.

- **Without RAG the model mostly made up quotes.** It refused when I named a speaker ("I don't have access to the October 2026 conference"). But on topic questions it confidently quoted things like *"Have I understood your concern correctly?"* as if a speaker said them. The 5 quotes that passed were scripture verses that a speaker also happened to quote.
- **With RAG the quotes were real, but not always credited to the right person.** In an early test, the bot quoted "special [witnesses] of the name of Christ in all the world" and credited it to Elder Caussé. That wording is D&C 107:23 from memory and isn't in any talk. That's why I added the attribution check to the eval.
- **Prompt v1 → v2.** v1's two failed quotes weren't misquotes of speakers. One was a Bible verse quoted from memory, and the other was example wording the bot wrote for the user and put in quotes. v2 added three rules:
    * only quote scripture if a speaker quoted it
    * use italics, not quotes, for the bot's own wording
    * put its own application under an "Applying this" heading
  
  Both quote problems went away. The "Applying this" rule only partly worked: on the AI question the bot added the section, but still slipped lines like "This suggests AI-generated answers should be evaluated carefully" between real quotes.
- **The model's query rewriting can hurt retrieval.** v2's one miss was "Is the gospel only for certain kinds of people?" The model searched with a long keyword-heavy rewrite and missed President Oaks's "The Gospel of Jesus Christ Is for All." The user's plain question ranks that talk #1.
- **Not-covered questions were handled well.**
    * *Foreordination:* the word never appears in the talks, but the agent searched three times and found Bishop Douglas's "God held you in reserve for this time… before you were born." This is the same lesson as hw2d: embeddings find the idea even when the word isn't there.
    * *AI:* the bot opened with "the conference did not give a detailed policy" and then found Elder Andersen's line about "misinformation, and now artificial information."

## Compared to web search
I ran the same 12 questions with the same model, using OpenAI's built-in `web_search` tool instead of my database (`python eval.py --label web --web`).
- **It found the right talks too.** Three weeks after conference the talks are already indexed, and 10 of 12 answers cited the official October 2026 talk page on churchofjesuschrist.org, with clickable links, which my bot doesn't give.
- **It was narrower.** It usually read 1–2 pages per answer instead of 3 whole talks, so it gave fewer quotes (35 vs 51) and drew less on multiple speakers.
- **It didn't stay inside the conference.** On the AI question it used the *General Handbook* and a newsroom workshop by Elder Gong. That's arguably a better answer, but it isn't what the bot is supposed to do, and I can't check those quotes against my talks. Of its 4 quotes that failed the check, 2 came from non-conference pages like these and 2 were its own wording put in quotes.
- **It cost more and depends on someone else's search engine.** Token cost was almost double ($0.047 vs $0.027), plus a fee for each of its 24 searches. Web search only works for content that's public and already indexed, while local RAG works on private or brand-new documents and is limited to exactly the sources I chose.

## What I learned
- **The system prompt is how the model knows what the retrieved text is for.** Without being told "this is the only source, quote it exactly, say when it doesn't cover the question," it mixes retrieved text with what it already knows, and you can't tell which is which.
- **Return whole talks, not just the matching chunk.** A 1,200-character chunk often cut off right before the point, and full talks are cheap (about $0.002 per question). Deduplicating mattered more than chunk size.
- **Giving the model tools beat a fixed retrieve-then-answer pipeline.** It searched again when the first search missed and used `list_talks` for speaker questions, which plain semantic search can't answer.
- **You have to check quotes automatically.** Every answer looks trustworthy, and the one fake quote I found looked exactly like the real ones. A simple word-for-word check against the source was the most useful part of the project.

## Files
- `ingest.py`: loads `talks/` into ChromaDB (`chroma/`, rebuildable, not committed)
- `gc_search.py`: deduplicated whole-talk search
- `chat.py`: the chatbot and its tools
- `system_prompt.md` (v2) and `system_prompt_v1.md`
- `eval.py`, plus `results-no-rag.json`, `results-v1.json`, `results-v2.json` and `results-web.json`
- `tools.py` and `usage.py`: copied from classwork

To run: `python ../classwork/2e/download_gc_talks.py https://www.churchofjesuschrist.org/study/general-conference/2026/10 talks`, then `python ingest.py`, then `python chat.py`.
