#!/usr/bin/env python3
"""Fetch a BYU speech from speeches.byu.edu and extract its transcript.

Uses only the standard library so it runs anywhere without a pip install, and
fetches over urllib rather than shelling out to curl -- that avoids the shell
quoting and platform differences that make `curl` calls fragile on Windows.

    python fetch_talk.py <url> [<url> ...] [--json] [--out DIR]

Exit codes:
    0  every talk fetched and had a transcript
    2  at least one talk had no published transcript (not an error -- see below)
    1  a genuine failure (network, bad URL)
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from html import unescape
from pathlib import Path

USER_AGENT = 'CS301R-coursework/1.0 (BYU student project; contact via course)'
TIMEOUT = 30

# BYU publishes some forum addresses as video/audio only. The page still exists
# and still has a title and speaker, so a naive scrape returns a near-empty
# transcript and looks like a parser bug. This sentinel is how the site says so.
NO_TRANSCRIPT_MARKER = 'text for this speech is unavailable'

# Below this length a <p> is almost always navigation, a share button, or a
# video-player control rather than a sentence of the talk.
MIN_PARAGRAPH_CHARS = 60


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        charset = response.headers.get_content_charset() or 'utf-8'
        return response.read().decode(charset, errors='replace')


def strip_tags(fragment: str) -> str:
    return ' '.join(unescape(re.sub(r'<[^>]+>', ' ', fragment)).split())


def extract(html: str, url: str) -> dict:
    # Drop script/style first. This matters more than it looks: the page embeds
    # JSON-LD metadata containing topic keywords, so a keyword search over the
    # raw HTML finds words like "miracle" that never appear in the talk itself.
    body = re.sub(r'<(script|style|noscript|svg)\b.*?</\1>', ' ', html, flags=re.S | re.I)

    title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.S | re.I)
    raw_title = strip_tags(title_match.group(1)) if title_match else ''
    # Page titles read "Talk Title | Speaker Name | BYU Speeches".
    parts = [p.strip() for p in raw_title.split('|')]
    title = parts[0] if parts else ''
    speaker = parts[1] if len(parts) > 1 else ''

    if not speaker:
        slug = re.search(r'/talks/([^/]+)/', url)
        if slug:
            speaker = slug.group(1).replace('-', ' ').title()

    paragraphs = [strip_tags(p) for p in re.findall(r'<p[^>]*>(.*?)</p>', body, re.S | re.I)]
    paragraphs = [p for p in paragraphs if len(p) >= MIN_PARAGRAPH_CHARS]

    has_transcript = NO_TRANSCRIPT_MARKER not in strip_tags(body).lower()

    return {
        'url': url,
        'title': title,
        'speaker': speaker,
        'has_transcript': has_transcript,
        'paragraphs': paragraphs if has_transcript else [],
        'word_count': sum(len(p.split()) for p in paragraphs) if has_transcript else 0,
    }


def slug_for(url: str) -> str:
    bits = [b for b in url.split('/') if b]
    return bits[-1] if bits else 'talk'


def main() -> int:
    parser = argparse.ArgumentParser(description='Fetch BYU speech transcripts.')
    parser.add_argument('urls', nargs='+', help='speeches.byu.edu talk URLs')
    parser.add_argument('--json', action='store_true', help='emit JSON instead of text')
    parser.add_argument('--out', type=Path, help='directory to write one file per talk')
    args = parser.parse_args()

    results = []
    missing = False

    for url in args.urls:
        try:
            data = extract(fetch(url), url)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
            print(f'FAILED {url}: {type(exc).__name__}: {exc}', file=sys.stderr)
            return 1

        results.append(data)
        if not data['has_transcript']:
            missing = True
            print(
                f'NO TRANSCRIPT: "{data["title"]}" by {data["speaker"]} is published as '
                f'video/audio only. Report this rather than treating it as zero matches.',
                file=sys.stderr,
            )

        if args.out:
            args.out.mkdir(parents=True, exist_ok=True)
            target = args.out / f'{slug_for(url)}.txt'
            header = f'{data["title"]}\n{data["speaker"]}\n{url}\n\n'
            payload = '\n\n'.join(data['paragraphs']) if data['has_transcript'] else '[no transcript published]'
            target.write_text(header + payload, encoding='utf-8')

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for data in results:
            print(f'=== {data["title"]} | {data["speaker"]}')
            print(f'    {data["url"]}')
            if data['has_transcript']:
                print(f'    {len(data["paragraphs"])} paragraphs, {data["word_count"]} words')
            else:
                print('    no transcript published (video/audio only)')

    return 2 if missing else 0


if __name__ == '__main__':
    sys.exit(main())
