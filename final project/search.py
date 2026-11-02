"""Semantic search across scriptures, general conference, and BYU Speeches."""

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
from openai import OpenAI

from settings import COURSE_DIR, DATA_DIR, MODEL


SCRIPTURE_CACHE = COURSE_DIR / "hw2d" / "cache-verse"
SOURCES = ("scripture", "conference", "byu")
VOLUME_SLUGS = {
    "old_testament": "ot",
    "new_testament": "nt",
    "book_of_mormon": "bofm",
    "doctrine_and_covenants": "dc-testament",
    "pearl_of_great_price": "pgp",
}
BOOK_SLUGS = {
    "Abraham": "abr", "Moses": "moses", "JS-History": "js-h",
    "JS-Matthew": "js-m", "Articles of Faith": "a-of-f",
    "D&C": "dc", "Alma": "alma", "Ether": "ether",
    "Helaman": "hel", "Mormon": "morm", "Moroni": "moro",
    "Mosiah": "mosiah", "Jacob": "jacob", "Enos": "enos",
    "Jarom": "jarom", "Omni": "omni", "1 Nephi": "1-ne",
    "2 Nephi": "2-ne", "3 Nephi": "3-ne", "4 Nephi": "4-ne",
    "Words of Mormon": "w-of-m", "Jeremiah": "jer", "Job": "job",
    "Isaiah": "isa", "Genesis": "gen", "Psalms": "ps",
    "Proverbs": "prov", "Ecclesiastes": "eccl", "Matthew": "matt",
    "Mark": "mark", "Luke": "luke", "John": "john",
    "Acts": "acts", "Romans": "rom", "Ephesians": "eph",
    "Hebrews": "heb", "Revelation": "rev", "1 Corinthians": "1-cor",
    "2 Corinthians": "2-cor", "1 Peter": "1-pet",
    "2 Peter": "2-pet", "1 Timothy": "1-tim",
    "2 Timothy": "2-tim",
}


def scripture_url(record: dict) -> str:
    reference = record["ref"]
    book, location = reference.rsplit(" ", 1)
    chapter, verse = location.split(":", 1)
    volume = VOLUME_SLUGS[record["volume"]]
    slug = BOOK_SLUGS.get(book, re.sub(r"[^a-z0-9]+", "-", book.lower()).strip("-"))
    return f"https://www.churchofjesuschrist.org/study/scriptures/{volume}/{slug}/{chapter}?lang=eng#p{verse}"


def load_index(source: str, scripture_cache: Path) -> tuple[np.ndarray, list[dict]]:
    stem = scripture_cache if source == "scripture" else DATA_DIR / source
    vector_path = stem.with_suffix(".npy")
    metadata_path = stem.with_suffix(".json")
    if not vector_path.exists() or not metadata_path.exists():
        if source == "scripture":
            raise FileNotFoundError(f"Missing scripture cache at {stem}; see README.md")
        raise FileNotFoundError(f"Missing {source} index; run build_index.py first")

    vectors = np.load(vector_path, mmap_mode="r")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if source == "scripture":
        records = metadata
    else:
        if metadata["model"] != MODEL:
            raise ValueError(f"{source} index uses {metadata['model']}; rebuild it with {MODEL}")
        records = metadata["records"]
    if vectors.ndim != 2 or vectors.shape[0] != len(records):
        raise ValueError(f"{source} index has mismatched vectors and records; rebuild it")
    return vectors, records


def search(query: str, indexes: dict, limit: int, per_source: bool = False) -> list[dict]:
    embedding = OpenAI().embeddings.create(model=MODEL, input=[query]).data[0].embedding
    query_vector = np.asarray(embedding, dtype=np.float32)
    query_vector /= np.linalg.norm(query_vector)
    candidates = []
    for source, (vectors, records) in indexes.items():
        if vectors.shape[1] != len(query_vector):
            raise ValueError(f"{source} index has a different embedding dimension")
        scores = vectors @ query_vector
        count = min(len(records), max(50, limit * 30))
        top = np.argpartition(-scores, count - 1)[:count]
        for index in top:
            record = records[int(index)]
            candidates.append({
                "source": source,
                "score": float(scores[index]),
                "reference": record["ref"] if source == "scripture" else record["title"],
                "speaker": record.get("speaker", ""),
                "date": record.get("date", ""),
                "url": scripture_url(record) if source == "scripture" else record["url"],
                "text": record["text"],
                "document_id": record["ref"] if source == "scripture" else record["document_id"],
            })

    hits = []
    seen = set()
    source_counts = {source: 0 for source in indexes}
    for hit in sorted(candidates, key=lambda item: item["score"], reverse=True):
        key = (hit["source"], hit["document_id"])
        if key in seen or (per_source and source_counts[hit["source"]] >= limit):
            continue
        hits.append(hit)
        seen.add(key)
        source_counts[hit["source"]] += 1
        if len(hits) >= limit * (len(indexes) if per_source else 1):
            break
    for hit in hits:
        del hit["document_id"]
    return hits


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="*")
    parser.add_argument("--source", choices=("all",) + SOURCES, default="all")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--scripture-cache", type=Path, default=SCRIPTURE_CACHE)
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--per-source", action="store_true", help="show --limit results from each source")
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be at least 1")
    if args.per_source and args.source != "all":
        parser.error("--per-source requires --source all")
    selected = SOURCES if args.source == "all" else (args.source,)
    indexes = {source: load_index(source, args.scripture_cache) for source in selected}
    if args.stats:
        for source, (_, records) in indexes.items():
            documents = len({record.get("document_id", record.get("ref")) for record in records})
            print(f"{source}: {documents} documents, {len(records)} searchable passages")
        return
    query = " ".join(args.query).strip()
    if not query:
        parser.error("provide a search query or use --stats")
    hits = search(query, indexes, args.limit, args.per_source)
    if args.json:
        print(json.dumps(hits, ensure_ascii=False, indent=2))
        return
    for rank, hit in enumerate(hits, 1):
        label = f"{hit['reference']} — {hit['speaker']}" if hit["speaker"] else hit["reference"]
        date = f" ({hit['date']})" if hit["date"] else ""
        excerpt = hit["text"].replace("\n", " ")[:360].strip()
        print(f"{rank}. [{hit['source']}] {label}{date}  cosine={hit['score']:.3f}")
        print(f"   {excerpt}{'…' if len(hit['text']) > 360 else ''}")
        print(f"   {hit['url']}\n")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
