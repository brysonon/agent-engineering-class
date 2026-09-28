# HW1f Write-up

## How I completed the required tasks
- I added capabilities for the chatbot.py to be able to call tools. I added a toolbox of statistics tools including 
    * I tested the model both with and without access to tools. I found that, using tools, costs went up as expected (by about twice as much). Also, using tools, the model was accurate 100% of the time when asked to complete tasks that the tools were made for. For example, using tools to generate the probability of heads 5037/10000 times generated 0.607% at $0.000470. Not using tools, the model generated different answers each time (0.735% and 0.757%) and cost $0.000266. It was definitely an improvement to be able to use tool calls, albeit a little bit more expensive. 

## Additional exploration
- I watched this basic video (https://www.youtube.com/shorts/V94BUC1kop8) on how tool calling works. What I learned is down below.
- I spent a lot of time conversing with Claude about how tool calls work and what really happens behind the scenes. Claude taught me about the nature of tool calls and gave me a step-by-step summary of what is sent and what it looks like. More about what I learned down below.

## Obstacles I encountered
- I had trouble understanding the relationship between the model, my machine, and the code I provided. I did not know how everything worked underneath the hood. So I spent time researching and understand it much better now. 
- A request for a random integer to be generated failed because the result I was sending back (after the tool call) had an extra argument field that was rejected by the API. The extra argument was caused by responses.stream, which is different from responses.create. I fixed it by removing the extra field. 


## What I learned
- From the video I watched, I learned that tool calling involves many steps. What I like most is that the model itself decides what tool to call and will send that tool call to the user's machine. This way, the user does not have to specify what tools the model should use. I also learned that the "toolbox" is sent in the system prompt at the beginning of the chat history. 
- I learned that, when chatbot.py is run, python builds schemas the tool name lookup. The model then decides to call a tool and chooses arguments. Then python will look up function by name and do the actual calculation. Then the model will return that result with an answer. 
- I learned that a single input prompt that uses a tool costs two API calls because it costs to both request the tool and give an answer. Thus, using tools can be expensive, especially if the returned input is large. 
- Using tool calls for more accurate and deterministic answers must be balanced with higher costs (2x the input API calls). 

## Why this matters in the context of agent engineering


## How many hours I spent
I spent  hours on this homework.
