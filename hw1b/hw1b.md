# HW1b Write-up

## How I completed the required tasks
- I made my bender-classifier program and my program that generates the first 100 digits of pi better. They are better in the sense that the models are less likely to hallucinate and are better-structured, so the output can be parsed and utilized by other programs more effectively. 
    * As an example, in 1a I told the model to classify a user into one of four benders but didn't give it an option to say that there is no type of bender inherent in the text. In 1b, the prompt specifically tells the model to not make any guesses and that it is okay to say Unknown, especially if the input does not mention any personality traits.
- 
- 

## Additional exploration
- I made a .md file titled side-by-side-output that shows the output after running every test case twice (the 1a way with plain text and the 1b way with JSON schema) using the same input and same model. It also recorded the time and cost of each output. I thought it was interesting that while, on average, 1b outputs cost more, both 1a and 1b outputs took about the same time. 
    * 
- 

## Obstacles I encountered
- At first, the phrase "I am a waterbender" did not trigger the model. It was looking only for phrases about personality traits, not for specific declarations. Thus, I added a line that said to cover explicit declarations of what bender the user is. 
- I can't claim that structured output produces better code because I have not tested it yet. 
- Costs went up, not down. Structured runs cost about 2-4x the non-structured runs because it used more tokens. Thus, it is more expensive for the model to be more reliable. 

## What I learned
- Interestingly,
- 
- 

## Why this matters in the context of agent engineering


## How many hours I spent
I spent  hours on this homework.
