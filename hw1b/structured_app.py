import argparse
import json
import sys
from pathlib import Path
from time import time

from dotenv import load_dotenv
from openai import OpenAI

from schemas import SCHEMAS
from usage import print_usage

load_dotenv()


def build_text_format(schema_name: str | None) -> dict:
    if schema_name is None:
        return {'format': {'type': 'text'}}

    return {
        'format': {
            'type': 'json_schema',
            'name': schema_name,
            'schema': SCHEMAS[schema_name],
            'strict': True,
        }
    }


def main(
    model: str,
    prompt: str,
    input_text: str | None = None,
    schema_name: str | None = None,
    reasoning_effort: str | None = None,
):
    client = OpenAI()
    if input_text:
        prompt = f'{prompt}\n\n{input_text}'

    extra = {'reasoning': {'effort': reasoning_effort}} if reasoning_effort else {}

    start = time()
    response = client.responses.create(
        model=model,
        input=prompt,
        text=build_text_format(schema_name),
        **extra,
    )
    elapsed = round(time() - start, 2)

    if response.status == 'incomplete':
        reason = getattr(response.incomplete_details, 'reason', 'unknown')
        print(f'Response incomplete ({reason}); output may be truncated.', file=sys.stderr)

    if schema_name is None:
        print(response.output_text)
    else:
        print(json.dumps(json.loads(response.output_text), indent=2))

    print(f'{elapsed} seconds elapsed', file=sys.stderr)
    print_usage([(model, response.usage)])


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Completion app with structured output')
    parser.add_argument('prompt_file', type=Path)
    parser.add_argument('input_file', type=Path, nargs='?')
    parser.add_argument('--model', default='gpt-5.6-luna')
    parser.add_argument(
        '--schema',
        choices=sorted(SCHEMAS),
        default=None,
        help='Attach this JSON schema to the call. Omit for 1a plain-text behavior.',
    )
    parser.add_argument('--reasoning', choices=['low', 'medium', 'high'], default=None)
    args = parser.parse_args()
    main(
        args.model,
        args.prompt_file.read_text(encoding='utf-8'),
        args.input_file.read_text(encoding='utf-8') if args.input_file else None,
        args.schema,
        args.reasoning,
    )
