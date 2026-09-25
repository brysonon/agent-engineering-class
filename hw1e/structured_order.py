# Does the ORDER of fields in a structured output change accuracy?
#
# Two schemas hold the same two fields. One emits `reasoning` before `answer`,
# the other emits `answer` before `reasoning`. Because the model generates JSON
# left to right, "reasoning first" lets it think on paper before committing;
# "answer first" forces it to commit and then justify.
#
# Each ordering runs at two reasoning-effort settings:
#   none  - the JSON field is the ONLY place the model can reason
#   high  - the model already reasoned internally before emitting any JSON
#
# Problems are GMAT Critical Reasoning questions (A-E multiple choice) from
# mba.com's official sample set. These are used instead of quant problems
# because quant saturated at ~97% accuracy, leaving no headroom to detect
# any effect of field order.
#
#   python structured_order.py
#   python structured_order.py --trials 5

import argparse
import json
import statistics
from pathlib import Path
from time import time

from dotenv import load_dotenv
from openai import OpenAI

from usage import PRICING

load_dotenv(Path(__file__).resolve().parent.parent / '.env')

INSTRUCTIONS = (
    'Answer the multiple-choice question. Respond only with the JSON object described '
    'by the schema. Give `answer` as a single letter: one of A, B, C, D, or E.'
)

CHOICE_LETTERS = ['A', 'B', 'C', 'D', 'E']

# (id, question stem, {letter: choice text}, expected letter)
#
# PASTE THE GMAT CRITICAL REASONING QUESTIONS HERE.
# Left empty deliberately: the questions come from mba.com's official sample
# set, which is bot-protected and could not be fetched, and inventing
# substitutes would misrepresent the source cited in the write-up.
PROBLEMS = [
    # ('cr-1',
    #  'Stimulus paragraph goes here. Which of the following, if true, most '
    #  'seriously weakens the argument above?',
    #  {'A': 'first choice',
    #   'B': 'second choice',
    #   'C': 'third choice',
    #   'D': 'fourth choice',
    #   'E': 'fifth choice'},
    #  'C'),
]


def format_question(question, choices):
    lines = [question, '']
    lines += [f'{letter}. {choices[letter]}' for letter in CHOICE_LETTERS if letter in choices]
    return '\n'.join(lines)


def build_schema(reasoning_first: bool) -> dict:
    reasoning = ('reasoning', {
        'type': 'string',
        'description': 'Step-by-step working that leads to the answer.',
    })
    answer = ('answer', {
        'type': 'string',
        'enum': CHOICE_LETTERS,
        'description': 'The letter of the correct answer choice.',
    })
    fields = [reasoning, answer] if reasoning_first else [answer, reasoning]
    return {
        'type': 'object',
        'properties': dict(fields),
        'required': [name for name, _ in fields],
        'additionalProperties': False,
    }


ORDERINGS = {
    'reasoning-first': build_schema(True),
    'answer-first': build_schema(False),
}


def cost_usd(model, usage):
    rates = PRICING[model]
    cached = usage.input_tokens_details.cached_tokens
    fresh = max(usage.input_tokens - cached, 0)
    return (
        fresh * rates['input']
        + cached * rates['cached']
        + usage.output_tokens * rates['output']
    ) / 1_000_000


def run_once(client, model, question, schema, order_name, effort):
    start = time()
    response = client.responses.create(
        model=model,
        input=f'{INSTRUCTIONS}\n\n{question}',
        reasoning={'effort': effort},
        text={
            'format': {
                'type': 'json_schema',
                'name': order_name.replace('-', '_'),
                'schema': schema,
                'strict': True,
            }
        },
    )
    elapsed = time() - start
    parsed = json.loads(response.output_text)
    return {
        'seconds': round(elapsed, 2),
        'answer': parsed['answer'],
        'reasoning_chars': len(parsed['reasoning']),
        'reasoning_tokens': response.usage.output_tokens_details.reasoning_tokens,
        'output_tokens': response.usage.output_tokens,
        'cost_usd': cost_usd(model, response.usage),
    }


def main(model, trials, efforts, out_path):
    if not PROBLEMS:
        raise SystemExit(
            'PROBLEMS is empty - paste the GMAT Critical Reasoning questions into '
            'structured_order.py before running.'
        )
    client = OpenAI()
    rows = []

    for effort in efforts:
        for order_name, schema in ORDERINGS.items():
            results = []
            for pid, question, choices, expected in PROBLEMS:
                prompt = format_question(question, choices)
                for trial in range(trials):
                    run = run_once(client, model, prompt, schema, order_name, effort)
                    run['problem'] = pid
                    run['expected'] = expected
                    run['correct'] = run['answer'] == expected
                    results.append(run)

            correct = sum(r['correct'] for r in results)
            row = {
                'effort': effort,
                'ordering': order_name,
                'correct': correct,
                'total': len(results),
                'accuracy': correct / len(results),
                'median_seconds': round(statistics.median(r['seconds'] for r in results), 2),
                'median_reasoning_chars': int(
                    statistics.median(r['reasoning_chars'] for r in results)
                ),
                'median_reasoning_tokens': int(
                    statistics.median(r['reasoning_tokens'] for r in results)
                ),
                'total_cost_usd': sum(r['cost_usd'] for r in results),
                'results': results,
            }
            rows.append(row)
            print(
                f"effort={effort:6s} {order_name:16s} "
                f"{correct:3d}/{len(results):<3d} = {row['accuracy']:6.1%}  "
                f"{row['median_seconds']:5.2f}s  "
                f"reasoning_field={row['median_reasoning_chars']:5d} chars  "
                f"${row['total_cost_usd']:.4f}",
                flush=True,
            )

    out_path.write_text(
        json.dumps({'model': model, 'trials': trials, 'rows': rows}, indent=2),
        encoding='utf-8',
    )
    print(f'\nWrote {out_path}')
    write_markdown(model, trials, rows, out_path.with_suffix('.md'))


def write_markdown(model, trials, rows, md_path):
    lines = [
        '# Structured output: does field order change accuracy?',
        '',
        f'Model: `{model}`. {len(PROBLEMS)} problems x {trials} trials = '
        f'{len(PROBLEMS) * trials} calls per cell.',
        '',
        '| Reasoning effort | Field order | Accuracy | Median time (s) | `reasoning` field (chars) | Internal reasoning tokens | Cost (USD) |',
        '|------------------|-------------|----------|-----------------|---------------------------|---------------------------|------------|',
    ]
    for r in rows:
        lines.append(
            f"| {r['effort']} | {r['ordering']} | {r['correct']}/{r['total']} = {r['accuracy']:.1%} | "
            f"{r['median_seconds']:.2f} | {r['median_reasoning_chars']} | "
            f"{r['median_reasoning_tokens']} | ${r['total_cost_usd']:.4f} |"
        )

    lines += ['', '## Per-problem accuracy', '']
    efforts = sorted({r['effort'] for r in rows})
    for effort in efforts:
        lines += [
            f'### effort = {effort}',
            '',
            '| Problem | Expected | reasoning-first | answer-first |',
            '|---------|----------|-----------------|--------------|',
        ]
        for pid, _, _choices, expected in PROBLEMS:
            cells = []
            for order_name in ORDERINGS:
                row = next(
                    r for r in rows if r['effort'] == effort and r['ordering'] == order_name
                )
                hits = [x for x in row['results'] if x['problem'] == pid]
                cells.append(f"{sum(x['correct'] for x in hits)}/{len(hits)}")
            lines.append(f'| {pid} | {expected} | {cells[0]} | {cells[1]} |')
        lines.append('')

    md_path.write_text('\n'.join(lines), encoding='utf-8')
    print(f'Wrote {md_path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Structured output field-order experiment')
    parser.add_argument('--model', default='gpt-5.6-luna')
    parser.add_argument('--trials', type=int, default=3)
    parser.add_argument('--efforts', nargs='+', default=['none', 'high'])
    parser.add_argument('--out', type=Path, default=Path(__file__).with_name('order-results.json'))
    args = parser.parse_args()
    main(args.model, args.trials, args.efforts, args.out)
