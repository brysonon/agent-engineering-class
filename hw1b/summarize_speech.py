import argparse
import sys
from pathlib import Path
from time import time

from dotenv import load_dotenv
from openai import OpenAI

from usage import print_usage

load_dotenv()

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')


def main(model: str, prompt: str, speech: str, out_file: Path | None, reasoning_effort: str | None):
    if not speech.strip():
        raise SystemExit('The speech file is empty. Paste the transcript into it first.')

    client = OpenAI()
    extra = {'reasoning': {'effort': reasoning_effort}} if reasoning_effort else {}

    start = time()
    response = client.responses.create(
        model=model,
        input=f'{prompt}\n\n{speech}',
        **extra,
    )
    elapsed = round(time() - start, 2)

    if response.status == 'incomplete':
        reason = getattr(response.incomplete_details, 'reason', 'unknown')
        raise SystemExit(f'Response incomplete ({reason}); the summary would be truncated.')

    report = response.output_text.strip() + '\n'

    if out_file:
        out_file.write_text(report, encoding='utf-8')
        print(f'wrote {out_file.name}', file=sys.stderr)
    else:
        print(report)

    print(f'{elapsed} seconds elapsed', file=sys.stderr)
    print_usage([(model, response.usage)])


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Summarize a speech into a markdown report')
    parser.add_argument('speech_file', type=Path)
    parser.add_argument('--prompt', type=Path, default=Path(__file__).parent / 'speech-prompt.md')
    parser.add_argument('--model', default='gpt-5.6-luna')
    parser.add_argument('--out', type=Path, default=None)
    parser.add_argument('--reasoning', choices=['low', 'medium', 'high'], default=None)
    args = parser.parse_args()
    main(
        args.model,
        args.prompt.read_text(encoding='utf-8'),
        args.speech_file.read_text(encoding='utf-8'),
        args.out,
        args.reasoning,
    )
