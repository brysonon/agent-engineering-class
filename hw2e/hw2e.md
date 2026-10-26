# HW2e Write-up

## How I completed the required tasks
- I downloaded the October 2026 General Conference with `download_gc_talks.py`. That gave me 38 talks, about 43k words.
- I ingested them into a local ChromaDB (`ingest.py`) using `ingest_folder` from `chroma_demo.py`. That made 257 chunks with `text-embedding-3-small`, for less than a cent.
- I built a chatbot (`chat.py`) that uses RAG as a tool instead of a fixed retrieve-then-answer step. The model gets three tools:
    * `search_talks` returns the top 3 whole talks for a query.
    * `list_talks` and `read_talk` let it open a talk by speaker, since searching for a name does not work with embeddings.
- I wrote the system prompt (`system_prompt.md`) to tell the model how to use the extra content. It should always search first, try new wording if a search misses, only quote exact words, cite the speaker and talk, and say so when the conference did not cover something.
- I changed `query_whole_documents` (in `gc_search.py`) because it returns one row per chunk, so the same talk came back several times. For "Why do we need prophets today?", 3 of the 5 results were the same talk. Mine keeps only the best chunk from each talk.

## Additional exploration
- I built an eval (`eval.py`) with 12 questions. Ten have a talk I expected it to find, and two (AI and foreordination) the conference never directly addresses. For each answer it checks whether the right talk was found and whether every quote appears word for word in the talks and is credited to the right speaker.
- I ran the same questions with no RAG, with my two prompt versions, and with OpenAI's web search instead of my database.

  | | Found expected talk | Real quotes | Cost (12 questions) |
  | --- | --- | --- | --- |
  | No RAG | - | 5/30 | $0.007 |
  | RAG, prompt v1 | 10/10 | 58/60 | $0.025 |
  | RAG, prompt v2 | 9/10 | 51/51 | $0.027 |
  | Web search | 10/12 cited the real talk page | 31/35 | $0.047 + search fees |

    * Without RAG the model refused when I named a speaker, but on topic questions it made up quotes.
    * v1's two bad quotes were a Bible verse from memory and the bot's own example wording in quotes. I added rules for both in v2 and they went away.
    * Web search found the right talks too, and it gave links. But it usually read only 1-2 pages, so it gave fewer quotes. It also went outside the conference: on the AI question it used the Handbook and a newsroom article. It cost almost double plus a fee per search.
- Foreordination never appears in the talks, but the agent searched three times and found Bishop Douglas's "God held you in reserve for this time… before you were born."

## Obstacles I encountered
- **Chroma crashed in parallel:** Running the eval questions in threads crashed when they all tried to open the database at once. I had to add a lock so only one opens it.
- **A fake quote that looked real:** In an early test the bot quoted D&C 107:23 from memory and said it was Elder Caussé. Nothing about it looked different from the real quotes, which is why I built the quote checker.
- **The checker was not perfect:** It flagged talk titles in single quotes and quotes where the speaker's name was too far away. I had to read the flagged answers myself to tell real errors from false alarms.
- **The model's search wording hurt it:** In v2 it rewrote "Is the gospel only for certain kinds of people?" into a long keyword-heavy query and missed President Oaks's "The Gospel of Jesus Christ Is for All." My plain question ranks that talk first.

## What I learned
- I learned that the system prompt is how the model knows what the retrieved text is for. Without being told it is the only source and to quote it exactly, the model mixes it with what it already knows, and you cannot tell which is which.
- I learned that RAG fixed made-up quotes but not wrong credit. The words were real, but I still had to check who said them.
- I learned that returning whole talks worked better than chunks, and removing duplicates mattered more than chunk size.
- I learned that giving the model search as a tool beat a fixed pipeline. It searched again when it missed and used `list_talks` for speaker questions.
- I learned that the model is not always better at writing search queries than the user. Its rewrites made one search worse.
- I learned that web search is close for public content, but local RAG keeps the bot limited to exactly the sources I chose.

## Why this matters in the context of agent engineering
Most agents that answer from documents work this way. They search, then answer from whatever came back. RAG as a tool lets the agent decide when and how to search, and that is why it could recover from a missed search or look up a speaker. But the agent also controls the query, and one of its rewrites made the search worse. Retrieval is only as good as the query the agent writes, and nothing tells you when a search missed.

The bigger thing is that a grounded answer still has to be checked. Every answer looked trustworthy, including the one with a fake quote. A simple word-for-word check against the sources caught what reading the answers did not. Any agent that cites sources needs something like that, because looking right and being right look the same.

## How many hours I spent
I spent 3 hours on this homework.
