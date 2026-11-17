# HW3d Report

## How I completed the required tasks

### Final project planning

I used the agent to narrow my final project into a retrieval-focused scripture study assistant instead of a generic chatbot. The app will let me paste a verse, ask a topic question, or describe what I am studying, then search a prebuilt library of the standard works, General Conference talks, and BYU devotionals.

### Product decisions

Version 1 will use hybrid retrieval with semantic search plus keyword search. Results will be separated into Scriptures, Conference, and BYU sections, with source checkboxes, clickable links, references, quote chunks, and a tiny note for why each result matches. Scripture results will be single verses, while talk and devotional results will be paragraph-sized chunks. The chat should also remember context across follow-up questions.

### Implementation direction

The main conclusion was that the next step is building the library and search index before polishing the interface. The simplest recommended stack is a small hostable web app using Streamlit, Postgres with pgvector or Supabase for storage and search, and an embedding API for semantic retrieval.

## Additional exploration

I also compared a simpler stack against a more polished full web stack and decided that search quality matters more than a fancy frontend for this project.

## Obstacles I encountered

The biggest challenge was narrowing the idea from a broad "chat with it" concept into a concrete first version with clear sources, chunk sizes, filters, and retrieval behavior.

## What I learned

I learned that interface ideas get much clearer once the retrieval pipeline is defined. For this project, corpus design, chunking, ranking, and evaluation matter more than advanced UI features.

## Why this matters in the context of agent engineering

This planning matters because useful study agents depend on structured source data, good retrieval, and clear constraints. A chat interface only helps if the agent can reliably find the right evidence first.

## How many hours I spent

I spent 3 hours on HW3d.
