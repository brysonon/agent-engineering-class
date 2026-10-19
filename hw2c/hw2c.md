# HW2c Write-up

## How I completed the required tasks
- I read the resource links provided in the lecture online.
- I built an LLM-as-judge app (`judge.py`) that grades written answers to conceptual questions from this class. It uses structured outputs so the judge has to return a coverage check for each required point, a quote from the answer backing up that check, a list of any false claims, a score from 1 to 5, and a justification.
- I needed some way to know whether the judge was actually any good, so I made an eval set of 6 questions with 3 answers each (`questions.py`). I set the quality of each answer myself before running anything.
    * The `strong` answers are my real answers from the 1h, 2a, and 2b quizzes. Most of them got full marks.
    * I wrote the `middling` answers to be vague but not wrong.
    * I wrote the `weak` answers to sound confident but actually be wrong.
    * Since I already knew the right ranking, I could measure the judge instead of just guessing whether it felt right.
- I wrote two versions of the judge prompt and ran all 18 answers through both.
    * **v1** only sees the question and the answer and is told to score it 1 to 5.
    * **v2** also sees the required points, and has to quote evidence for each one, list false claims, and build the score up from what it actually found instead of starting high.
- For the classifier, I built `classify.py` using Jev. It grades the exact same 18 answers, but instead of writing a score and a justification it picks one label out of `full_credit`, `partial_credit`, or `no_credit` and returns how confident it is.
    * I did it this way on purpose so I could compare a classifier against a generative model on identical inputs instead of just arguing about which one should be better.
    * My three quality tiers map straight onto the three labels, so accuracy is just a count.

## Additional exploration
- Here are the results for both versions, 18 graded answers each:

  | | v1 (naive) | v2 (rubric) |
  | --- | --- | --- |
  | Ranked strong > middling > weak | 2/6 | **5/6** |
  | Ranked strong > weak | 6/6 | 6/6 |
  | Wrong answers scoring 3 or higher | 2/6 | **0/6** |
  | Mean score, strong | 4.83 | 4.83 |
  | Mean score, middling | 3.83 | 2.00 |
  | Mean score, weak | 2.17 | 1.00 |
  | Cost | $0.0059 | $0.0061 |

- **My impressions of the LLM's abilities.** Both versions could tell a good answer from a bad one, since strong beat weak 6 out of 6 either way. What the naive version could not do was handle anything in the middle. It only got the full ranking right 2 out of 6 times.
    * On `progressive-disclosure` it gave my intentionally wrong answer a 4, which tied it with the vague but correct one. That wrong answer describes progressive disclosure as a user interface principle, which has nothing to do with what we learned.
    * On `agent-legibility` it actually scored the wrong answer **higher** than the vague but correct one, 4 against 2.
- **The most interesting thing I found.** On that second one, v1 did not miss the mistake. Its own output lists the false claim and says the answer "overstates" the concept. Then it gave it a 4 out of 5 anyway. It found the problem and then graded as if it had not. I only caught this because structured outputs made the judge write its false claims in a separate field from its score. If it had just returned a number I would have seen a 4 and figured it disagreed with me.
- **Prompt and workflow changes that improved performance.**
    * Giving the judge the required points instead of making it come up with its own standard. Without them it grades against some vague idea of what a good answer sounds like, which is exactly what a confident wrong answer takes advantage of.
    * Making it quote evidence for every point. If it cannot find a quote, the point does not count. This got rid of the room to give partial credit for an answer that just gestures in the right direction.
    * Telling it to build the score up from what it found instead of starting high and deducting. This was the change that dropped the weak average from 2.17 to 1.00.
    * Telling it directly that a long answer is not the same as a complete one and that sounding confident is not the same as being right. I added these because that is exactly how I wrote my weak answers.
- Interestingly, v2 did not just become a harsher grader. The strong average is 4.83 in both versions, so only the middling and weak scores moved. That was the result I wanted, because a judge that lowers every score equally has not actually gotten better at anything.
- **The Jev classifier results.** It got all 18 answers right, which honestly surprised me.

  | | judge v1 | judge v2 | Jev classifier |
  | --- | --- | --- | --- |
  | Questions ranked correctly | 2/6 | 5/6 | **6/6** |
  | Individual answers labeled correctly | — | — | **18/18** |
  | Median time per call | 3.26s | 2.80s | **0.11s** |
  | Cost for all 18 | $0.0059 | $0.0061 | not reported by the API |

    * It got `agent-legibility` right, which is the one case **both** judge versions failed on. The judge could not tell my vague answer apart from my wrong answer and gave them the same score. Jev labeled one `partial_credit` and the other `no_credit`.
    * It was about 25 times faster than the judge.
- **Why a classifier is the right fit here compared to a generative model.** The thing I actually needed was one label out of three. Everything the generative judge produced beyond that label was work I did not ask for and then had to validate.
    * The output can only be one of my three labels. The judge could hand back a 3.5 or a score that did not match its own written justification, and I had to build a JSON schema to constrain it at all. Jev cannot return something outside the set.
    * I get a confidence number for free. The generative judge has no equivalent, because a model writing "I am fairly confident" is just more text. With a real probability I could set a threshold and send anything under it to a human instead of trusting the label.
    * It is far faster, which matters if I ever wanted to grade a whole class instead of 18 answers.
    * The tradeoff is that it tells me nothing about *why*. When the judge inflated a score, I could read its justification and see that it had found the false claim and ignored it. Jev gives me a label and a number and no explanation. For grading at scale that is fine. For debugging my own rubric, the judge's explanation was what made the problem visible.
- **How accurate I think the outputs are.** I think 18/18 overstates how good it really is, and I would not claim it is perfect from this.
    * I wrote the answers myself, so I made the three tiers more clearly separated than real student answers would be. A real class would have a lot of answers sitting right on the line between partial and full credit, and that is exactly where I would expect it to start missing.
    * My sample is 18 answers across 6 questions, all from one course, all written by one person. That is not enough to put a real number on accuracy.
    * I cannot tell whether the confidence score is useful yet. The idea is that low confidence flags cases worth a human look, but since nothing was wrong, there is nothing to compare the confidence against. The lowest it ever got was 0.65 and that answer was still labeled correctly.
    * One thing I should be upfront about: the judge prompt went through two rounds of tuning and the Jev criteria only got written once. The comparison is not completely fair to the judge.

## Obstacles I encountered
- **No way to check the judge:** My real obstacle was that grading my own answers tells me nothing, because I have no separate standard to compare the grade against. I had to make my own ground truth by writing answers at quality levels I picked ahead of time before I could measure anything.
- **Writing the middling answers:** Deciding where `middling` stopped and `weak` started was harder than I expected. A vague answer and a wrong answer should not get the same score, but it took me a few tries to write an answer that was genuinely vague without being incorrect.
- **v2 still fails one case:** On `agent-legibility` it gave both the middling and weak answers a 1, so they tie instead of ranking correctly. That is better than v1 flipping them, but it means the judge still cannot tell the difference between an answer that is too vague to earn the point and an answer that is about the wrong thing entirely.

## What I learned
- I learned that an LLM judge grades against whatever standard you hand it, and if you do not hand it one, it makes one up that rewards writing that sounds good. A confident wrong answer beats a correct but hesitant one.
- I learned that structured outputs are what made the failure visible in the first place. Forcing the judge to write out its false claims separately from its score is the only reason I could see it find an error and still score the answer well.
- I learned that you cannot evaluate a judge without ground truth, but you can make your own. Writing three answers at quality levels I chose took me about thirty minutes, and after that every claim I made about the judge was something I could actually check.
- I learned that telling a good answer from a bad one is the easy half of grading. The hard half is the middle, which is where almost every real answer falls, and that is exactly where the naive prompt was unreliable.
- I learned that I had been reaching for a generative model out of habit. My whole task was picking one label out of three, and the generative judge spent most of its effort producing prose I did not need and then had to check. The classifier did the actual job better and 25 times faster.
- I learned that the explanation is worth something even when it is not the output I wanted. The only reason I found the judge inflating scores was that it wrote out its reasoning and I could see it contradict itself. Jev would have just handed me a label. If I were building this for real I would probably use the classifier to grade and keep the judge around for figuring out why it got something wrong.

## Why this matters in the context of agent engineering
LLM-as-judge is how agent systems grade themselves when there is too much output for a human to read. That means a judge that quietly inflates scores breaks every evaluation built on top of it. A harness that reports a 90% pass rate is worse than having no harness at all if the judge is lenient, because now you have false confidence instead of no information.

What fixed it here was not a better or more expensive model. It was giving the judge an explicit standard, making it show evidence, and taking away the room to be generous. That is prompt and workflow design.

This is the same thing I ran into in HW1h, where my agent asked permission in the chat instead of hitting the approval gate I had written. A model behaving well is not the same as a system that actually enforces something. Making the judge quote evidence for every rubric point is a real control. Telling the judge to be strict is only a request.

## How many hours I spent
