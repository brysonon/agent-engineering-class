---
name: byu-speech-transcripts
description: Fetch and extract transcripts from BYU speeches on speeches.byu.edu, then search or quote them accurately. Use this whenever the user mentions BYU speeches, devotionals, forum addresses, speeches.byu.edu URLs, or a named General Authority or BYU speaker's talk — including when they want to find quotes on a theme, build a collection of passages, compare several talks, or pull text for a project. Use it even when the request sounds like ordinary web scraping, because this site has three specific traps (video-only talks, metadata false positives, and navigation junk) that produce confidently wrong results otherwise.
---

# BYU speech transcripts

Pull clean transcript text from `speeches.byu.edu` and work with it honestly.

The site is friendly to scrape — no bot wall, stable URL structure — so the risk
here is not access. The risk is producing a result that looks right and isn't.
Three things cause that, and all three are silent.

## Use the bundled script

```sh
python scripts/fetch_talk.py <url> [<url> ...] [--json] [--out DIR]
```

Standard library only, so there is nothing to install. It fetches over `urllib`
rather than shelling out to `curl`, which matters on Windows: a `curl` command
with flags like `-L --fail --silent` passed through `cmd.exe` can have its flags
interpreted as directory names, and you end up fighting the shell instead of
doing the task.

Exit codes: `0` all talks had transcripts, `2` at least one did not, `1` a real
failure.

## Trap 1: some talks have no transcript at all

This is the one that burns people. BYU publishes certain forum addresses as
video and audio only. The page still exists, still returns HTTP 200, still has
a title, speaker, and date — it just has no talk text. Instead the page says
"The text for this speech is unavailable."

A naive scrape returns a handful of short paragraphs and zero keyword matches,
which is indistinguishable from "this talk never discusses that theme." If you
report `0` without checking, you have told the user something false.

The script detects this and sets `has_transcript: false`. When you hit it, say
so plainly — "BYU publishes this one as video only, so there is no text to
search" — rather than reporting a count. If the user needs that talk's content,
the options are the video or the audio, and that is their call to make.

## Trap 2: page metadata contains topic keywords

Each page embeds JSON-LD structured data listing topics, keywords, and
summaries. Searching the raw HTML for a word like "miracle" will match this
metadata even when the word never appears in the talk. The script strips
`script`/`style` blocks before extracting, so work from its output rather than
grepping the HTML yourself.

## Trap 3: navigation and player text looks like prose

Share buttons, language switchers, and video-player controls ("Speed 0.5x
0.75x 1.0x…") all live in the page body. Paragraphs shorter than 60 characters
are almost always this rather than talk content, which is where the script's
filter comes from. A typical real talk lands between 2,500 and 5,500 words; if
you extract far less than that and the page claims a transcript, something went
wrong and it is worth looking at the HTML before reporting numbers.

## Finding a talk's URL

URLs follow `https://speeches.byu.edu/talks/<speaker-slug>/<talk-slug>/`, with
both slugs lowercased and hyphenated.

The site's own search at `https://speeches.byu.edu/?s=<query>` works for older
talks but does not reliably index recent ones, so a talk from the last few
months can be missing from results even though its page is live. If a search
comes up empty, try constructing the URL directly from the speaker and title,
or use web search scoped to the domain. Confirm the URL returns 200 before
building anything on it.

## Quoting responsibly

These are religious addresses, and people use the quotes in talks, lessons, and
personal study, so attribution is not a formality.

- Quote verbatim. Do not smooth, shorten, or paraphrase inside quotation marks.
- Carry the speaker, talk title, and canonical URL with every quote.
- Keep the surrounding sentence when a passage would otherwise change meaning.
- When searching for a theme, match word stems rather than exact words, since
  most real occurrences are inflected forms: "promis" catches promise,
  promised, promises.

  Cut the stem short enough to survive the inflection. This is easy to get
  wrong: "miracl" looks like the stem for miracle words, but it misses
  *miraculous* and *miraculously*, which are spelled m-i-r-a-c-**u**-l-o-u-s.
  The stem that works is "mirac". Before trusting a stem, write out the forms
  you want and check that each one actually contains it — a stem that silently
  drops half the matches gives you an undercount that looks like a real answer.

## Working at scale

For more than a few talks, write the transcripts to disk with `--out` and
search the files, rather than pulling every transcript into context. Five talks
is roughly 15,000 words; reading them all in costs far more than grepping them
and reading only what matched.

On Windows, set `PYTHONIOENCODING=utf-8` before printing transcript text. These
talks contain curly quotes and em dashes, and the default console encoding
raises `UnicodeEncodeError` on them.
