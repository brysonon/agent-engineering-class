# HW1b Write-up

## How I completed the required tasks
- I made my bender-classifier program and my program that generates the first 100 digits of pi better. They are better in the sense that the models are less likely to hallucinate and are better-structured, so the output can be parsed and utilized by other programs more effectively. 
    * As an example, in 1a I told the model to classify a user into one of four benders but didn't give it an option to say that there is no type of bender inherent in the text. In 1b, the prompt specifically tells the model to not make any guesses and that it is okay to say Unknown, especially if the input does not mention any personality traits.
- I made an agent that summarizes speech. The prompt told the agent to summarize the key takeaways, important messages, and every time the speaker talks about promises of the Lord, which is something important to me. 
    * I then tried the summarizing agent with a variety of different models. 

## Additional exploration
- I made a .md file titled side-by-side-output that shows the output after running every test case twice (the 1a way with plain text and the 1b way with JSON schema) using the same input and same model. It also recorded the time and cost of each output. I thought it was interesting that while, on average, 1b outputs cost more, both 1a and 1b outputs took about the same time. 
- I tried the summarizing agent with a few different models. I tried 5.6-sol, 5.6-luna, and 4.0-nano. Interestingly, gpt 4.0-nano was the most expensive at 2 cents. It also took the least amount of time. On the first pass, 5.6-sol provided the best answer, in my opinion, and took a slightly longer time than 4.0-nano but less time than 5.6-luna. I ran it a second time, and 5.6-sol took 87 seconds and cost almost 13 cents. It blew my mind how much it cost and how long it ran for. 

## Obstacles I encountered
- At first, the phrase "I am a waterbender" did not trigger the model. It was looking only for phrases about personality traits, not for specific declarations. Thus, I added a line that said to cover explicit declarations of what bender the user is. 
- I can't claim that structured output produces better code because I have not tested it yet. 
- Costs went up, not down. Structured runs cost about 2-4x the non-structured runs because it used more tokens. Thus, it is more expensive for the model to be more reliable. 

## What I learned
- I learned that learning to structure output is very important for when bigger projects are created and larger agent teams and pipelines are created. It makes it easier when it becomes input for other agents or projects.
- I learned that having the formatting (structured output) in the prompt makes the actual coding (in the program) so much easier. At first, I tried formatting the output in the .py file itself, but I found it so much easier to format the output in the prompt.
- In the speech summarizer, I learned that it's important to be specific for the things you are looking for. For example, I wanted the model to repeat all quotes about promises. But I had to give specific instructions to find promises from the Lord, not promises from the speaker. 

## Why this matters in the context of agent engineering
This matters in the context of agent engineering because it's importnat to know where to put rules. You can put it in the program itself as Python code, as a JSON schema, or as English text in the prompt. Having the rules in the code is free, but the rest cost input tokens. There is also a possibility for drifting/hallucinating if it is placed in the prompt text. This teaches the engineer how to make good architecture decisions when creating agents. Later, when harnesses are made and multiple agents are orchestrated, these engineering decisions are crucial. 

## How many hours I spent
I spent 4 hours on this homework.
