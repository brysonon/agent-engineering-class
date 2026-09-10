# HW1a Write-up

## How I completed the required tasks
- Spent a lot of time setting up my environment with the API key.
- Added a `.env` file, which had to be listed in `.gitignore`.
- Reviewed the code we went over in class.
- Fiddled around with `basic_response.py` and `response.py` to make sure everything worked with my environment.

## Additional exploration


## Obstacles I encountered
- **Hallucination with older models:** When using older models like `gpt-5-nano`, the model frequently hallucinated — for example, it output a classification even on a run with no input text. This showed me that older models are more likely to give confident-sounding answers with no substance behind them.
- **API key not working:** Even after creating the `.env` file, I couldn't get my API key to work. This was because I hadn't installed `python-dotenv`.
- **Reasoning effort hardcoded:** I had initially hardcoded reasoning effort to "low." I later dropped this so the program wouldn't fail when using older models, like `gpt-4.1`, that don't support that parameter.

## What I learned
- I learned what each of the import lines actually does. For example, `from time import time` pulls in the `time` function that measures how long the API call takes.
- I learned I needed to call `load_dotenv()` to read the `.env` file — something I'd never done before.
- I learned that agent behavior is determined by the prompt, not by the code itself. The code stays the same, but the behavior can change entirely with a different prompt file. It's genuinely exciting that I can write essentially any program I want around a powerful OpenAI model just by changing the prompt.

## Why this matters in the context of agent engineering
This matters because this is the most basic form of an agent—the primitive, foundational block that will then be used to build multi-agent systems. These can also be orchestrated together to become a machine of thousands of agents. I need to understand this before delving further because agent engineering is built on this.

## How many hours I spent
I spent 4 hours on this homework.
