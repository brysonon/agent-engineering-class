import argparse
import sys
from pathlib import Path
from time import time

from dotenv import load_dotenv
from openai import OpenAI

from usage import print_usage

load_dotenv()


def main(model: str, reasoning: str, prompt: str):
    client = OpenAI()
    usage = []
    history = [{'role': 'system', 'content': prompt}]
    
    try:
        while True:
            user_msg = input('USER: ')
            if not user_msg:
                break
            history.append({'role': 'user', 'content': user_msg})
            
            start = time()
            kwargs = {}
            if reasoning:
                kwargs['reasoning'] = {'effort': reasoning}

            response = client.responses.create(
                model=model,
                input=history,
                **kwargs
            )
            print(response.output_text)
            usage.append((model, response.usage))
            history.extend(response.output)
        
            print(f'{round(time()-start, 2)} seconds elapsed', file=sys.stderr)
    finally:
        print_usage(usage)


# Launch app
if __name__ == "__main__":
    parser = argparse.ArgumentParser('AI Response')
    parser.add_argument('prompt_file', type=Path)
    parser.add_argument('--model', default='gpt-5.6-luna')
    parser.add_argument('--reasoning', default=None)
    args = parser.parse_args()
    main(args.model, args.reasoning, args.prompt_file.read_text())
