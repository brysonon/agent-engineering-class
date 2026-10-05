# HW1g Write-up

## How I completed the required tasks
- I built my agent from the 1g classwork files. The agent is `chat_tools.py` and its four main tools come from `agent_toolbox.py`: `shell`, `read`, `write`, and `edit`. `tools.py` generates each tool's JSON schema from the Python type hints, so I never hand-wrote a schema.
- I extended it with OpenAI's built-in `web_search` tool. The merge was one line: `tools=toolbox.tools + [{'type': 'web_search'}]`.
    * What surprised me is that I didn't have to touch the dispatch loop at all. `web_search` is hosted, so OpenAI runs it and hands back a finished `web_search_call` item. My loop only executes items where `output.type == 'function_call'`, so the hosted tool slides right past it. My four local tools are the only ones I actually have to run myself.
- I also had to add `load_dotenv` to `chat_tools.py`. The classwork version never loads `.env`, so my first run died on auth before the agent started.
- My first test used both kinds of tools at once: look up which Python version added `tomllib`, then write a script that parses a TOML file and prints each key's type, write a sample file, and run it. It answered Python 3.11 citing PEP 680, wrote both files, and ran them in **13.66 seconds for $0.0029**. I re-ran its script myself and the output it claimed was exactly what the script really printed.

## Additional exploration
- I gave it a real project instead of a toy: download five BYU speeches, pull every paragraph mentioning "promis" or "miracl", and build a PDF of the quotes grouped by speaker with source URLs.
- It did the whole thing in **57.2 seconds for $0.0051**. It downloaded all five, wrote its own `extract_quotes.py`, installed `beautifulsoup4` and `reportlab` without being told to, and produced a valid 5-page PDF.
    * The part I liked is that it wrote a script to do the filtering instead of reading all five transcripts into its own context. That was about 15,000 words it never had to pay for twice.
- Quotes found: Wilcox 4, Holland 7, Oaks 1, Kearon 2, Jenkins 0.
- **The zero is the interesting part.** I went and checked, and the Dallas Jenkins page says "The text for this speech is unavailable" — BYU only published the video. So the 0 was technically correct, but the agent reported it as a bare number and never asked why one of its five inputs came back empty. I ended up with a PDF page that has a heading and nothing under it. A person would have flagged that in a second.

## Obstacles I encountered
- **My first run crashed because of the tool I had just added.** The agent finished all its work and then died on `UnicodeEncodeError: 'charmap' codec can't encode character ''`. That character is a private-use citation marker that `web_search` embeds in its response text, and my Windows console uses cp1252 and can't encode it. `PYTHONIOENCODING=utf-8` fixed it. This cost me real time because the traceback points at `print`, so it looks like a printing bug instead of something the search tool introduced.
- **The agent fought my shell.** On the speeches task it took six `shell` calls just to download five files. It started with Git Bash syntax, failed, switched to `curl.exe`, then to `cmd /c`, and at one point ran `rmdir /s /q speeches\brad-wilcox.html` because it had decided the HTML files were folders. It recovered on its own, but a third of its tool calls went to fighting Windows. The reason is that `shell` passes one string to `subprocess.run(shell=True)`, which on my machine is `cmd.exe`, and the model kept reaching for Linux commands.
- The missing `load_dotenv` above.
- `agent_toolbox.py` runs `shell` and `write` with no confirmation step. The model can run any command and overwrite any file immediately. It worked out, but I scoped both tasks to empty folders on purpose because I was aware I'd handed a model unsupervised shell access to my own machine.

## What I learned
- There are two different kinds of tools and the difference shows up in the code. My four tools are functions I have to execute and return results for. `web_search` is hosted, so OpenAI executes it. Adding it was one line because the hard part was never mine.
- Caching is what makes the loop affordable. The tomllib task cached 76% of its input tokens; the speeches task cached **91% (54,964 of 60,364)**. The loop re-sends the whole history every pass, so the longer the task runs the more it leans on cache.
- I ran both tasks at `--reasoning none` and both finished. In my 1e write-up I guessed that higher reasoning would matter most for complex multi-step work, and that was only half right. The steps themselves were easy enough without it — but the shell thrashing is exactly the kind of mistake more reasoning might have avoided. "Multi-step" and "hard" are not the same thing.
- **Verifying the agent is cheap and it is not optional.** Re-running its script took seconds and is the only reason I can say it didn't fabricate anything. Finding out *why* Jenkins returned 0 took one look at the page. The agent reported a true number that gave a false impression, and it would have gone straight into my PDF if I hadn't checked.

## Why this matters in the context of agent engineering
The loop itself is tiny. `chat_tools.py` is under 80 lines and the part that makes it an agent — call the model, run the tools it asks for, feed results back, repeat — is maybe fifteen of them. Everything that decides whether the agent is any good lives outside that loop: which tools you expose, how well you describe them, and what you let it do without asking.

Giving a model `shell` with no approval gate is the biggest decision in the whole file, and it gets made implicitly by just not writing a confirmation step. Every tool is a capability surface and a risk surface at the same time.

The other lesson is that an agent reporting success is not the same as success. Mine finished both tasks, reported accurate numbers, and still handed me a PDF with a blank page in it. Agents fail quietly and plausibly, which means the verification step has to be mine.

## How many hours I spent
I spent 3 hours on this homework.
