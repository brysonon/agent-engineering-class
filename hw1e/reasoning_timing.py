# Measures how much time, how many tokens, and how much money each reasoning
# effort level costs on the same problems.
#
#   python reasoning_timing.py
#   python reasoning_timing.py --trials 5 --model gpt-5.6-luna

import argparse
import json
import statistics
from pathlib import Path
from time import time

from dotenv import load_dotenv
from openai import OpenAI

from usage import PRICING

load_dotenv(Path(__file__).resolve().parent.parent / '.env')

EFFORTS = ['none', 'low', 'medium', 'high', 'max']

PROBLEMS = {
    'trivial-fact': 'Who was the first president of the United States?',
    'gmat-quant': (
        'One hour after Yolanda started walking from X to Y, a distance of 45 miles, '
        'Bob started walking along the same road from Y to X. If Yolanda’s walking '
        'rate was 3 miles per hour and Bob’s was 4 miles per hour, how many miles '
        'had Bob walked when they met?'
    ),
    'fermi': (
        'Estimate the number of drink cups or cans that are spilled annually on '
        "BYU's campus. Produce a tightly bound estimate."
    ),
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


def run_once(client, model, prompt, effort):
    start = time()
    response = client.responses.create(
        model=model,
        input=prompt,
        reasoning={'effort': effort},
    )
    elapsed = time() - start
    usage = response.usage
    return {
        'seconds': round(elapsed, 2),
        'input_tokens': usage.input_tokens,
        'output_tokens': usage.output_tokens,
        'reasoning_tokens': usage.output_tokens_details.reasoning_tokens,
        'cost_usd': cost_usd(model, usage),
        'answer': response.output_text.strip(),
    }


def main(model, trials, out_path):
    client = OpenAI()
    rows = []

    for name, prompt in PROBLEMS.items():
        for effort in EFFORTS:
            runs = [run_once(client, model, prompt, effort) for _ in range(trials)]
            row = {
                'problem': name,
                'effort': effort,
                'trials': trials,
                'median_seconds': round(statistics.median(r['seconds'] for r in runs), 2),
                'median_reasoning_tokens': int(
                    statistics.median(r['reasoning_tokens'] for r in runs)
                ),
                'median_output_tokens': int(
                    statistics.median(r['output_tokens'] for r in runs)
                ),
                'mean_cost_usd': statistics.mean(r['cost_usd'] for r in runs),
                'runs': runs,
            }
            rows.append(row)
            print(
                f"{name:14s} {effort:7s} "
                f"{row['median_seconds']:6.2f}s  "
                f"reasoning={row['median_reasoning_tokens']:6d}  "
                f"output={row['median_output_tokens']:6d}  "
                f"${row['mean_cost_usd']:.6f}",
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
        '# Reasoning effort: time, tokens, and cost',
        '',
        f'Model: `{model}`. Median of {trials} trials per cell.',
        '',
    ]
    for name in PROBLEMS:
        lines += [
            f'## {name}',
            '',
            '| Effort | Median time (s) | Reasoning tokens | Output tokens | Cost (USD) | vs. `none` (time) | vs. `none` (cost) |',
            '|--------|-----------------|------------------|---------------|------------|-------------------|-------------------|',
        ]
        subset = [r for r in rows if r['problem'] == name]
        base = next(r for r in subset if r['effort'] == 'none')
        for r in subset:
            t_ratio = r['median_seconds'] / base['median_seconds'] if base['median_seconds'] else 0
            c_ratio = r['mean_cost_usd'] / base['mean_cost_usd'] if base['mean_cost_usd'] else 0
            lines.append(
                f"| {r['effort']} | {r['median_seconds']:.2f} | {r['median_reasoning_tokens']} | "
                f"{r['median_output_tokens']} | ${r['mean_cost_usd']:.6f} | "
                f"{t_ratio:.2f}x | {c_ratio:.2f}x |"
            )
        lines.append('')
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    print(f'Wrote {md_path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Reasoning effort timing harness')
    parser.add_argument('--model', default='gpt-5.6-luna')
    parser.add_argument('--trials', type=int, default=3)
    parser.add_argument('--out', type=Path, default=Path(__file__).with_name('timing-results.json'))
    args = parser.parse_args()
    main(args.model, args.trials, args.out)
