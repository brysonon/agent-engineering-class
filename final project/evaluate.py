"""Evaluate retrieval quality for the semantic search prototype."""

import argparse
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from openai import OpenAI

from search import SCRIPTURE_CACHE, SOURCES, load_index
from settings import MODEL, PROJECT_DIR


QUESTION_SET = PROJECT_DIR / "eval_questions_church.json"
EMBED_BATCH_SIZE = 64
MIN_VECTOR_CANDIDATES = 200
VECTOR_CANDIDATE_MULTIPLIER = 30
KEYWORD_K1 = 1.5
KEYWORD_B = 0.75
RRF_K = 60
TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?")
STOPWORDS = {
    "a", "about", "all", "am", "an", "and", "are", "as", "at", "be", "because",
    "brings", "can", "conference", "does", "during", "for", "from", "general", "he",
    "her", "his", "how", "i", "in", "into", "is", "it", "its", "life", "lord",
    "me", "message", "of", "on", "or", "our", "people", "says", "scripture",
    "scriptures", "should", "so", "talk", "teaches", "teaching", "that", "the",
    "their", "them", "they", "this", "through", "to", "us", "verse", "what",
    "when", "which", "who", "with", "you", "your",
}


def parse_ks(value: str) -> tuple[int, ...]:
    pieces = []
    for part in value.split(","):
        text = part.strip()
        if not text:
            continue
        number = int(text)
        if number < 1:
            raise argparse.ArgumentTypeError("all k values must be at least 1")
        pieces.append(number)
    if not pieces:
        raise argparse.ArgumentTypeError("provide at least one k value")
    return tuple(sorted(set(pieces)))


def tokenize(text: str) -> list[str]:
    return [token for token in TOKEN_RE.findall(text.lower()) if token not in STOPWORDS]


def record_reference(source: str, record: dict) -> str:
    return record["ref"] if source == "scripture" else record["title"]


def record_document_id(source: str, record: dict) -> str:
    return record["ref"] if source == "scripture" else record["document_id"]


def record_url(source: str, record: dict) -> str:
    return "" if source == "scripture" else record["url"]


def gold_lookup_key(source: str, reference: str, date: str = "") -> tuple[str, str, str]:
    return source, reference, date or ""


def lexical_text(source: str, record: dict) -> str:
    if source == "scripture":
        return f"{record['ref']}\n{record['text']}"
    parts = [record["title"], record.get("speaker", ""), record.get("summary", ""), record["text"]]
    return "\n".join(part for part in parts if part)


def load_question_set(path: Path) -> tuple[dict, list[dict]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or "resources" not in payload or "questions" not in payload:
        raise ValueError(f"Question set at {path} must contain resources and questions")
    return payload["resources"], payload["questions"]


def build_gold_lookup(indexes: dict[str, tuple[np.ndarray, list[dict]]]) -> dict[tuple[str, str, str], set[str]]:
    lookup = defaultdict(set)
    by_reference = defaultdict(set)
    for source, (_, records) in indexes.items():
        for record in records:
            reference = record_reference(source, record)
            document_id = record_document_id(source, record)
            date = record.get("date", "")
            lookup[gold_lookup_key(source, reference, date)].add(document_id)
            by_reference[(source, reference)].add(document_id)
    for (source, reference), document_ids in by_reference.items():
        if len(document_ids) == 1:
            lookup[gold_lookup_key(source, reference)].update(document_ids)
    return dict(lookup)


def validate_questions(resources: dict, questions: list[dict], gold_lookup: dict[tuple[str, str, str], set[str]]) -> None:
    seen_ids = set()
    for question in questions:
        question_id = question["id"]
        if question_id in seen_ids:
            raise ValueError(f"Duplicate question id: {question_id}")
        seen_ids.add(question_id)
        if question["church_resource"] not in resources:
            raise ValueError(f"Unknown church_resource for {question_id}: {question['church_resource']}")
        if not question.get("gold"):
            raise ValueError(f"Question {question_id} has no gold answers")
        for gold in question["gold"]:
            key = gold_lookup_key(gold["source"], gold["reference"], gold.get("date", ""))
            if key not in gold_lookup:
                raise ValueError(f"Gold answer not found in indexes for {question_id}: {key}")


def build_lexical_index(indexes: dict[str, tuple[np.ndarray, list[dict]]]) -> dict:
    documents = []
    postings = defaultdict(list)
    lengths = []
    for source, (_, records) in indexes.items():
        for record in records:
            document = {
                "source": source,
                "reference": record_reference(source, record),
                "document_id": record_document_id(source, record),
                "speaker": record.get("speaker", ""),
                "date": record.get("date", ""),
                "url": record_url(source, record),
                "text": record["text"],
            }
            documents.append(document)
            counts = Counter(tokenize(lexical_text(source, record)))
            doc_index = len(documents) - 1
            lengths.append(sum(counts.values()))
            for term, frequency in counts.items():
                postings[term].append((doc_index, frequency))

    total_docs = len(documents)
    average_length = float(sum(lengths) / total_docs)
    idf = {
        term: math.log(1 + (total_docs - len(entries) + 0.5) / (len(entries) + 0.5))
        for term, entries in postings.items()
    }
    return {
        "documents": documents,
        "postings": postings,
        "lengths": np.asarray(lengths, dtype=np.float32),
        "avgdl": average_length,
        "idf": idf,
    }


def embed_queries(queries: list[str]) -> list[np.ndarray]:
    client = OpenAI()
    vectors = []
    for start in range(0, len(queries), EMBED_BATCH_SIZE):
        batch = queries[start : start + EMBED_BATCH_SIZE]
        response = client.embeddings.create(model=MODEL, input=batch)
        ordered = [None] * len(batch)
        for item in response.data:
            ordered[item.index] = item.embedding
        matrix = np.asarray(ordered, dtype=np.float32)
        matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)
        vectors.extend(matrix)
    return [np.asarray(vector, dtype=np.float32) for vector in vectors]


def dedupe_ranked_hits(candidates: list[dict], limit: int) -> list[dict]:
    hits = []
    seen = set()
    for hit in sorted(candidates, key=lambda item: item["score"], reverse=True):
        key = (hit["source"], hit["document_id"])
        if key in seen:
            continue
        hits.append(hit)
        seen.add(key)
        if len(hits) >= limit:
            break
    return hits


def vector_hits(
    query_vector: np.ndarray,
    indexes: dict[str, tuple[np.ndarray, list[dict]]],
    limit: int,
    selected_sources: tuple[str, ...] | None = None,
) -> list[dict]:
    sources = selected_sources or tuple(indexes)
    candidate_limit = max(MIN_VECTOR_CANDIDATES, limit * VECTOR_CANDIDATE_MULTIPLIER)
    candidates = []
    for source in sources:
        vectors, records = indexes[source]
        if vectors.shape[1] != len(query_vector):
            raise ValueError(f"{source} index has a different embedding dimension")
        scores = vectors @ query_vector
        count = min(len(records), candidate_limit)
        top_indices = np.argpartition(-scores, count - 1)[:count]
        for index in top_indices:
            record = records[int(index)]
            candidates.append({
                "source": source,
                "reference": record_reference(source, record),
                "document_id": record_document_id(source, record),
                "speaker": record.get("speaker", ""),
                "date": record.get("date", ""),
                "url": record_url(source, record),
                "text": record["text"],
                "score": float(scores[index]),
            })
    return dedupe_ranked_hits(candidates, limit)


def keyword_hits(query: str, lexical_index: dict, limit: int, selected_sources: tuple[str, ...] | None = None) -> list[dict]:
    query_terms = Counter(tokenize(query))
    if not query_terms:
        return []
    documents = lexical_index["documents"]
    postings = lexical_index["postings"]
    lengths = lexical_index["lengths"]
    average_length = lexical_index["avgdl"]
    idf = lexical_index["idf"]
    source_filter = set(selected_sources) if selected_sources else None
    scores = defaultdict(float)
    for term, query_frequency in query_terms.items():
        if term not in postings:
            continue
        term_idf = idf[term]
        for doc_index, term_frequency in postings[term]:
            document = documents[doc_index]
            if source_filter is not None and document["source"] not in source_filter:
                continue
            doc_length = lengths[doc_index]
            denominator = term_frequency + KEYWORD_K1 * (1 - KEYWORD_B + KEYWORD_B * doc_length / average_length)
            scores[doc_index] += query_frequency * term_idf * term_frequency * (KEYWORD_K1 + 1) / denominator
    if not scores:
        return []
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    hits = []
    seen = set()
    for doc_index, score in ranked:
        document = documents[doc_index]
        key = (document["source"], document["document_id"])
        if key in seen:
            continue
        hits.append({**document, "score": float(score)})
        seen.add(key)
        if len(hits) >= limit:
            break
    return hits


def hybrid_hits(vector_ranked: list[dict], keyword_ranked: list[dict], limit: int) -> list[dict]:
    scores = defaultdict(float)
    metadata = {}
    for ranked_hits in (vector_ranked, keyword_ranked):
        for rank, hit in enumerate(ranked_hits, 1):
            key = (hit["source"], hit["document_id"])
            scores[key] += 1 / (RRF_K + rank)
            metadata[key] = hit
    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    hits = []
    for (source, document_id), score in ordered[:limit]:
        hit = dict(metadata[(source, document_id)])
        hit["score"] = float(score)
        hits.append(hit)
    return hits


def resolve_gold_keys(question: dict, gold_lookup: dict[tuple[str, str, str], set[str]]) -> tuple[set[tuple[str, str]], tuple[str, ...]]:
    keys = set()
    sources = []
    for gold in question["gold"]:
        source = gold["source"]
        document_ids = gold_lookup[gold_lookup_key(source, gold["reference"], gold.get("date", ""))]
        for document_id in document_ids:
            keys.add((source, document_id))
        if source not in sources:
            sources.append(source)
    return keys, tuple(sources)


def first_relevant_rank(hits: list[dict], gold_keys: set[tuple[str, str]]) -> int | None:
    for rank, hit in enumerate(hits, 1):
        if (hit["source"], hit["document_id"]) in gold_keys:
            return rank
    return None


def summarize_results(results: list[dict], ks: tuple[int, ...]) -> dict:
    total = len(results)
    summary = {"count": total}
    if total == 0:
        for k in ks:
            summary[f"hit@{k}"] = 0.0
        summary[f"mrr@{max(ks)}"] = 0.0
        return summary
    for k in ks:
        summary[f"hit@{k}"] = sum(1 for result in results if result["rank"] is not None and result["rank"] <= k) / total
    max_k = max(ks)
    summary[f"mrr@{max_k}"] = sum(
        1 / result["rank"] if result["rank"] is not None and result["rank"] <= max_k else 0.0
        for result in results
    ) / total
    return summary


def format_percent(value: float) -> str:
    return f"{value:.1%}"


def print_table(title: str, summaries: dict[str, dict], ks: tuple[int, ...]) -> None:
    metric_names = [f"hit@{k}" for k in ks] + [f"mrr@{max(ks)}"]
    headers = ["mode", "count"] + metric_names
    rows = []
    for mode, summary in summaries.items():
        row = [mode, str(summary["count"])]
        row.extend(format_percent(summary[name]) for name in metric_names)
        rows.append(row)
    widths = [len(header) for header in headers]
    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))
    print(title)
    print("  ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    for row in rows:
        print("  ".join(value.ljust(widths[index]) for index, value in enumerate(row)))
    print()


def top_hit_summary(hit: dict | None) -> dict | None:
    if hit is None:
        return None
    return {
        "source": hit["source"],
        "reference": hit["reference"],
        "score": hit["score"],
    }


def run_evaluation(args: argparse.Namespace) -> dict:
    resources, questions = load_question_set(args.questions)
    selected_sources = SOURCES if args.source == "all" else (args.source,)
    indexes = {source: load_index(source, args.scripture_cache) for source in selected_sources}
    gold_lookup = build_gold_lookup(indexes)
    validate_questions(resources, questions, gold_lookup)

    filtered_questions = []
    for question in questions:
        gold_sources = {gold["source"] for gold in question["gold"]}
        if not gold_sources.issubset(selected_sources):
            continue
        if args.gold_source != "all" and gold_sources != {args.gold_source}:
            continue
        if args.tag and not set(args.tag).issubset(set(question.get("tags", []))):
            continue
        filtered_questions.append(question)
    if args.question_limit is not None:
        filtered_questions = filtered_questions[: args.question_limit]
    if not filtered_questions:
        raise ValueError("No questions remain after filtering")

    lexical_index = build_lexical_index(indexes)
    query_vectors = embed_queries([question["question"] for question in filtered_questions])
    ranking_limit = max(100, max(args.ks) * 10)
    modes = args.modes
    results_by_mode = {mode: [] for mode in modes}

    for question, query_vector in zip(filtered_questions, query_vectors):
        gold_keys, gold_sources = resolve_gold_keys(question, gold_lookup)
        vector_ranked = None
        keyword_ranked = None
        for mode in modes:
            if mode == "vector":
                hits = vector_hits(query_vector, indexes, ranking_limit)
            elif mode == "vector-per-source":
                hits = vector_hits(query_vector, indexes, ranking_limit, selected_sources=gold_sources)
            elif mode == "keyword":
                hits = keyword_hits(question["question"], lexical_index, ranking_limit)
            elif mode == "hybrid":
                if vector_ranked is None:
                    vector_ranked = vector_hits(query_vector, indexes, ranking_limit)
                if keyword_ranked is None:
                    keyword_ranked = keyword_hits(question["question"], lexical_index, ranking_limit)
                hits = hybrid_hits(vector_ranked, keyword_ranked, ranking_limit)
            else:
                raise ValueError(f"Unknown mode: {mode}")
            if mode == "vector":
                vector_ranked = hits
            if mode == "keyword":
                keyword_ranked = hits
            rank = first_relevant_rank(hits, gold_keys)
            results_by_mode[mode].append({
                "id": question["id"],
                "question": question["question"],
                "gold": question["gold"],
                "gold_sources": list(gold_sources),
                "rank": rank,
                "top_hit": top_hit_summary(hits[0] if hits else None),
                "church_resource": resources[question["church_resource"]],
            })

    overall = {mode: summarize_results(results, args.ks) for mode, results in results_by_mode.items()}
    by_source = {}
    for source in sorted({result["gold_sources"][0] for results in results_by_mode.values() for result in results}):
        by_source[source] = {
            mode: summarize_results([result for result in results if result["gold_sources"] == [source]], args.ks)
            for mode, results in results_by_mode.items()
        }

    misses = {}
    for mode, results in results_by_mode.items():
        misses[mode] = [
            {
                "id": result["id"],
                "question": result["question"],
                "gold": result["gold"],
                "rank": result["rank"],
                "top_hit": result["top_hit"],
            }
            for result in results
            if result["rank"] is None or result["rank"] > max(args.ks)
        ][: args.show_misses]

    return {
        "question_count": len(filtered_questions),
        "modes": modes,
        "ks": list(args.ks),
        "overall": overall,
        "by_source": by_source,
        "misses": misses,
    }


def parse_modes(value: str) -> list[str]:
    modes = [part.strip() for part in value.split(",") if part.strip()]
    allowed = {"vector", "vector-per-source", "keyword", "hybrid"}
    invalid = [mode for mode in modes if mode not in allowed]
    if invalid:
        raise argparse.ArgumentTypeError(f"unsupported mode(s): {', '.join(invalid)}")
    if not modes:
        raise argparse.ArgumentTypeError("provide at least one mode")
    return modes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, default=QUESTION_SET)
    parser.add_argument("--scripture-cache", type=Path, default=SCRIPTURE_CACHE)
    parser.add_argument("--source", choices=("all",) + SOURCES, default="all")
    parser.add_argument("--gold-source", choices=("all",) + SOURCES, default="all")
    parser.add_argument("--tag", action="append")
    parser.add_argument("--ks", type=parse_ks, default=(1, 3, 5, 10))
    parser.add_argument("--modes", type=parse_modes, default=["vector", "vector-per-source", "keyword", "hybrid"])
    parser.add_argument("--show-misses", type=int, default=5)
    parser.add_argument("--question-limit", type=int)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.show_misses < 0:
        parser.error("--show-misses must be at least 0")
    if args.question_limit is not None and args.question_limit < 1:
        parser.error("--question-limit must be at least 1")

    report = run_evaluation(args)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    print_table("Overall", report["overall"], tuple(report["ks"]))
    for source, summaries in report["by_source"].items():
        print_table(f"Gold source: {source}", summaries, tuple(report["ks"]))
    for mode, misses in report["misses"].items():
        if not misses:
            continue
        print(f"Misses for {mode}")
        for miss in misses:
            gold = ", ".join(entry["reference"] for entry in miss["gold"])
            top_hit = "none" if miss["top_hit"] is None else f"{miss['top_hit']['source']} / {miss['top_hit']['reference']}"
            rank = "not found" if miss["rank"] is None else str(miss["rank"])
            print(f"- {miss['id']}: rank={rank}; gold={gold}; top1={top_hit}")
        print()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
