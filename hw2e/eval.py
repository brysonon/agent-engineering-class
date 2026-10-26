"""Run a fixed set of questions through the chatbot and check its quotes.

For every answer this records which talks the agent opened, whether it found
the talk I expected, and whether each quoted phrase actually appears word for
word somewhere in the conference. That last check is what caught the bot
quoting D&C 107:23 from memory and attributing it to Elder Caussé.

    python eval.py --label v1                           # RAG with system_prompt.md
    python eval.py --label v2 --prompt system_prompt_v2.md
    python eval.py --label no-rag --no-rag              # same model, no tools
"""

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from openai import OpenAI

import chat
import gc_search
from usage import _aggregate_usage, _calculate_cost_usd

HERE = Path(__file__).resolve().parent

# (question, talk files I expect a good answer to draw on; empty = not covered)
QUESTIONS = [
    ('Why do we need living prophets today?', ['05_vaiangina_sikahema.txt']),
    ("How can the Holy Ghost comfort me when I'm grieving?", ['18_matthew_j_eyring.txt']),
    ('Why should I pay tithing when money is tight?', ['13_patricio_m_giuffra.txt', '31_moises_villanueva.txt']),
    ('What does it mean to be sealed by the Holy Spirit of Promise?', ['32_david_a_bednar.txt']),
    ('What did President Oaks say in his closing remarks?', ['38_dallin_h_oaks.txt']),
    ('How should I talk to people I strongly disagree with?', ['26_alfred_kyungu.txt']),
    ('What is the purpose of fasting?', ['07_ulisses_soares.txt']),
    ('How can our ward be united when members are so different from each other?', ['29_dieter_f_uchtdorf.txt']),
    ('What did Elder Christofferson teach about wisdom?', ['09_d_todd_christofferson.txt']),
    ('Is the gospel only for certain kinds of people?', ['28_dallin_h_oaks.txt']),
    ('What does the Church teach about using artificial intelligence?', []),
    ('What did the conference teach about foreordination?', []),
]

NO_RAG_INSTRUCTIONS = (
    'You are a gospel study assistant for members of The Church of Jesus Christ of Latter-day Saints. '
    'Answer doctrinal questions using the October 2026 General Conference. Quote speakers where helpful. '
    'Usually 150-350 words.'
)

# The v2 answering rules, minus the parts about my ChromaDB tools, so the only
# difference is where the text comes from.
WEB_INSTRUCTIONS = (
    'You are a gospel study assistant for members of The Church of Jesus Christ of Latter-day Saints. '
    'Answer doctrinal questions using talks from the October 2026 General Conference, which you can find '
    'with web search (churchofjesuschrist.org has the official text). Always search before answering. '
    'Quote short phrases exactly and say who said them and in which talk. Only put text in quotation marks '
    'if it appears word for word in a source you read. If the conference did not address the question, '
    'say so plainly. Usually 150-350 words.'
)


def words(text: str) -> str:
    text = text.replace('’', "'").replace('‘', "'")
    return ' '.join(re.findall(r"[a-z0-9']+", text.lower()))


TALKS = {p.name: words(p.read_text(encoding='utf-8')) for p in gc_search.TALKS_DIR.glob('*.txt')}
TITLES = {words(t['title'].strip('“”"')) for t in gc_search.list_talks()}
# Surname of each talk's speaker, e.g. 'bednar', for the attribution check.
SURNAMES = {t['filename']: words(t['speaker'].split('(')[0]).split()[-1] for t in gc_search.list_talks()}


def check_quotes(answer: str) -> list[dict]:
    """Every quoted span of 4+ words, and whether it appears verbatim in the conference.

    Bracketed edits and ellipses are allowed, so each piece between them is
    checked separately. Talk titles in quotes are skipped since they are citations.
    'attributed' is a heuristic: the surname of a speaker whose talk contains the
    quote shows up within a few hundred characters of it in the answer.
    """
    results = []
    for match in re.finditer(r'[“"]([^“”"]+)[”"]', answer):
        span = match.group(1)
        if len(span.split()) < 4 or words(span) in TITLES:
            continue
        pieces = [words(p) for p in re.split(r'\[[^\]]*\]|…|\.\.\.', span)]
        pieces = [p for p in pieces if len(p.split()) >= 2]
        found_in = [name for name, text in TALKS.items() if all(p in text for p in pieces)]
        nearby = words(answer[max(0, match.start() - 300):match.end() + 300])
        results.append({
            'quote': span,
            'verified': bool(found_in),
            'found_in': found_in,
            'attributed': any(SURNAMES[name] in nearby.split() for name in found_in),
        })
    return results


def run_one(client, model, question, expected, instructions, no_rag, web):
    usages, events = [], []
    sources = []
    history = [{'role': 'user', 'content': question}]
    if web:
        # Same model and question, but OpenAI's hosted web search instead of my ChromaDB tools.
        response = client.responses.create(
            model=model, instructions=WEB_INSTRUCTIONS, input=history, tools=[{'type': 'web_search'}])
        usages.append((model, response.usage))
        answer = response.output_text.strip()
        events = [{'tool': 'web_search', 'arguments': {}} for item in response.output if item.type == 'web_search_call']
        sources = list(dict.fromkeys(
            a.url for item in response.output if item.type == 'message'
            for part in item.content for a in getattr(part, 'annotations', []) if a.type == 'url_citation'))
    elif no_rag:
        response = client.responses.create(model=model, instructions=NO_RAG_INSTRUCTIONS, input=history)
        usages.append((model, response.usage))
        answer = response.output_text.strip()
    else:
        chat.INSTRUCTIONS = instructions
        answer = chat.answer(client, model, history, usages, events)

    # Which talks the agent actually saw, from search results and direct reads.
    seen = []
    for e in events:
        if e['tool'] == 'search_talks':
            seen += [h['filename'] for h in gc_search.search(e['arguments']['query'], n_talks=3)]
        elif e['tool'] == 'read_talk':
            seen.append(Path(e['arguments']['filename']).name)
    seen = list(dict.fromkeys(seen))

    quotes = check_quotes(answer)
    return {
        'question': question,
        'expected': expected,
        'found_expected': all(f in seen for f in expected) if expected else None,
        'tool_calls': events,
        'talks_seen': seen,
        'quotes': quotes,
        'quotes_verified': sum(q['verified'] for q in quotes),
        'quotes_attributed': sum(q['attributed'] for q in quotes),
        'sources': sources,
        'cost': _calculate_cost_usd(_aggregate_usage(usages)),
        'answer': answer,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--label', required=True)
    parser.add_argument('--prompt', default='system_prompt.md')
    parser.add_argument('--model', default='gpt-5.6-luna')
    parser.add_argument('--no-rag', action='store_true')
    parser.add_argument('--web', action='store_true', help='use OpenAI web search instead of ChromaDB')
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')

    client = OpenAI()
    instructions = (HERE / args.prompt).read_text(encoding='utf-8')
    with ThreadPoolExecutor(4) as pool:
        results = list(pool.map(
            lambda qe: run_one(client, args.model, qe[0], qe[1], instructions, args.no_rag, args.web), QUESTIONS))

    out = HERE / f'results-{args.label}.json'
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding='utf-8')

    print(f"\n{'question':<62} found  calls  verified  attrib  cost")
    for r in results:
        found = {True: 'yes', False: 'NO', None: '-'}[r['found_expected']]
        n = len(r['quotes'])
        print(f"{r['question'][:60]:<62} {found:<6} {len(r['tool_calls']):<6} "
              f"{r['quotes_verified']}/{n:<7} {r['quotes_attributed']}/{n:<5} ${r['cost']:.4f}")
    total_q = sum(len(r['quotes']) for r in results)
    total_v = sum(r['quotes_verified'] for r in results)
    total_a = sum(r['quotes_attributed'] for r in results)
    print(f"\nQuotes verified: {total_v}/{total_q}   attributed: {total_a}/{total_q}   "
          f"Total cost: ${sum(r['cost'] for r in results):.4f}")
    print(f'Saved {out.name}')


if __name__ == '__main__':
    main()
