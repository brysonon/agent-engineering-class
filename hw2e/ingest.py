"""Ingest the downloaded General Conference talks into a local ChromaDB.

Run once after download_gc_talks.py. It embeds ~43k words with
text-embedding-3-small, which costs well under a cent.

    python ingest.py
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
load_dotenv(HERE.parent / '.env')

# Reuse the course's ingest_folder as-is instead of copying it here.
sys.path.insert(0, str(HERE.parent / 'classwork' / '2e'))
from chroma_demo import ingest_folder  # noqa: E402

CHROMA_DIR = HERE / 'chroma'
COLLECTION = 'gc-2026-10'
TALKS_DIR = HERE / 'talks'

if __name__ == '__main__':
    ingest_folder(str(CHROMA_DIR), COLLECTION, str(TALKS_DIR))
