# Agent Engineering Portfolio

This repository contains completed coursework, experiments, and a final project from **CS 301R: Agent Engineering** at Brigham Young University (Fall 2026).

Across the class, I built and evaluated LLM-based systems that use retrieval, tool calling, structured outputs, and safety controls to solve practical tasks. The work in this repository emphasizes grounded AI, tool-using agents, evaluation, and safe agent behavior.

## Final project

My final project is a **semantic search system for personal gospel study**.

- Searches **41,995 scripture verses** from the standard works
- Searches **38 October 2026 general conference talks**
- Searches selected **BYU speeches**
- Compares **vector**, **keyword**, and **hybrid** retrieval
- Returns source-linked passages instead of unsupported generated answers

The project includes a labeled evaluation set to measure retrieval quality across sources and is documented here: [`final project/README.md`](final%20project/README.md)

## Selected coursework

- [`hw2d/hw2d.md`](hw2d/hw2d.md) — semantic search over the standard works
- [`hw2e/hw2e.md`](hw2e/hw2e.md) — conference retrieval with quote checking
- [`hw3b/hw3b.md`](hw3b/hw3b.md) — sandboxed agent execution and prompt injection testing
- [`hw3c/hw3c.md`](hw3c/hw3c.md) — GitHub connector experimentation and repository presentation work

## Skills demonstrated

- Prompt engineering and system prompt design
- Tool calling and structured outputs
- Semantic search, retrieval evaluation, and RAG workflows
- Prompt injection testing, sandboxing, and agent safety
- Python, Git/GitHub, CLI workflows, and Markdown documentation

## Repository structure

- [`final project/`](final%20project/) — final project code and documentation
- `hw0a/` through `hw3c/` — homework submissions and reports
- `classwork/` — smaller in-class experiments and supporting prototypes

## Course themes

This work focused on building agents that can retrieve evidence, call tools, manage context, and operate more reliably in realistic settings. The repository reflects both the implementation of those systems and the evaluation work needed to make them useful and trustworthy.
