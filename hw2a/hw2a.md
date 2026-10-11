# HW2a Write-up

## How I completed the required tasks
- I made my own AGENTS.md file.
- I vibecoded a simple BYU Speech finder app. 
    * It was very good at taking natural language and finding a talk that was relevant. It was also very smooth, well-functioning, and good-looking. It had eye-catching colors and layouts.
    * Because it didn't have very many talks uploaded (only 42), it wasn't very good at finding the best talk possible because of its small database. It also wasn't very good at matching different talks to different situations. It would frequently give the same talks each time. 
- I used the `skill-creator` skill to build a skill called `byu-speech-transcripts`. It lives in `.claude/skills/` and it bundles a Python script that fetches a talk from speeches.byu.edu and pulls out the transcript.
    * I built it around three traps I had already hit by hand in HW1g: some talks are published as video only and have no text at all, the page embeds topic metadata that creates false keyword matches, and the navigation and video-player text looks like prose if you do not filter it out.
    * The script uses only the standard library and fetches with `urllib` instead of shelling out to `curl`. In HW1g my agent burned six shell calls fighting Windows quoting on `curl` flags, so removing the shell from that step removes the whole failure mode.
- I tested the skill by running the same task twice: once with the skill and once with no skill at all, and comparing. I also ran the same task through two different instruction sets to see what the instructions alone were worth.
- I explored different ideas for a final project (more info below).

## Additional exploration
- **Does the skill make a difference?** I gave both runs the same job: count how many paragraphs in three BYU talks mention miracles.

  | | With skill | Without skill |
  | --- | --- | --- |
  | Tokens | 39,946 | 57,042 |
  | Tool calls | 9 | 21 |
  | Time | 53.8s | 237.2s |
  | Correct? | yes | yes |

    * The skill made no difference to correctness. Both runs got the same answers, and both correctly reported that the Dallas Jenkins talk has no published transcript instead of reporting it as zero.
    * It made a large difference to efficiency: 43% fewer tokens, less than half the tool calls, and 4.4x faster. The run without the skill was slow because it had to work out the page structure by trial and error, which is exactly the work the skill had already done.
- **The skill also taught the agent something false.** I had written in the skill that the word stem "miracl" catches "miraculous." It does not — that word is spelled m-i-r-a-c-u-l-o-u-s, so it contains no "miracl" at all. The correct stem is "mirac." The run using my skill trusted that claim and repeated it. The run without the skill had nothing to trust, worked the matching out from scratch, and caught the mistake. I fixed the skill afterward.
- **Do different instruction sets change the output?** I wrote two system prompts and ran the same task through my HW1g agent with each: `minimal.md` (five words, "You are a helpful agent") and `disciplined.md` (155 words telling it to verify its sources, distinguish "no data" from "zero," and prefer writing a script over matching by hand).

  | | minimal | disciplined |
  | --- | --- | --- |
  | Input tokens | 22,776 | 23,264 |
  | Output tokens | 619 | 543 |
  | Reasoning tokens | 217 | 191 |
  | Time | 12.98s | 7.84s |
  | Cost | $0.005298 | $0.005304 |
  | Correct? | yes | yes |

    * Both were right. The longer instructions cost 488 more input tokens, produced 76 fewer output tokens, ran five seconds faster, and changed the answer not at all. The cost difference was six ten-thousandths of a cent.
    * I think the reason is that both runs reached the pages through `web_search`, which hands back the readable page text, so the model actually read the sentence "The text for this speech is unavailable." My HW1g agent scraped raw HTML and counted paragraph tags, which buried that same sentence in navigation junk. Same model and same trap, opposite outcome, because of how the content got to it.
- I also explored some different ideas for a final project within the realm of the Church's databases. I want to be able to prototype something that will help me in my personal studies of the scriptures, whether that is related to BYU speeches, the overall searching and indexing tools that the Church provides, or the General Handbook. 
    * For example, I tried a BYU speeches indexer to help narrow down my searches for BYU speeches with English text, using natural language skills. 

## Obstacles I encountered
- One obstacle I faced was that it was frustrating to not know exactly what AI was doing. I just had to trust that the process it was going through while building my app was correct.  
- Another obstacle I faced was that it was extremely annoying for Codex to constantly ask me for permission before doing basic tasks. I was constantly switching back to the tab and clicking approve, which soured my experience a lot. I fixed this by giving Codex full permissions, finally relenting. 

## What I learned
- I learned that how involved a human wants to be in the vibecoding process is determined in large part by the quality of the code that they desire. AI isn't perfect and can make mistakes, but it is usually good at correcting itself. 
- I learned a lot about how intuitive it is to use Codex. OpenAI included many wonderful features and additions and commands to make it easy to navigate. 
- I learned that a skill is mostly a shortcut, not an upgrade. Mine did not make the agent smarter or more accurate — it made it faster and more consistent by handing it work that had already been figured out. That is still worth a lot, but it is a different claim than "the skill made the output better."
- I learned that a skill makes whatever you got wrong authoritative. My stem mistake would have been harmless in a one-off conversation, but putting it in a skill meant every run that used the skill inherited it and repeated it confidently. The run that had no skill was slower precisely because it was re-deriving everything, and that is why it was the one that caught my error. Being handed an answer and being made to work it out are different, and they fail in different directions.
- I learned that the instructions matter less than how the information reaches the model. I expected my careful 155-word prompt to beat a five-word one and it did not. What actually decided the outcome was whether the tool handed back readable text or raw HTML.

## Why this matters in the context of agent engineering
This matters in the context of agent engineering because agents are very good at coding. However, you still have to know the direction you want to go and how much you care about the durability and quality of your code. If you care a lot about these things, then you will most likely want to be a lot more involved in the coding process. If you do not care as much and simply want a working product, then you can let AI do most or all of the coding. It is a delicate refining process.

Building skills matters a lot in the context of agent engineering because they simplify workflows. Well-developed skills can save time and money and make it easier for the user to repeat consistent output. It's important for the user to know when to make a skill versus when to not. 

## How many hours I spent
