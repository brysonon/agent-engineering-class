"""Search the embedded scriptures, and run the experiments for the write-up.

Reads the cache built by embed_corpus.py, so queries are cheap -- only the
query itself gets embedded.

    python search.py "I existed before I was born"
    python search.py --experiments
"""

import argparse
import json
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parent.parent / '.env')

MODEL = 'text-embedding-3-small'

# What the doctrine of foreordination actually sounds like in each volume.
# Almost no shared vocabulary, which is the point.
FOREORDINATION_REFS = [
    'Jeremiah 1:5',
    'Job 38:7',
    'Ephesians 1:4',
    'Alma 13:3',
    'Abraham 3:22',
    'Abraham 3:23',
    'D&C 138:55',
]

PARAPHRASES = [
    'I existed before I was born',
    'God knew me before I came to earth',
    'chosen beforehand for a purpose',
    'we lived with God in a life before this one',
    'foreordination and the premortal existence',
]


class Index:
    def __init__(self, stem: Path):
        self.vectors = np.load(stem.with_suffix('.npy'))
        self.units = json.loads(stem.with_suffix('.json').read_text(encoding='utf-8'))
        self.by_ref = {u['ref']: i for i, u in enumerate(self.units)}
        self.client = OpenAI()

    def embed(self, text: str) -> np.ndarray:
        vector = np.array(
            self.client.embeddings.create(model=MODEL, input=[text]).data[0].embedding,
            dtype=np.float32,
        )
        return vector / np.linalg.norm(vector)

    def search(self, query: str, k: int = 10) -> list[tuple[float, dict]]:
        # Vectors are pre-normalized, so the dot product is the cosine.
        scores = self.vectors @ self.embed(query)
        top = np.argsort(-scores)[:k]
        return [(float(scores[i]), self.units[i]) for i in top]

    def similarity(self, ref_a: str, ref_b: str) -> float:
        return float(self.vectors[self.by_ref[ref_a]] @ self.vectors[self.by_ref[ref_b]])

    def rank_of(self, query: str, ref: str) -> int:
        """Where a known verse lands for a query. 1 is best; 0 means missing."""
        scores = self.vectors @ self.embed(query)
        order = np.argsort(-scores)
        target = self.by_ref.get(ref)
        if target is None:
            return 0
        return int(np.where(order == target)[0][0]) + 1


def show(results, indent='    '):
    for score, unit in results:
        volume = unit['volume'].replace('_', ' ')
        print(f"{indent}{score:.3f}  {unit['ref']:20} [{volume}]  {unit['text'][:90]}")


def experiments(index: Index):
    print('=' * 78)
    print('1. SAME MEANING, DIFFERENT WORDING')
    print('   Does one plain-English query find the doctrine across all volumes?')
    print('=' * 78)
    for query in PARAPHRASES[:2]:
        print(f'\n  query: "{query}"')
        show(index.search(query, 8))

    print('\n' + '=' * 78)
    print('2. WHERE EACH KNOWN PASSAGE RANKS FOR EACH PARAPHRASE')
    print('   Low number = found easily. 0 = not in the corpus.')
    print('=' * 78)
    header = '  ' + 'reference'.ljust(16) + ''.join(f'{i + 1:>8}' for i in range(len(PARAPHRASES)))
    print(header)
    for ref in FOREORDINATION_REFS:
        row = ''.join(f'{index.rank_of(q, ref):>8}' for q in PARAPHRASES)
        print(f'  {ref:16}{row}')
    print('\n  queries:')
    for i, q in enumerate(PARAPHRASES, 1):
        print(f'    {i}. "{q}"')

    print('\n' + '=' * 78)
    print('3. SIMILAR vs DISSIMILAR PAIRS')
    print('   Same doctrine in different words, vs verses that share words only.')
    print('=' * 78)
    pairs = [
        ('Jeremiah 1:5', 'Abraham 3:23', 'same doctrine, no shared wording'),
        ('Ephesians 1:4', 'Alma 13:3', 'same doctrine, both say "foundation of the world"'),
        ('Jeremiah 1:5', 'Alma 13:3', 'same doctrine, different volumes'),
        ('Jeremiah 1:5', 'Genesis 5:3', 'both about being born -- different doctrine'),
        ('Abraham 3:23', 'Genesis 1:1', 'both about creation -- different doctrine'),
    ]
    for a, b, note in pairs:
        if a in index.by_ref and b in index.by_ref:
            print(f'  {index.similarity(a, b):.3f}  {a:16} <-> {b:16}  ({note})')

    print('\n' + '=' * 78)
    print('4. FALSE POSITIVES: the "foundation of the world" trap')
    print('   45 verses use this phrase. Most are not about foreordination.')
    print('=' * 78)
    print('\n  query: "foundation of the world"')
    show(index.search('foundation of the world', 10))


def main(args):
    index = Index(args.cache)
    if args.experiments:
        experiments(index)
    elif args.query:
        show(index.search(args.query, args.k), indent='  ')
    else:
        print('Give a query, or pass --experiments.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Search the embedded scriptures')
    parser.add_argument('query', nargs='?')
    parser.add_argument('-k', type=int, default=10)
    parser.add_argument('--cache', type=Path, default=Path(__file__).with_name('cache-verse'))
    parser.add_argument('--experiments', action='store_true')
    main(parser.parse_args())
