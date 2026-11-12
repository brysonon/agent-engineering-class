"""Shared helpers for general conference discovery and import."""

from __future__ import annotations

import importlib.util
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from settings import COURSE_DIR


BASE_URL = "https://www.churchofjesuschrist.org"
ARCHIVE_URL = f"{BASE_URL}/study/general-conference?lang=eng"
CONFERENCE_PATH = re.compile(r"^/study/general-conference/(\d{4})/(\d{2})$")
BUCKET_PATH = re.compile(r"^/study/general-conference/\d{8}$")
MONTH_NAMES = {"04": "April", "10": "October"}


@lru_cache(maxsize=1)
def gc_downloader():
    script_path = COURSE_DIR / "classwork" / "2e" / "download_gc_talks.py"
    spec = importlib.util.spec_from_file_location("gc_downloader_shared", script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load downloader from {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def conference_parts(conference_url: str) -> tuple[str, str]:
    match = CONFERENCE_PATH.match(urlparse(conference_url).path)
    if not match:
        raise ValueError(f"Not a general conference URL: {conference_url}")
    return match.group(1), match.group(2)


def conference_slug(conference_url: str) -> str:
    year, month = conference_parts(conference_url)
    return f"{year}-{month}"


def conference_date_label(conference_url: str) -> str:
    year, month = conference_parts(conference_url)
    return f"{MONTH_NAMES.get(month, month)} {year}"


def conference_sort_key(conference_url: str) -> tuple[int, int]:
    year, month = conference_parts(conference_url)
    return int(year), int(month)


def discover_conference_urls(start_year: int | None = None, end_year: int | None = None) -> list[str]:
    downloader = gc_downloader()
    html = downloader.fetch_html(ARCHIVE_URL)
    state = downloader.extract_initial_state(html)
    library = state.get("library", {}) if isinstance(state, dict) else {}
    root = library.get("/eng/general-conference", {}) if isinstance(library, dict) else {}

    direct_urls = set()
    bucket_urls = set()
    for section in root.get("sections", []):
        if not isinstance(section, dict):
            continue
        for entry in section.get("entries", []):
            uri = entry.get("uri", "")
            if not isinstance(uri, str):
                continue
            absolute = downloader.normalize_url_with_lang(urljoin(BASE_URL, uri), "eng")
            path = urlparse(absolute).path
            if CONFERENCE_PATH.match(path):
                direct_urls.add(absolute)
            elif BUCKET_PATH.match(path):
                bucket_urls.add(absolute)

    urls = set(direct_urls)
    for bucket_url in bucket_urls:
        bucket_html = downloader.fetch_html(bucket_url)
        for anchor in BeautifulSoup(bucket_html, "html.parser").select("a[href]"):
            href = (anchor.get("href") or "").strip()
            absolute = downloader.normalize_url_with_lang(urljoin(bucket_url, href), "eng")
            if CONFERENCE_PATH.match(urlparse(absolute).path):
                urls.add(absolute)

    filtered = []
    for url in urls:
        year, _ = conference_parts(url)
        year_value = int(year)
        if start_year is not None and year_value < start_year:
            continue
        if end_year is not None and year_value > end_year:
            continue
        filtered.append(url)
    return sorted(filtered, key=conference_sort_key)


def conference_talk_items(conference_url: str) -> list[dict[str, str]]:
    downloader = gc_downloader()
    conference_url = downloader.normalize_url_with_lang(conference_url, "eng")
    conference_html = downloader.fetch_html(conference_url)
    conference_state = downloader.extract_initial_state(conference_html)
    items = downloader.extract_talk_items_from_state(conference_state, conference_url)
    if not items:
        items = downloader.extract_talk_items_from_html(conference_html, conference_url)
    if not items:
        raise ValueError(f"No talk links found on conference page: {conference_url}")

    for item in items:
        if item.get("title"):
            item["title"] = BeautifulSoup(item["title"], "html.parser").get_text(" ", strip=True)

    metadata = {}
    prefix = urlparse(conference_url).path.rstrip("/") + "/"
    for anchor in BeautifulSoup(conference_html, "html.parser").select("li a[href]"):
        href = (anchor.get("href") or "").strip()
        absolute = downloader.normalize_url_with_lang(urljoin(conference_url, href), "eng")
        path = urlparse(absolute).path
        if not path.startswith(prefix) or "session" in path:
            continue
        title_node = anchor.select_one("p.title")
        description_node = anchor.select_one("p.description")
        if not title_node:
            continue
        metadata[absolute] = {
            "title": title_node.get_text(" ", strip=True),
            "summary": description_node.get_text(" ", strip=True) if description_node else "",
        }
    for item in items:
        extra = metadata.get(item["url"], {})
        if not item.get("title") and extra.get("title"):
            item["title"] = extra["title"]
        item["summary"] = extra.get("summary", "")
    return items


def write_conference_config(conference_urls: list[str], output_root: Path, config_path: Path) -> None:
    entries = []
    for conference_url in conference_urls:
        folder = output_root / conference_slug(conference_url)
        relative_folder = os.path.relpath(folder, config_path.parent).replace("\\", "/")
        entries.append({"url": conference_url, "folder": relative_folder})
    config_path.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _fetch_talk(order: int, item: dict[str, str], retries: int) -> dict:
    downloader = gc_downloader()
    last_error = None
    for _ in range(retries):
        try:
            talk_html = downloader.fetch_html(item["url"])
            talk_state = downloader.extract_initial_state(talk_html)
            title, speaker, role, paragraphs = downloader.extract_talk_from_state(talk_state, item["url"])
            title = title or item.get("title", "") or "Untitled Talk"
            speaker = speaker or item.get("speaker", "") or "unknown_speaker"
            if not paragraphs:
                content_store = talk_state.get("reader", {}).get("contentStore", {})
                for entry in content_store.values():
                    if not isinstance(entry, dict):
                        continue
                    content = entry.get("content", {}) if isinstance(entry.get("content"), dict) else {}
                    head = content.get("head", {}) if isinstance(content.get("head"), dict) else {}
                    social = head.get("page-meta-social", {}) if isinstance(head.get("page-meta-social"), dict) else {}
                    page_meta = social.get("pageMeta", {}) if isinstance(social.get("pageMeta"), dict) else {}
                    description = page_meta.get("description", "")
                    if isinstance(description, str) and description.strip():
                        paragraphs = [description.strip()]
                        break
                    body = content.get("body", "")
                    if isinstance(body, str):
                        video = BeautifulSoup(body, "html.parser").find("video")
                        if video:
                            description = video.get("data-video-description", "").strip()
                            if description:
                                paragraphs = [description]
                                title = video.get("data-video-title", "").strip() or title
                                break
                if not paragraphs:
                    raise ValueError("no paragraphs found")
            return {
                "order": order,
                "speaker": speaker,
                "role": role or "",
                "title": title,
                "paragraphs": paragraphs,
            }
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    raise last_error


def download_conference(conference_url: str, output_dir: Path, workers: int = 4, retries: int = 3, skip_existing: bool = False) -> tuple[int, int]:
    downloader = gc_downloader()
    items = conference_talk_items(conference_url)
    output_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(output_dir.glob("*.txt"))
    if skip_existing and len(existing) == len(items):
        return len(items), len(items)
    for path in existing:
        path.unlink()

    if workers <= 1:
        success_count = 0
        for order, item in enumerate(items, start=1):
            payload = _fetch_talk(order, item, retries)
            dest = output_dir / downloader.build_output_filename(order, payload["speaker"])
            downloader.write_talk_file(dest, payload["speaker"], payload["role"], payload["title"], payload["paragraphs"])
            success_count += 1
        return success_count, len(items)

    success_count = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_fetch_talk, order, item, retries): order
            for order, item in enumerate(items, start=1)
        }
        for future in as_completed(futures):
            order = futures[future]
            payload = future.result()
            dest = output_dir / downloader.build_output_filename(order, payload["speaker"])
            downloader.write_talk_file(dest, payload["speaker"], payload["role"], payload["title"], payload["paragraphs"])
            success_count += 1
    return success_count, len(items)
