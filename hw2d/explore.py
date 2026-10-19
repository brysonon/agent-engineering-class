"""Two follow-up experiments on the cached verse embeddings.

    python explore.py --centroid      # most and least "average" Book of Mormon verses
    python explore.py --typos         # how much do spelling mistakes hurt search?
"""

import argparse
from pathlib import Path

import numpy as np

from search import Index, show

# Each pair is the same query spelled right and spelled wrong, plus the verse
# the correct spelling should find.
TYPO_CASES = [
    ('God knew me before I came to earth', 'God knw me befor I cam to erth', 'Jeremiah 1:5'),
    ('chosen beforehand for a purpose', 'chosen befourhand for a purpos', 'Alma 13:3'),
    ('the morning stars sang together', 'the mourning stars sang togather', 'Job 38:7'),
    ('Nephi built a ship', 'Nefi bilt a shipp', '1 Nephi 17:8'),
    ('faith, hope, and charity', 'faith, hop, and charaty', 'Moroni 7:44'),
]


def centroid(index: Index, volume: str, k: int = 5):
    """The verse closest to the volume's average vector, and the farthest."""
    rows = [i for i, u in enumerate(index.units) if u['volume'] == volume]
    vectors = index.vectors[rows]
    center = vectors.mean(axis=0)
    center /= np.linalg.norm(center)
    scores = vectors @ center
    order = np.argsort(-scores)

    print(f'Most average verses in {volume} ({len(rows)} verses):')
    show([(float(scores[i]), index.units[rows[i]]) for i in order[:k]])
    print(f'\nLeast average verses in {volume}:')
    show([(float(scores[i]), index.units[rows[i]]) for i in order[-k:][::-1]])


def typos(index: Index):
    print(f'  {"query sim":>9}  {"rank ok":>7}  {"rank typo":>9}  target')
    for correct, typo, ref in TYPO_CASES:
        sim = float(index.embed(correct) @ index.embed(typo))
        print(f'  {sim:9.3f}  {index.rank_of(correct, ref):7}  {index.rank_of(typo, ref):9}  {ref}')
        print(f'             "{correct}"  vs  "{typo}"')


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Extra embedding experiments')
    parser.add_argument('--centroid', action='store_true')
    parser.add_argument('--typos', action='store_true')
    parser.add_argument('--volume', default='book_of_mormon')
    parser.add_argument('--cache', type=Path, default=Path(__file__).with_name('cache-verse'))
    args = parser.parse_args()

    index = Index(args.cache)
    if args.centroid:
        centroid(index, args.volume)
    if args.typos:
        typos(index)
    if not (args.centroid or args.typos):
        print('Pass --centroid and/or --typos.')
