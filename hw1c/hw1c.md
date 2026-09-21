# HW1c Write-up

## How I completed the required tasks
- I made a game similar to cat-dog-bird called believe_game. This game required the agent to, on a hidden agenda, get the user to say the two words "I believe," in that order. 
    * I modified the prompt because, at first, the agent was looking for just those two words and nothing after, but I wanted it to look for anything that started with those two words.
- I also read the news release. 

## Additional exploration
- I played around with the emoji prompt, which tells the model to respond in only emojis. Interestingly, 5.6-sol was the only model that had thought-out, easy-to-follow questions. For example, it said 🤔👉❤️🍕🍔🍣❓ to ask me what food I like or 🌍✈️👉💭📍❓ to ask which places I'm thinking of travelling to. The cheaper models, like 4.1 or 4.1-nano, only asked two or three word questions like ❓🤔 5.6-sol can handle a lot more complexity and translation requirements. 
- I made a disciple_prompt that responds and acts like an LDS church leader, using scriptures and quotations. It was too strong at first, so I made a disciple_prompt_subtle that was more subtle when responding in the chat. It would only include a quote or text here and there. 

## Obstacles I encountered
- A minor obstacle I encountered was that I couldn't get my API key to work. I realized I had forgotten to do include the load_dotenv() line. 
- An obstacle I encountered with disciple_prompt.md was that the model was outputting too much. It would always output a scripture, a talk, and give advice. It felt too long, so I found ways to shorten it by telling the model to "keep it simple."
- For my believe_game.md, the agent didn't respond with the phrase it was supposed to after it won, even after I said "I believe..." I think it was because it was looking for just that phrase by itself. I wanted it to win as long as the user started the sentence with I believe. 

## What I learned
- I learned that, as a conversation gets longer, chats become more expensive. This is beecause chats keep the history and resend the entire history every turn. I learned that this can be mitigated by truncating the history or caching it (summarizing the repeated parts). 
- I learned that, when given a prompt, the model tends to default to a larger response so that it can fulfill all the requests. I had to put constraints in the prompt so that the model was more subtle. The model always seems to over-please and over-deliver. 
- I also learned that it does make a large difference what model you choose, especially when tasks involve translations or multiple parts. For example, the emoji_prompt performed significantly better with 5.6-sol than it did with 4.1. 
- In reading the news release on Anthropic's constitution, I learned about how Anthropic is trying to paint Claude in a human-like light. They are trying to get people to believe Claude has feelings and mental well-being to generate more usage and make it feel more real. 

## Why this matters in the context of agent engineering
This is important in the context of agent engineering because it further promotes the idea that English-text prompts are the program while the actual code remains the same. For example, all of my different prompt.md files made the same chat.py behave differently. It is also important to remember that, in order to have a chat, history needs to be saved. Or else, "conversations" as we perceive them could not be had. However, it's important to learn where to truncate or cache the history so that costs do not skyrocket. 

## How many hours I spent
I spent 4 hours on this homework.
