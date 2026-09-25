# HW1e Write-up

## How I completed the required tasks
- I fiddled around with the reasoning argument on the chatbot. I read the reasoning that it output for different Fermi problems.
- I did additional exploration in the form of watching YouTube videos.
- I had the model solve GMAT problems on different reasonings. I found out that low vs high reasoning is about a 1.5x increase in cost. and used about 50% more reasoning tokens. I didn't think that upping the reasoning was worth it for these problems because they were not incredibly difficult. In my intuition, higher reasoning is useful for a lot more complex, nuanced tasks—perhaps tasks that don't have a definitive answer (like fermi problems). 
    * Higher reasoning isn't useful for problems that don't need to be broken down or that are simpler. It wastes time because of the latency and also costs more. I also found that higher reasoning doesn't seem to help with problems that involve a lot of counting or large quantities of text because the model gets too confused. 
    * For the critical reasoning questions from the GMAT, higher reasoning performed significantly better. Low reasoning got one out of two questions wrong, while higher reasoning got both questions right. Higher reasoning was more expensive, but not by a marginal amount. 
- Overall, I developed a much better intuition for how long it would take and how much it would cost to up the reasoning for certain tasks. 
- I 

## Additional exploration
- I watched 3 YouTube videos to deepen my understanding of reasoning, how it works in models, and what thought chains are (more of what I learned is in the "What I Learned" section):
    * Anthropic: https://www.youtube.com/watch?v=Bj9BD2D3DzA
    * Google: https://www.youtube.com/watch?v=xCRvOUykOX0
    * How they actually work: https://www.youtube.com/shorts/9F-WHimhscs
- I tested the model on GMAT questions found on mba.com (https://www.mba.com/exams/gmat-exam/about/sample-questions) at different levels of reasoning. Simpler questions were easier for the model to answer with or without reasoning, while harder (more complex) questions were answered better when the model had a higher reasoning parameter.

## Obstacles I encountered
- I had trouble in the beginning trying to understand what reasoning is. I didn't understand why models would want to use it. Upon further investigation (helpful YouTube videos), I learned a lot more about what they are and why agent engineers would use reasoning. 
- Max reasoning seemed to think way too much, and the output accuracy/quality was not worth the extra cost. For example, on a simple Fermi problem, it output a worse answer (in my opinion) than the model with high reasoning and cost 50x more. I can't see cases in which max reasoning would be valuable. 
- At first, I was giving the agent easy problems. The model would produce the same answer with or without reasoning. The only thing that would change would be the time and cost. Thus, I needed to find harder problems for it to solve. 
- I tried giving the agent the "hardest riddle" I could find on the internet, but it answers it easily even with low reasoning. I think this is because it is so popular that it the answer is already embedded in its training data. 

## What I learned
- In most cases I tested, max effort seemed to be overkill. It seemed to be too much thinking. For example, for the Fermi problem of how many drinks are spilled annually on BYU campus, the model produced (in my opinion) way too much reasoning and was incredibly expensive, yet the estimate was a lot lower than other reasoning efforts. 
- I learned that, many times, reasoning can make answers more accurate because models will follow a chain of thought and use its reasoning tokens to produce an output instead of just jumping to a conclusion immediately. However, at the end of the day, models are really just next-token predictors. 
- I learned about best-of-n sampling, where a model will output n number of responses and then selects the best result (or most repeated result), which can help lead to more accurate answers. 

## Why this matters in the context of agent engineering
This is very important for agent engineering because reasoning effort can be determined at every stage of the agent's loop. For example, an agent should use low effort for trivial steps and high effort for critical steps, or steps that require critical thinking (that are high-impact). If reasoning was kept on high the entire time, then latency and cost would compound significantly with more turns that an agent runs. 

The most important thing I learned is that more thinking is not necessarily better. I used to always put ChatGPT on high reasoning, but I am learning that that is not always more accurate. Reasoning effort is not just a dial to raise whenever you want more quality. There is a fine line where you can spend just enough to get the best answer. 

## How many hours I spent
I spent 3 hours on this homework.
