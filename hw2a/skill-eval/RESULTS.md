# Skill eval: byu-speech-transcripts (iteration 1)

Task given to both runs, identically:

> For each of these three BYU speeches, report how many paragraphs of the talk
> mention miracles. Match the word stem "miracl" so it catches miracle,
> miracles, and miraculous.
> (Wilcox / His Grace Is Sufficient, Jenkins / Five Loaves and Two Fishes,
> Kearon / Peace and Rest—Even Now)

## Correctness

| Talk | With skill | Without skill | Truth |
|---|---|---|---|
| Wilcox | 2 paragraphs | 2 paragraphs | 2 |
| Jenkins | no transcript published | no transcript published | no transcript published |
| Kearon | 0 | 0 | 0 |

Both runs were correct. Both avoided the trap of reporting Jenkins as "0".

## Cost

| | With skill | Without skill | Difference |
|---|---|---|---|
| Tokens | 39,946 | 57,042 | baseline used 43% more |
| Tool calls | 9 | 21 | baseline used 2.3x |
| Wall time | 53.8s | 237.2s | baseline took 4.4x |

## The finding that matters

The skill did not improve correctness. It improved efficiency substantially,
and it introduced an error.

The skill's own text claimed the stem "miracl" catches "miraculous". It does
not -- that word is spelled m-i-r-a-c-u-l-o-u-s, so it contains no "miracl".
The correct stem is "mirac". The with-skill run inherited this claim and
repeated it. The baseline, having nothing to trust, worked the matching out
from scratch and caught the error, flagging that Wilcox contains one
"miraculously" the specified pattern misses.

Fixed in iteration 2 of SKILL.md.
