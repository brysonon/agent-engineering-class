# HW2f Write-up

## How I completed the required tasks
- **What I am interested in doing and why:** I want to build a semantic search app for personal gospel study. It would search the standard works, every General Conference talk back to 1971, and BYU devotionals, and give a short answer that cites what it found.
    * In hw2d I saw that keyword search cannot find ideas that are worded differently. "Foreordain" is in 1 verse and "premortal" is in 0, but the passages that teach it are there. Embeddings found them, so embeddings will be my core concept.
    * In hw2e I built a chatbot over one conference with a quote checker. I want to scale that up to everything and keep the checker so the answers stay honest.
- **Alternatives I considered:**
    * A research project asking whether hybrid search (keyword + vector) beats pure vector search for doctrinal questions. I still plan to measure this, just inside the app.
    * Extending my hw2e chatbot to all conferences. I chose search plus answers instead, because for personal study I want to see the sources, not just a summary.
    * A work app, such as a bookkeeping or deal-screening agent. It would be useful, but embeddings would not be central to it.

## Additional exploration
- I estimated the size. The scriptures are 1.2M words and cost 3 cents to embed in hw2d. Conference is about 4,000 talks and BYU speeches are a few thousand more, so roughly 30M words total, which is still under $1 to embed.
- I already have `download_gc_talks.py` working from hw2e, so getting all of conference is a loop over every conference.
- I planned how I will measure it: a set of 30-50 questions where I already know the right passages, comparing keyword, vector, hybrid, and LLM re-ranked search.

## Obstacles I encountered
- **BYU speeches will be the hardest data to get.** Some talks are video only and the pages have extra text mixed in, so I will add them last.
- **Mixing sources is tricky.** A verse is 30 words and a devotional is 5,000, so they will not score the same. I will probably group results by source.
- **Keeping the focus on embeddings.** Cited answers make the app better, but I do not want it to turn into just a RAG chatbot.

## What I learned
- I learned that the hardest part of this project will be the data, not the model.
- I learned that I can justify using an LLM with my own numbers from hw2d instead of just saying semantic search is better.
- I learned that deciding the user first (personal study) answered a lot of my design questions, like showing the sources and not just the answer.

## Why this matters in the context of agent engineering
Search is the first step of almost every agent that answers from documents, and if it misses something the agent has no way of knowing. Building this across sources this different will show me how chunking, mixed sources, and hybrid search actually affect what the agent gets back. Measuring it against keyword search will tell me whether the LLM parts are worth their cost.

## How many hours I spent
I spent 3 hours on this homework.
