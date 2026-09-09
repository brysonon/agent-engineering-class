### Notes from the video
- All LLMs do is predict the next token
- Because it is technically deterministic, and in order to not get the same output every time, occasionally some lower-probability tokens are selected
- Backpropogation tweaks the model's parameters (there can be billions)
- Steps in preparing an AI chatbot
    1. Pretraining on lots of text
    2. Reinforcement learning with human feedback
        * Workers flag model's errors
- Transformers read all text in parallel, at once, by converting every token to a multi-number vector
    - Words with similar meanings lie in the same high-dimensional space


### Notes from the reading
- The biggest source of text data we have is the internet
- Companies dedicate themselves to collecting and cleaning the data
- "Pure pattern recognition," no thinking or reasoning
- "all the internet’s knowledge is distilled within mathematical parameters"

### Overall, what did I learn?
The most important lesson I took away from this video and reading is that, at their core, LLMs are simply predicting the next most likely token based on gargantuan amounts of training data. I can better understand why models sometimes hallucinate. The more I learn about LLMs, the more I realize that the amount of data they process is incomprehensible. But it is so cool! 

Although I am new to the Machine Learning major, I really liked seeing how all of my classes are fitting together. In CS 270, for example, I learned about backpropogation, which is how LLMs tune their parameters. In MATH 213, I learned about vectors, which is what transformers use to define words. I like how everything is coming together. 

I am curious to see what is to come for the future. How will we evolve into Artificial General Intelligence?