import argparse
import sys
from pathlib import Path
from time import time

from dotenv import load_dotenv
from openai import OpenAI

from usage import print_usage

load_dotenv()


def main(model: str, prompt: str, input_text: str | None = None):
    client = OpenAI()
    if input_text:
        prompt = f'{prompt}\n\n{input_text}'

    start = time()
    response = client.responses.create(
        model=model,
        input=prompt
    )
    print(response.output_text)

    print(f'{round(time() - start, 2)} seconds elapsed', file=sys.stderr)
    print_usage([(model, response.usage)])


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Basic completion app')
    parser.add_argument('prompt_file', type=Path)
    parser.add_argument('input_file', type=Path, nargs='?')
    parser.add_argument('--model', default='gpt-5-nano')
    args = parser.parse_args()
    main(
        args.model,
        args.prompt_file.read_text(encoding='utf-8'),
        args.input_file.read_text(encoding='utf-8') if args.input_file else None
    )
