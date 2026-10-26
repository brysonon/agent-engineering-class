"""Chatbot that answers doctrinal questions from October 2026 General Conference.

RAG-as-a-tool: the model decides when to search, can search more than once,
and can open a specific talk by speaker. Keeps the conversation going so you
can ask follow-ups.

    python chat.py                                      # interactive
    python chat.py "What is the gathering of Israel?"   # one question
"""

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

import gc_search
from tools import ToolBox
from usage import print_usage

HERE = Path(__file__).resolve().parent
load_dotenv(HERE.parent / '.env')

INSTRUCTIONS = (HERE / 'system_prompt.md').read_text(encoding='utf-8')

toolbox = ToolBox()


@toolbox.tool
def search_talks(query: str) -> str:
    """Semantic search over the October 2026 General Conference talks. Returns the 3 most relevant talks in full, with speaker and title. Phrase the query as the idea you are looking for, not as keywords."""
    hits = gc_search.search(query, n_talks=3)
    return '\n\n=====\n\n'.join(
        f"TALK: {h['title']}\nSPEAKER: {h['speaker']}\nFILE: {h['filename']}\n\n{h['text']}"
        for h in hits
    )


@toolbox.tool
def list_talks() -> str:
    """List every talk in the conference with its speaker, title, and filename."""
    return '\n'.join(f"{t['filename']}: {t['title']} - {t['speaker']}" for t in gc_search.list_talks())


@toolbox.tool
def read_talk(filename: str) -> str:
    """Read one whole talk by its filename from list_talks, e.g. 32_david_a_bednar.txt."""
    path = gc_search.TALKS_DIR / Path(filename).name
    if not path.is_file():
        return f'No talk named {filename}. Call list_talks to see the filenames.'
    return path.read_text(encoding='utf-8')


def answer(client: OpenAI, model: str, history: list, usages: list, events: list | None = None) -> str:
    """Run the tool loop until the model gives a final answer. Mutates history."""
    while True:
        response = client.responses.create(
            model=model,
            instructions=INSTRUCTIONS,
            input=history,
            tools=toolbox.tools,
        )
        usages.append((model, response.usage))
        history.extend(response.output)

        function_calls = [item for item in response.output if item.type == 'function_call']
        if not function_calls:
            return response.output_text.strip()

        for item in function_calls:
            arguments = json.loads(item.arguments)
            print(f'  [{item.name}({", ".join(map(repr, arguments.values()))})]', file=sys.stderr)
            result = toolbox.get_tool_function(item.name)(**arguments)
            if events is not None:
                events.append({'tool': item.name, 'arguments': arguments})
            history.append({'type': 'function_call_output', 'call_id': item.call_id, 'output': result})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('question', nargs='*')
    parser.add_argument('--model', default='gpt-5.6-luna')
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')

    client = OpenAI()
    history, usages = [], []

    if args.question:
        history.append({'role': 'user', 'content': ' '.join(args.question)})
        print(answer(client, args.model, history, usages))
        print_usage(usages)
        return

    print('Ask a question about the October 2026 General Conference (blank line to quit).')
    while (question := input('\nYou: ').strip()):
        history.append({'role': 'user', 'content': question})
        print('\nAssistant:', answer(client, args.model, history, usages))
    print_usage(usages)


if __name__ == '__main__':
    main()
