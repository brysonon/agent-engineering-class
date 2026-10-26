"""Retrieval over the October 2026 General Conference talks in ChromaDB.

Built on query_whole_documents from the course's chroma_demo.py, with one
change: that function returns one row per matching chunk, so a talk with three
matching chunks came back three times and filled the context with duplicates.
Here I over-fetch chunks and keep only the best chunk per talk.

    python gc_search.py "Why do we need prophets today?"
"""

import sys
import threading
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
load_dotenv(HERE.parent / '.env')

sys.path.insert(0, str(HERE.parent / 'classwork' / '2e'))
from chroma_demo import _get_whole_documents  # noqa: E402

from ingest import CHROMA_DIR, COLLECTION, TALKS_DIR  # noqa: E402

# Talks average ~7 chunks, so a handful of distinct talks needs several chunks each.
CHUNKS_PER_TALK = 5

_collection = None
# eval.py runs questions in threads, and Chroma's client setup is not thread safe.
_lock = threading.Lock()


def collection():
    global _collection
    with _lock:
        if _collection is None:
            client = chromadb.PersistentClient(path=str(CHROMA_DIR))
            _collection = client.get_collection(
                COLLECTION, embedding_function=OpenAIEmbeddingFunction(model_name='text-embedding-3-small'))
    return _collection


def talk_header(filename: str) -> tuple[str, str]:
    """(speaker line, title) from the first two lines of a talk file."""
    lines = (TALKS_DIR / filename).read_text(encoding='utf-8').splitlines()
    return lines[0], lines[1]


def search(query: str, n_talks: int = 3) -> list[dict]:
    """Best n_talks distinct talks for the query, each with its whole text."""
    q = collection().query(
        query_texts=[query],
        n_results=n_talks * CHUNKS_PER_TALK,
        include=['documents', 'metadatas', 'distances'],
    )
    best: dict[str, dict] = {}
    for chunk, meta, distance in zip(q['documents'][0], q['metadatas'][0], q['distances'][0]):
        filename = meta['filename']
        if filename not in best:
            best[filename] = {'filename': filename, 'distance': distance, 'matching_chunk': chunk}
        if len(best) == n_talks:
            break

    hits = list(best.values())
    for hit, text in zip(hits, _get_whole_documents(collection(), [h['filename'] for h in hits])):
        hit['speaker'], hit['title'] = talk_header(hit['filename'])
        hit['text'] = text
    return hits


def list_talks() -> list[dict]:
    talks = []
    for path in sorted(TALKS_DIR.glob('*.txt')):
        speaker, title = talk_header(path.name)
        talks.append({'filename': path.name, 'speaker': speaker, 'title': title})
    return talks


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    for hit in search(' '.join(sys.argv[1:]) or 'Why do we need prophets today?', n_talks=5):
        print(f"({hit['distance']:.3f}) {hit['title']} - {hit['speaker']}")
        print('   ', hit['matching_chunk'][:200].replace('\n', ' '), '...\n')
