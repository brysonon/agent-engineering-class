"""Embed every verse in the scriptures folder and cache the result to disk.

Run this once. It costs about three cents and takes a few minutes. Everything
else reads the cache, so exploring queries is free after this.

    python embed_corpus.py
    python embed_corpus.py --level chapter --out chapters
"""

import argparse
import json
from pathlib import Path
from time import time

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parent.parent / '.env')

MODEL = 'text-embedding-3-small'
MAX_ITEMS = 500
# The API caps a single request at 300k tokens. A batch of 500 verses is tiny,
# but 500 chapters is roughly 600k tokens and gets rejected, so batches have to
# be built by size rather than by count.
MAX_TOKENS = 250_000
TOKENS_PER_WORD = 1.4

# The folders use short slugs. These are the ones I actually cite, so the
# output reads like a scripture reference instead of a file path.
BOOK_NAMES = {
    'abr': 'Abraham', 'moses': 'Moses', 'js-h': 'JS-History', 'js-m': 'JS-Matthew',
    'a-of-f': 'Articles of Faith', 'dc': 'D&C', 'alma': 'Alma', 'ether': 'Ether',
    'hel': 'Helaman', 'morm': 'Mormon', 'moro': 'Moroni', 'mosiah': 'Mosiah',
    'jacob': 'Jacob', 'enos': 'Enos', 'jarom': 'Jarom', 'omni': 'Omni',
    '1-ne': '1 Nephi', '2-ne': '2 Nephi', '3-ne': '3 Nephi', '4-ne': '4 Nephi',
    'w-of-m': 'Words of Mormon', 'jer': 'Jeremiah', 'job': 'Job', 'isa': 'Isaiah',
    'gen': 'Genesis', 'ps': 'Psalms', 'prov': 'Proverbs', 'eccl': 'Ecclesiastes',
    'matt': 'Matthew', 'mark': 'Mark', 'luke': 'Luke', 'john': 'John',
    'acts': 'Acts', 'rom': 'Romans', 'eph': 'Ephesians', 'heb': 'Hebrews',
    'rev': 'Revelation', '1-cor': '1 Corinthians', '2-cor': '2 Corinthians',
    '1-pet': '1 Peter', '2-pet': '2 Peter', '1-tim': '1 Timothy', '2-tim': '2 Timothy',
}


def pretty(book_slug: str) -> str:
    return BOOK_NAMES.get(book_slug, book_slug.replace('-', ' ').title())


def load_units(root: Path, level: str) -> list[dict]:
    """One record per verse, or one per chapter if level == 'chapter'."""
    units = []
    for chapter_file in sorted(root.rglob('*.txt')):
        parts = chapter_file.relative_to(root).parts
        if len(parts) < 3:
            continue
        volume, book, filename = parts[0], parts[1], parts[-1]
        chapter = int(filename.removesuffix('.txt'))
        lines = [l.strip() for l in chapter_file.read_text(encoding='utf-8', errors='replace').splitlines() if l.strip()]
        if not lines:
            continue

        if level == 'chapter':
            units.append({
                'ref': f'{pretty(book)} {chapter}',
                'volume': volume,
                'text': ' '.join(lines),
            })
        else:
            for n, line in enumerate(lines, 1):
                units.append({
                    'ref': f'{pretty(book)} {chapter}:{n}',
                    'volume': volume,
                    'text': line,
                })
    return units


def batches(texts: list[str]):
    """Group texts so no request exceeds the item or token cap."""
    current, current_tokens = [], 0
    for text in texts:
        tokens = len(text.split()) * TOKENS_PER_WORD
        if current and (len(current) >= MAX_ITEMS or current_tokens + tokens > MAX_TOKENS):
            yield current
            current, current_tokens = [], 0
        current.append(text)
        current_tokens += tokens
    if current:
        yield current


def embed_all(client, texts: list[str]) -> np.ndarray:
    vectors = []
    start = time()
    for chunk in batches(texts):
        response = client.embeddings.create(model=MODEL, input=chunk)
        vectors.extend(d.embedding for d in response.data)
        print(f'  {len(vectors)}/{len(texts)}  ({time() - start:.0f}s)', flush=True)

    matrix = np.array(vectors, dtype=np.float32)
    # Normalize once here so similarity is a plain dot product later.
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix


def main(root: Path, level: str, out_stem: Path):
    units = load_units(root, level)
    print(f'{len(units)} {level}-level units from {root}')

    client = OpenAI()
    matrix = embed_all(client, [u['text'] for u in units])

    np.save(out_stem.with_suffix('.npy'), matrix)
    out_stem.with_suffix('.json').write_text(
        json.dumps(units, ensure_ascii=False), encoding='utf-8'
    )
    size_mb = out_stem.with_suffix('.npy').stat().st_size / 1e6
    print(f'\nSaved {matrix.shape} to {out_stem.with_suffix(".npy")} ({size_mb:.0f} MB)')
    print(f'Saved metadata to {out_stem.with_suffix(".json")}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Embed the scriptures')
    parser.add_argument('--root', type=Path, default=Path(__file__).with_name('scriptures'))
    parser.add_argument('--level', choices=['verse', 'chapter'], default='verse')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    stem = args.out or Path(__file__).with_name(f'cache-{args.level}')
    main(args.root, args.level, stem)
