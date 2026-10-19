# LLM-as-judge: scores a written answer to a conceptual exam question.
#
# Two prompt versions so the change can be measured rather than asserted:
#
#   v1  "naive"  - give the answer a score out of 5 and some feedback.
#   v2  "rubric" - check the answer against the question's required points one
#                  at a time, quote the supporting text for each, and derive the
#                  score from how many points were actually covered.
#
# Both produce the same structured output, so the only variable is the prompt.
#
#   python judge.py --version v1
#   python judge.py --version v2 --out results-v2.json

import argparse
import json
import statistics
from pathlib import Path
from time import time

from dotenv import load_dotenv
from openai import OpenAI

from questions import QUESTIONS, TIERS
from usage import PRICING

load_dotenv(Path(__file__).resolve().parent.parent / '.env')

V1_NAIVE = """You are grading a student's answer to a question from an agent
engineering course. Give the answer a score from 1 to 5 and explain your
reasoning."""

V2_RUBRIC = """You are grading a student's answer to a question from an agent
engineering course.

You will be given the question, a list of the points a complete answer must
cover, and the student's answer.

Work through the required points one at a time. For each one, decide whether
the student's answer actually contains it, and quote the words that show it. If
you cannot quote anything, the point is not covered -- an answer that gestures
at the right area without stating the idea has not earned it.

Two things to hold to while you grade:

- Length is not coverage. A long answer that restates the question in different
  words covers nothing. A short answer that states the idea plainly covers it.
- A confident answer can still be wrong. Judge what the answer claims against
  what is true, not against how sure it sounds. If the answer asserts something
  false, say so, and do not let correct-sounding vocabulary earn credit.

Derive the score from the points actually covered, minus any deduction for
claims that are wrong. Do not start from a good score and look for reasons to
lower it."""

SCHEMA = {
    'type': 'object',
    'properties': {
        'point_checks': {
            'type': 'array',
            'description': 'One entry per required point, in the order given.',
            'items': {
                'type': 'object',
                'properties': {
                    'point': {'type': 'string'},
                    'covered': {'type': 'boolean'},
                    'evidence': {
                        'type': 'string',
                        'description': 'Words quoted from the answer, or empty if not covered.',
                    },
                },
                'required': ['point', 'covered', 'evidence'],
                'additionalProperties': False,
            },
        },
        'false_claims': {
            'type': 'array',
            'description': 'Statements in the answer that are incorrect. Empty if none.',
            'items': {'type': 'string'},
        },
        'score': {
            'type': 'number',
            'description': 'Overall score from 1 to 5.',
        },
        'justification': {'type': 'string'},
    },
    'required': ['point_checks', 'false_claims', 'score', 'justification'],
    'additionalProperties': False,
}


def cost_usd(model, usage):
    rates = PRICING[model]
    cached = usage.input_tokens_details.cached_tokens
    fresh = max(usage.input_tokens - cached, 0)
    return (
        fresh * rates['input'] + cached * rates['cached'] + usage.output_tokens * rates['output']
    ) / 1_000_000


def build_input(version, question, answer):
    if version == 'v1':
        # The naive version is not shown the required points at all -- that is
        # the whole point of the comparison.
        return f"Question:\n{question['question']}\n\nStudent's answer:\n{answer}"
    points = '\n'.join(f'- {p}' for p in question['required_points'])
    return (
        f"Question:\n{question['question']}\n\n"
        f"Required points:\n{points}\n\n"
        f"Student's answer:\n{answer}"
    )


def judge_once(client, model, version, question, answer):
    instructions = V1_NAIVE if version == 'v1' else V2_RUBRIC
    start = time()
    response = client.responses.create(
        model=model,
        input=f'{instructions}\n\n{build_input(version, question, answer)}',
        reasoning={'effort': 'none'},
        text={
            'format': {
                'type': 'json_schema',
                'name': 'grade',
                'schema': SCHEMA,
                'strict': True,
            }
        },
    )
    parsed = json.loads(response.output_text)
    parsed['seconds'] = round(time() - start, 2)
    parsed['cost_usd'] = cost_usd(model, response.usage)
    parsed['output_tokens'] = response.usage.output_tokens
    return parsed


def main(model, version, out_path):
    client = OpenAI()
    rows = []

    for question in QUESTIONS:
        scores = {}
        for tier in TIERS:
            # v1 never sees required_points, but the judge's point_checks array
            # is still requested so both versions return the same shape.
            result = judge_once(client, model, version, question, question[tier])
            scores[tier] = result['score']
            rows.append({
                'question': question['id'],
                'tier': tier,
                **result,
            })
            print(f"  {question['id']:22} {tier:9} score={result['score']:.1f}", flush=True)

        ordered = scores['strong'] > scores['middling'] > scores['weak']
        separated = scores['strong'] > scores['weak']
        print(
            f"  {question['id']:22} -> strictly ordered: {ordered}, "
            f"strong>weak: {separated}\n",
            flush=True,
        )

    summarize(version, rows)
    out_path.write_text(json.dumps({'version': version, 'rows': rows}, indent=2), encoding='utf-8')
    print(f'Wrote {out_path}')


def summarize(version, rows):
    by_tier = {t: [r['score'] for r in rows if r['tier'] == t] for t in TIERS}
    ordered = separated = 0
    for question in QUESTIONS:
        s = {r['tier']: r['score'] for r in rows if r['question'] == question['id']}
        ordered += s['strong'] > s['middling'] > s['weak']
        separated += s['strong'] > s['weak']

    print(f'\n===== {version} =====')
    for tier in TIERS:
        print(f'  mean {tier:9} score: {statistics.mean(by_tier[tier]):.2f}')
    print(f'  strictly ordered: {ordered}/{len(QUESTIONS)}')
    print(f'  strong > weak:    {separated}/{len(QUESTIONS)}')
    print(f'  weak answers scoring >= 3: {sum(1 for s in by_tier["weak"] if s >= 3)}/{len(QUESTIONS)}')
    print(f'  total cost: ${sum(r["cost_usd"] for r in rows):.4f}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser('LLM-as-judge for exam answers')
    parser.add_argument('--model', default='gpt-5.6-luna')
    parser.add_argument('--version', choices=['v1', 'v2'], default='v2')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    out = args.out or Path(__file__).with_name(f'results-{args.version}.json')
    main(args.model, args.version, out)
