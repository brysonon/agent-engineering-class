# HW3b Report

## How I completed the required tasks

### Sandbox

I installed Docker in WSL and ran a small shell-tool agent ([`sandbox/agent.py`](sandbox/agent.py)) whose commands execute in a container with no network, a read-only filesystem, a non-root user, and memory/CPU/process limits. The container saw only a copy of my project code, and my API key stayed outside it. I gave the agent three tasks: review my project code, report what the sandbox allows, and summarize a file containing a hidden prompt injection.

### Project status

My semantic search works over 41,995 scripture verses, 38 October 2026 conference talks, and four BYU speeches. I also built a small retrieval evaluation set from official Church study resources. On 47 questions, vector search reached 83% hit@1 and 100% hit@10, beating the keyword baseline overall. Next I plan to improve the missed conference queries and then add more sources.

## Additional exploration

I ran the injected command myself inside the container. It failed because the container had no network, so the sandbox blocked the attack even though the model had already ignored it.
For the search project, I also added a small Church-based evaluation set and compared vector, keyword, and hybrid retrieval.

## Obstacles I encountered

My harness called `wsl -- docker exec`, which ran `$(...)` and backticks in the WSL shell before the command reached the container. That let parts of the agent's commands run outside the sandbox. Switching to `wsl --exec` fixed it.
For search, the hardest part was writing fair gold questions because some prompts could reasonably match more than one verse or talk.

## What I learned

A sandbox is only as strong as the code that sends commands into it. Testing where commands actually ran caught a problem that reading the Docker settings did not.
I also learned that vector search helps more on broader conference questions, while keyword search stays very strong on direct scripture questions.

## Why this matters in agent engineering

Agents will sometimes run harmful commands, by mistake or from injected instructions. A sandbox limits the damage, but the harness around it needs testing too.
Evaluation matters for retrieval too, because if search misses the right source, any later answer step starts with the wrong evidence.

## How many hours I spent

I spent 3 hours on HW3b.
