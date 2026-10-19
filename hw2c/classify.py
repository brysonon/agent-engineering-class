"""Jev classifier: assign a credit tier to a written exam answer.

This grades the exact same 18 answers as judge.py, so the two approaches can be
compared directly instead of argued about. judge.py is a generative model asked
to produce a score and prose; this is a classifier asked to pick one label from
a fixed set and report how confident it is.

Requires TYPESAFE_API_KEY in the environment or in ../.env.

    python classify.py
    python classify.py --out classify-results.json
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from pathlib import Path
from time import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv

from questions import QUESTIONS, TIERS

load_dotenv(Path(__file__).resolve().parent.parent / '.env')

API_URL = 'https://api.typesafe.ai/v1/systemone'
DEFAULT_MODEL = 'jev-latest'

# The quality tier I assigned each answer by hand maps onto exactly one label,
# which is what makes accuracy measurable rather than a matter of opinion.
EXPECTED_LABEL = {
    'strong': 'full_credit',
    'middling': 'partial_credit',
    'weak': 'no_credit',
}

CRITERIA = {
    'full_credit': (
        'Covers every required point correctly and states each idea plainly enough '
        'that the specific concept is identifiable.'
    ),
    'partial_credit': (
        'Covers some required points but not all, or is broadly correct while being '
        'too vague to show the specific concept. Nothing it asserts is false.'
    ),
    'no_credit': (
        'Covers none of the required points, or describes a different concept than '
        'the one asked about, or asserts something false.'
    ),
}


def build_state(question: dict, answer: str) -> str:
    points = '\n'.join(f'- {p}' for p in question['required_points'])
    return '\n\n'.join([
        f"QUESTION\n{question['question']}",
        f'REQUIRED POINTS\n{points}',
        f'STUDENT ANSWER\n{answer}',
    ])


def call_jev(state: str, model: str) -> dict:
    api_key = os.environ.get('TYPESAFE_API_KEY')
    if not api_key:
        raise RuntimeError(
            'TYPESAFE_API_KEY is not set. Add it to the .env file at the repo root.'
        )

    payload = {
        'model': model,
        'state': state,
        'questions': {
            'grade_tier': {
                'type': 'choice',
                'instructions': 'What credit does this answer earn against the required points?',
                'criteria': CRITERIA,
            }
        },
    }

    request = Request(
        API_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as error:
        detail = error.read().decode('utf-8', errors='replace')
        raise RuntimeError(f'Jev returned HTTP {error.code}: {detail}') from error
    except URLError as error:
        raise RuntimeError(f'Could not reach Jev: {error.reason}') from error


def classify_one(question: dict, tier: str, model: str) -> dict:
    start = time()
    result = call_jev(build_state(question, question[tier]), model)
    elapsed = round(time() - start, 2)

    answer = result.get('answers', result).get('grade_tier', {})
    choice = answer.get('choice')
    probabilities = answer.get('probabilities') or {}

    return {
        'question': question['id'],
        'tier': tier,
        'expected': EXPECTED_LABEL[tier],
        'predicted': choice,
        'correct': choice == EXPECTED_LABEL[tier],
        # Confidence in the label it actually picked. A classifier gives this
        # away for free; the generative judge has no equivalent.
        'confidence': probabilities.get(choice),
        'probabilities': probabilities,
        'seconds': elapsed,
    }


def summarize(rows: list[dict]) -> None:
    correct = sum(r['correct'] for r in rows)
    print(f'\n===== Jev classifier =====')
    print(f'  accuracy: {correct}/{len(rows)} = {correct / len(rows):.1%}')

    for tier in TIERS:
        subset = [r for r in rows if r['tier'] == tier]
        hits = sum(r['correct'] for r in subset)
        print(f'  {tier:9} ({EXPECTED_LABEL[tier]:14}): {hits}/{len(subset)}')

    print('\n  confusion (expected -> predicted):')
    for tier in TIERS:
        for r in (r for r in rows if r['tier'] == tier and not r['correct']):
            print(f"    {r['question']:22} {r['expected']:14} -> {r['predicted']}")

    confidences = [r['confidence'] for r in rows if r['confidence'] is not None]
    if confidences:
        right = [r['confidence'] for r in rows if r['correct'] and r['confidence'] is not None]
        wrong = [r['confidence'] for r in rows if not r['correct'] and r['confidence'] is not None]
        print(f'\n  mean confidence overall: {statistics.mean(confidences):.3f}')
        if right:
            print(f'  mean confidence when right: {statistics.mean(right):.3f}')
        if wrong:
            print(f'  mean confidence when wrong: {statistics.mean(wrong):.3f}')
        # If wrong answers come with visibly lower confidence, a threshold can
        # route those cases to a human instead of trusting the label.

    print(f'  median seconds per call: {statistics.median(r["seconds"] for r in rows):.2f}')


def main(model: str, out_path: Path) -> int:
    rows = []
    for question in QUESTIONS:
        for tier in TIERS:
            try:
                row = classify_one(question, tier, model)
            except RuntimeError as error:
                print(f'\nError: {error}', file=sys.stderr)
                return 1
            rows.append(row)
            mark = 'ok ' if row['correct'] else 'MISS'
            conf = f"{row['confidence']:.2f}" if row['confidence'] is not None else 'n/a'
            print(
                f"  {mark} {row['question']:22} {tier:9} -> {row['predicted']:14} (conf {conf})",
                flush=True,
            )

    summarize(rows)
    out_path.write_text(json.dumps({'model': model, 'rows': rows}, indent=2), encoding='utf-8')
    print(f'\nWrote {out_path}')
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Grade exam answers with the Jev classifier.')
    parser.add_argument('--model', default=DEFAULT_MODEL)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    out = args.out or Path(__file__).with_name('classify-results.json')
    raise SystemExit(main(args.model, out))
