import re
from html.parser import HTMLParser
from urllib.parse import urljoin

import httpx

from stats_tools import toolbox

CONFERENCE_INDEX_URL = 'https://www.churchofjesuschrist.org/study/general-conference/2026/04?lang=eng'
MAX_CHARS = 30_000

SKIP_TAGS = {'script', 'style', 'noscript', 'svg', 'nav', 'header', 'footer', 'head'}
BLOCK_TAGS = {'p', 'div', 'li', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'tr', 'section', 'article', 'blockquote'}


class _TextExtractor(HTMLParser):
    """Turns HTML into readable text: drops scripts/navigation, keeps sentences on one line."""

    def __init__(self):
        super().__init__()
        self._skip_depth = 0
        self._parts = []

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self._skip_depth += 1
        elif tag in BLOCK_TAGS:
            self._parts.append('\n')

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
        elif tag in BLOCK_TAGS:
            self._parts.append('\n')

    def handle_data(self, data):
        if not self._skip_depth:
            self._parts.append(data)

    def text(self) -> str:
        lines = (re.sub(r'\s+', ' ', line).strip() for line in ''.join(self._parts).split('\n'))
        return '\n'.join(line for line in lines if line)


class _TalkLinkExtractor(HTMLParser):
    """Collects (url, [title, speaker]) for every talk link on a conference index page."""

    def __init__(self, base_url: str):
        super().__init__()
        self._base_url = base_url
        self._current = None
        self.talks = []

    def handle_starttag(self, tag, attrs):
        href = dict(attrs).get('href') or ''
        if tag == 'a' and '/study/general-conference/' in href:
            self._current = (urljoin(self._base_url, href), [])

    def handle_endtag(self, tag):
        if tag == 'a' and self._current:
            if self._current[1]:
                self.talks.append(self._current)
            self._current = None

    def handle_data(self, data):
        if self._current and data.strip():
            self._current[1].append(data.strip())


def _get_html(url: str) -> str:
    response = httpx.get(url, follow_redirects=True, timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
    response.raise_for_status()
    return response.text


@toolbox.tool
def fetch_url(url: str) -> str:
    """Fetch a web page and return its readable text content (HTML and navigation removed)."""
    extractor = _TextExtractor()
    extractor.feed(_get_html(url))
    text = extractor.text()
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + '\n[...truncated]'
    return text


@toolbox.tool
def get_conference_index() -> str:
    """Get the April 2026 General Conference table of contents: every talk's title, speaker, and URL.
    Use this first to find the URL of a speaker's talk."""
    extractor = _TalkLinkExtractor(CONFERENCE_INDEX_URL)
    extractor.feed(_get_html(CONFERENCE_INDEX_URL))
    lines = [' | '.join(parts) + f' | {url}' for url, parts in extractor.talks]
    return 'Title | Speaker | URL\n' + '\n'.join(lines)
