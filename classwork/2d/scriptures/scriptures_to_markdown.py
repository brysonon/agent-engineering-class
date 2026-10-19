#!/usr/bin/env python3
"""Render the scripture directory tree as Markdown.

Usage:
    python scriptures_to_markdown.py PATH

PATH may be the scripture root, a work directory, a book directory, or a
chapter text file. Output is written to stdout.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def chapter_files(book: Path) -> list[Path]:
    """Return the text files directly inside a book directory."""
    return sorted(
        (path for path in book.iterdir() if path.is_file() and path.suffix == ".txt"),
        key=lambda path: path.name,
    )


def render_chapter(chapter: Path) -> list[str]:
    lines = [f"### {chapter.stem}", ""]
    with chapter.open(encoding="utf-8") as source:
        verses = [line.strip() for line in source if line.strip()]

    lines.extend(f"{number}. {verse}" for number, verse in enumerate(verses, start=1))
    lines.append("")
    return lines


def render_book(work: Path, book: Path, chapters: list[Path], *, include_work: bool = True) -> list[str]:
    lines = [f"# {work.name}", ""] if include_work else []
    lines.extend([f"## {book.name}", ""])
    for chapter in chapters:
        lines.extend(render_chapter(chapter))
    return lines


def render_work(work: Path) -> list[str]:
    lines = [f"# {work.name}", ""]
    for book in sorted((path for path in work.iterdir() if path.is_dir()), key=lambda p: p.name):
        chapters = chapter_files(book)
        if chapters:
            lines.extend(render_book(work, book, chapters, include_work=False))
    return lines


def render_root(root: Path) -> list[str]:
    lines: list[str] = []
    for work in sorted((path for path in root.iterdir() if path.is_dir()), key=lambda p: p.name):
        lines.extend(render_work(work))
    return lines


def render_target(target: Path) -> list[str]:
    if target.is_file():
        book = target.parent
        work = book.parent
        return render_book(work, book, [target])

    chapters = chapter_files(target)
    if chapters:
        # A directory containing chapter files is a book directory.
        return render_book(target.parent, target, chapters)

    child_dirs = sorted((path for path in target.iterdir() if path.is_dir()), key=lambda p: p.name)
    if any(chapter_files(book) for book in child_dirs):
        # A directory containing book directories is a work directory.
        return render_work(target)

    # Otherwise treat it as the scripture root.
    return render_root(target)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render scripture files as Markdown.")
    parser.add_argument("target", type=Path, help="root, work, book, or chapter file to render")
    args = parser.parse_args()

    target = args.target.expanduser()
    if not target.exists():
        parser.error(f"target does not exist: {target}")

    try:
        output = render_target(target)
    except (OSError, UnicodeError) as error:
        parser.error(str(error))

    try:
        sys.stdout.write("\n".join(output).rstrip() + "\n" if output else "")
    except BrokenPipeError:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
