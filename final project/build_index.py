"""Build local embedding indexes for conference talks and BYU Speeches."""

import argparse
import html
import json
import unicodedata
from pathlib import Path
from urllib.parse import urljoin, urlparse

import numpy as np
import requests
from bs4 import BeautifulSoup
from openai import OpenAI

from conference_source import conference_date_label, conference_talk_items
from settings import DATA_DIR, MODEL, PROJECT_DIR


CONFERENCES = PROJECT_DIR / "conferences.json"
SPEECH_URLS = PROJECT_DIR / "speeches.txt"
USER_AGENT = "CS301R-semantic-search/1.0 (personal course project)"
WINDOW_WORDS = 180
OVERLAP_WORDS = 30
BATCH_SIZE = 100


def normalized_title(title: str) -> str:
    plain = BeautifulSoup(html.unescape(title), "html.parser").get_text(" ", strip=True)
    folded = unicodedata.normalize("NFKD", plain).casefold()
    return "".join(character for character in folded if character.isalnum())


def chunks(text: str) -> list[str]:
    words = text.split()
    if not words:
        return []
    result = []
    step = WINDOW_WORDS - OVERLAP_WORDS
    for start in range(0, len(words), step):
        piece = words[start : start + WINDOW_WORDS]
        if len(piece) < OVERLAP_WORDS and result:
            break
        result.append(" ".join(piece))
        if start + WINDOW_WORDS >= len(words):
            break
    return result


def fetch_page(url: str) -> BeautifulSoup:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.content, "html.parser")


def conference_links(conference_url: str) -> list[tuple[str, str, str]]:
    return [
        (item["title"], item["url"], item.get("summary", ""))
        for item in conference_talk_items(conference_url)
    ]


def conference_records(folder: Path, conference_url: str) -> tuple[list[dict], int]:
    files = sorted(folder.glob("*.txt"))
    links = conference_links(conference_url)
    if not files or len(files) != len(links):
        raise ValueError(f"Found {len(files)} local talks but {len(links)} source links; check the conference folder and URL")

    records = []
    conference_date = conference_date_label(conference_url)
    for path, (source_title, url, summary) in zip(files, links):
        lines = path.read_text(encoding="utf-8").splitlines()
        if len(lines) < 3:
            raise ValueError(f"Talk has no body: {path}")
        speaker, title = lines[:2]
        if normalized_title(title) != normalized_title(source_title):
            raise ValueError(f"Talk order or title mismatch: {path.name} / {source_title}")
        for index, text in enumerate(chunks("\n".join(lines[2:]))):
            records.append({
                "source": "conference",
                "document_id": url,
                "title": title,
                "speaker": speaker,
                "date": conference_date,
                "url": url,
                "summary": summary,
                "chunk": index + 1,
                "text": text,
            })
    return records, len(files)


def all_conference_records(config_path: Path) -> tuple[list[dict], int]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, list) or not config:
        raise ValueError("Conference list must contain at least one URL and folder")
    records = []
    documents = 0
    seen_urls = set()
    for entry in config:
        folder = (config_path.parent / entry["folder"]).resolve()
        batch, count = conference_records(folder, entry["url"])
        batch_urls = {record["document_id"] for record in batch}
        duplicates = seen_urls & batch_urls
        if duplicates:
            raise ValueError(f"Duplicate conference talk: {next(iter(duplicates))}")
        seen_urls.update(batch_urls)
        records.extend(batch)
        documents += count
    return records, documents


def read_speech_urls(path: Path) -> list[str]:
    urls = []
    for line in path.read_text(encoding="utf-8").splitlines():
        url = line.strip()
        if not url or url.startswith("#"):
            continue
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != "speeches.byu.edu" or not parsed.path.startswith("/talks/"):
            raise ValueError(f"Not a BYU Speeches transcript URL: {url}")
        canonical = f"https://speeches.byu.edu{parsed.path.rstrip('/')}/"
        if canonical not in urls:
            urls.append(canonical)
    return urls


def speech_record(url: str) -> dict | None:
    page = fetch_page(url)
    body = page.select_one(".individual-speech__content")
    if body is None:
        return None
    parts = [node.get_text(" ", strip=True) for node in body.find_all(["h2", "h3", "p"])]
    text = "\n".join(part for part in parts if part)
    if len(text.split()) < 100:
        return None
    title_node = page.select_one("h1.individual-speech__title")
    speaker_node = page.select_one(".individual-speech__speakers")
    date_node = page.select_one(".individual-speech__date")
    if not title_node or not speaker_node:
        raise ValueError(f"Missing title or speaker on {url}")
    return {
        "title": title_node.get_text(" ", strip=True),
        "speaker": speaker_node.get_text(" ", strip=True),
        "date": date_node.get_text(" ", strip=True) if date_node else "",
        "url": url,
        "text": text,
    }


def byu_records(url_file: Path) -> tuple[list[dict], int]:
    records = []
    found = 0
    for url in read_speech_urls(url_file):
        speech = speech_record(url)
        if speech is None:
            print(f"Skipping speech without a published transcript: {url}")
            continue
        found += 1
        for index, text in enumerate(chunks(speech["text"])):
            records.append({
                "source": "byu",
                "document_id": url,
                "title": speech["title"],
                "speaker": speech["speaker"],
                "date": speech["date"],
                "url": url,
                "chunk": index + 1,
                "text": text,
            })
    if not records:
        raise ValueError("No BYU transcripts were found")
    return records, found


def embed_records(records: list[dict]) -> np.ndarray:
    client = OpenAI()
    vectors = []
    for start in range(0, len(records), BATCH_SIZE):
        batch = records[start : start + BATCH_SIZE]
        inputs = [
            "\n".join(
                part for part in [
                    record["title"],
                    record.get("speaker", ""),
                    record.get("summary", ""),
                    record["text"],
                ]
                if part
            )
            for record in batch
        ]
        response = client.embeddings.create(model=MODEL, input=inputs)
        vectors.extend(item.embedding for item in sorted(response.data, key=lambda item: item.index))
        print(f"Embedded {len(vectors)}/{len(records)} chunks", flush=True)
    matrix = np.asarray(vectors, dtype=np.float32)
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix


def save_index(source: str, records: list[dict], vectors: np.ndarray) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    vector_path = DATA_DIR / f"{source}.npy"
    metadata_path = DATA_DIR / f"{source}.json"
    temporary_vectors = DATA_DIR / f"{source}.npy.tmp"
    temporary_metadata = DATA_DIR / f"{source}.json.tmp"
    with temporary_vectors.open("wb") as output:
        np.save(output, vectors)
    temporary_metadata.write_text(
        json.dumps({"model": MODEL, "records": records}, ensure_ascii=False),
        encoding="utf-8",
    )
    temporary_vectors.replace(vector_path)
    temporary_metadata.replace(metadata_path)
    print(f"Saved {len(records)} {source} chunks to {DATA_DIR}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=["all", "conference", "byu"], default="all")
    parser.add_argument("--conferences", type=Path, default=CONFERENCES)
    parser.add_argument("--speech-urls", type=Path, default=SPEECH_URLS)
    args = parser.parse_args()
    for source in (["conference", "byu"] if args.source == "all" else [args.source]):
        if source == "conference":
            records, documents = all_conference_records(args.conferences)
        else:
            records, documents = byu_records(args.speech_urls)
        print(f"Found {documents} {source} documents and {len(records)} chunks")
        save_index(source, records, embed_records(records))


if __name__ == "__main__":
    main()
