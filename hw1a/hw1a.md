### How I completed the required tasks
In completing the required tasks, I first spent lots of time setting up my environment with the API key. I added a .env file that had to be listed in .gitignore. I then reviewed code that we went over in the classroom. I fiddled around with basic_response.py and response.py, making sure it worked with my environment. 

### Additional exploration


### Obstacles I encountered
When using the older models, such as gpt-5-nano, it frequently hallucinated. For example, it output a classification even in a run with no input text. Thus, older models are more likely to give confident-sounding answers with no substance to back them up. Another roadblock was that I didn't know how to use my API key even after creating the .env file. This is becasue I hadn't installed python-dotenv. At first, I had hardcoded reasoning to be low effort. I dropped it later on so that the program wouldn't fail using older models, like gpt-4.1 

### What I learned 
I learned a lot about what each of the import lines mean. For example, "from time import time" pulls in the time function that measures how long the API call takes. I also learned I needed to import load_dotenv() to read the .env file. I had never done that before. 

I also learned that agent behavior is determined in the prompt, not in the actual code that I write. The code stays the same but the behavior can entirely change with the prompt file. It is so cool that, basically, I can write any program I want around the powerful OpenAI model. 

### Why this matters in the context of agent engineering
This matters in the context of agent engineering because this is the most basic form of an agent. This is the primitive, foundation block that will then be used to make multi-agent systems. They can also be orchestrated together to become a machine of thousands of agents. I need to understand this before delving further. 

### How many hours I spent
I spent 4 hours on this homework.


________________

Why your class starts here: this is the atom. An agent is what you get when you wrap control flow around this primitive — call the model, look at what it said, decide whether to call a tool, feed the result back, call again, repeat until done. Every one of those steps is still just a completion. You're building the single unit before building the machine that orchestrates thousands of them.

The part worth actually sitting with, and what your assignment is nudging at with "each prompt is effectively a program of its own": your Python file never changes. Swap sentiment-instructions.md for prime-code-instructions.md and the same 38 lines become a code generator instead of a classifier. The behavior lives in the prompt, not the code.

That's a genuinely different way to build software. Normally behavior is in the logic you write; here the logic is a fixed pipe and the English text is the program. Which is also why prompt quality is the engineering discipline in this field, and why the assignment makes you write at least two and feel the difference.

