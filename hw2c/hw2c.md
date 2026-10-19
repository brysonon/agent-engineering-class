# HW2c Write-up

## How I completed the required tasks
- I read the resource links provided in the lecture online.
- I built a judge app (`judge.py`) that grades written answers to questions from this class. For each required point it has to say whether the answer covered it and quote the words that prove it, then list any false claims and give a score from 1 to 5.
- To know whether the judge was any good, I made a test set of 6 questions with 3 answers each (`questions.py`), and I set the quality of each answer myself beforehand.
    * `strong` answers are my real answers from the 1h, 2a, and 2b quizzes. Most got full marks.
    * `middling` answers I wrote to be vague but not wrong.
    * `weak` answers I wrote to sound confident but be wrong.
    * Since I already knew the right ranking, I could measure the judge instead of guessing whether it felt right.
- I wrote two versions of the judge prompt and ran all 18 answers through both.
    * **v1** only sees the question and the answer, and is told to score it 1 to 5.
    * **v2** also sees the required points, and has to quote evidence for each one and build the score up from what it found instead of starting high.
- I built a second app (`classify.py`) using Jev. It grades the same 18 answers, but picks one label out of `full_credit`, `partial_credit`, or `no_credit` and says how confident it is.
    * I used the same answers on purpose so I could compare a classifier to a generative model on identical inputs.
    * My three quality levels map straight onto the three labels, so accuracy is just a count.

## Additional exploration
- Results for both judge versions:

  | | v1 | v2 |
  | --- | --- | --- |
  | Ranked strong > middling > weak | 2/6 | **5/6** |
  | Wrong answers scoring 3 or higher | 2/6 | **0/6** |
  | Mean score, strong | 4.83 | 4.83 |
  | Mean score, middling | 3.83 | 2.00 |
  | Mean score, weak | 2.17 | 1.00 |

- **My impressions of the LLM's abilities.** Both versions could tell a good answer from a bad one. What v1 could not do was handle the middle. It only got the full ranking right 2 out of 6 times.
    * On `progressive-disclosure` it gave my wrong answer a 4, tying it with the vague but correct one.
    * On `agent-legibility` it scored the wrong answer **higher** than the vague but correct one, 4 against 2.
- **The most interesting thing I found.** On that second one, v1 did not miss the mistake. Its own output lists the false claim and says the answer "overstates" the concept, and then it gave it a 4 anyway. It found the problem and graded as if it had not. I only caught this because I made the judge write its false claims in a separate field from its score. If it had just returned a number, I would have seen a 4 and figured it disagreed with me.
- **Prompt and workflow changes that improved performance.**
    * Giving the judge the required points instead of letting it invent its own standard. Without them it grades against a vague sense of what sounds good, which is what a confident wrong answer takes advantage of.
    * Making it quote evidence for every point. No quote, no credit. This removed the room to reward an answer that just gestures in the right direction.
    * Telling it to build the score up from what it found instead of starting high and deducting. This dropped the weak average from 2.17 to 1.00.
    * Telling it that a long answer is not a complete one and that sounding confident is not being right, since that is how I wrote my weak answers.
- v2 did not just become a harsher grader. The strong average stayed at 4.83, so only the middling and weak scores moved. That was what I wanted, because a judge that lowers every score equally has not gotten better at anything.
- **The Jev results.** It got all 18 right, which surprised me.

  | | judge v1 | judge v2 | Jev |
  | --- | --- | --- | --- |
  | Questions ranked correctly | 2/6 | 5/6 | **6/6** |
  | Answers labeled correctly | — | — | **18/18** |
  | Median time per call | 3.26s | 2.80s | **0.11s** |

    * It got `agent-legibility` right, the one case **both** judge versions failed. The judge gave my vague answer and my wrong answer the same score. Jev labeled one `partial_credit` and the other `no_credit`.
    * It was about 25 times faster.
- **Why a classifier is an appropriate choice here compared to a generative model.** All I needed was one label out of three. Everything the judge produced beyond that was work I did not ask for and then had to check.
    * The answer can only be one of my three labels. The judge could return a 3.5, or a score that did not match its own justification, and I had to write a JSON schema just to keep it in range.
    * I get a confidence number for free. A model writing "I am fairly confident" is just more text, but a real number means I could send anything below a cutoff to a person instead of trusting it.
    * It is much faster, which would matter for grading a whole class instead of 18 answers.
    * The tradeoff is that it tells me nothing about why. When the judge inflated a score I could read its reasoning and see it contradict itself. Jev gives a label and a number. For grading at scale that is fine, but the judge's explanation is what made the problem visible in the first place.
- **How accurate I think the outputs are.** I think 18/18 makes it look better than it is.
    * I wrote the answers myself, so my three levels are more clearly separated than real student answers would be. A real class would have a lot of answers sitting right between partial and full credit, and that is where I would expect it to start missing.
    * 18 answers from one course written by one person is not enough to put a real number on accuracy.
    * I cannot tell yet whether the confidence number is useful. It is supposed to flag cases worth a second look, but nothing was wrong, so there is nothing to compare it against. The lowest it got was 0.65 and that answer was still right.
    * I should also be upfront that the judge prompt got two rounds of tuning and the Jev criteria only got written once, so the comparison is not completely fair to the judge.

## Obstacles I encountered
- **No way to check the judge:** Grading my own answers tells me nothing, because I have no separate standard to compare the grade against. I had to write answers at quality levels I picked ahead of time before I could measure anything.
- **Writing the middling answers:** Deciding where `middling` stopped and `weak` started was harder than I expected. It took me a few tries to write an answer that was genuinely vague without being incorrect.
- **v2 still fails one case:** On `agent-legibility` it gave both the middling and weak answers a 1, so they tie instead of ranking correctly. Better than v1 flipping them, but it still cannot tell an answer that is too vague from an answer that is about the wrong thing.

## What I learned
- I learned that a judge grades against whatever standard you give it, and if you do not give it one, it invents one that rewards writing that sounds good.
- I learned that making the judge write out its reasoning separately from its score is the only reason I caught it finding an error and scoring the answer well anyway.
- I learned that you cannot evaluate a judge without knowing the right answers, but you can make your own. Writing three answers at levels I chose took about thirty minutes and made every later claim something I could check.
- I learned that telling a good answer from a bad one is the easy part of grading. The hard part is knowing where to draw the line on answers that are more nuanced. 
- I learned that I had been reaching for a generative model out of habit. My task was picking one label out of three, and the classifier did that better and 25 times faster (and cheaper).
- I learned that the explanation is still worth something even when it is not what I wanted. If I built this for real I would probably grade with the classifier and keep the judge around for figuring out why it got something wrong.

## Why this matters in the context of agent engineering
Knowing when to reach for a classifier matters most while I am designing the loop, not while I am debugging it. Agents mostly make decisions, and generative models are built to produce things. An agent is constantly asking whether a tool call is safe, whether the task is done, whether a retrieved passage is relevant. None of those need prose, they need one label, and sending them through a generative model means writing text and then parsing it back into a decision. Picking the wrong one is not a mistake I would notice right away either, because the generative model gives a reasonable answer. I only found out by running both on the same 18 inputs and seeing the classifier win on speed and on the one case the judge kept failing.

It matters just as much to know when not to use one. The only reason I found my judge inflating scores was that it wrote out its reasoning and I could see it contradict itself. Jev would have handed me a clean label and I never would have known. So the pattern I would actually build is both: classify in the places the agent runs constantly, where speed and a fixed set of answers matter, and keep a generative model for the times something looks wrong and I need to know why.

## How many hours I spent
I spent 3.5 hours on this homework.