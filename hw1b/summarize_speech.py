import argparse
import json
import sys
from pathlib import Path
from time import time

from dotenv import load_dotenv
from openai import OpenAI

from schemas import SPEECH_SCHEMA
from usage import print_usage

load_dotenv()

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

SIGNAL_LABELS = {
    'repeated_throughout': 'returned to throughout the speech',
    'stated_as_purpose': 'stated outright as the purpose',
    'personal_experience': 'taught through personal experience',
    'direct_invitation': 'given as a direct invitation',
    'closing_testimony': 'chosen as the closing testimony',
}

ATTRIBUTION_LABELS = {
    'scripture': 'Scripture',
    'living_prophet': 'Prophet or Church leader',
    'speaker_testimony': 'Speaker witness',
    'unattributed': 'Unattributed',
}


def quote_block(text: str) -> list[str]:
    return ['> ' + line if line else '>' for line in text.strip().splitlines()]


def render(summary: dict) -> str:
    lines = [f"# {summary['title'] or 'Speech Summary'}", '']

    if summary['speaker']:
        lines += [f"**Speaker:** {summary['speaker']}", '']

    lines += ['*' + summary['one_sentence_summary'] + '*', '', '---', '']

    lines += ['## Key Take-aways', '']
    if summary['key_takeaways']:
        for number, item in enumerate(summary['key_takeaways'], start=1):
            lines += [f"### {number}. {item['takeaway']}", '']
            lines += quote_block(item['quote'])
            lines += ['']
    else:
        lines += ['*None identified.*', '']

    lines += ['## What Mattered Most to the Speaker', '']
    if summary['speaker_emphasis']:
        for item in summary['speaker_emphasis']:
            label = SIGNAL_LABELS.get(item['signal'], item['signal'])
            lines += [f"### {item['message']}", '', f'*Signal: {label}*', '']
            lines += quote_block(item['quote'])
            lines += ['']
    else:
        lines += ['*None identified.*', '']

    lines += ['## Promises from the Lord', '']
    if summary['divine_promises']:
        lines += ['| Promise | Given on condition of | Grounded in |', '|---|---|---|']
        for item in summary['divine_promises']:
            condition = item['condition'] or '*stated unconditionally*'
            attribution = ATTRIBUTION_LABELS.get(item['attribution'], item['attribution'])
            promise = item['promise'].replace('|', r'\|')
            condition = condition.replace('|', r'\|')
            lines += [f'| {promise} | {condition} | {attribution} |']
        lines += ['']
        for item in summary['divine_promises']:
            lines += [f"**{item['promise']}**", '']
            lines += quote_block(item['quote'])
            lines += ['']
    else:
        lines += ['*None identified.*', '']

    return '\n'.join(lines).rstrip() + '\n'


def main(model: str, prompt: str, speech: str, out_file: Path | None, reasoning_effort: str | None):
    if not speech.strip():
        raise SystemExit('The speech file is empty. Paste the transcript into it first.')

    client = OpenAI()
    extra = {'reasoning': {'effort': reasoning_effort}} if reasoning_effort else {}

    start = time()
    response = client.responses.create(
        model=model,
        input=f'{prompt}\n\n{speech}',
        text={
            'format': {
                'type': 'json_schema',
                'name': 'speech',
                'schema': SPEECH_SCHEMA,
                'strict': True,
            }
        },
        **extra,
    )
    elapsed = round(time() - start, 2)

    if response.status == 'incomplete':
        reason = getattr(response.incomplete_details, 'reason', 'unknown')
        raise SystemExit(f'Response incomplete ({reason}); the summary would be truncated.')

    summary = json.loads(response.output_text)
    report = render(summary)

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
