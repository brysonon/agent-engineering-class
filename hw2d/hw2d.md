# HW2d Write-up

## How I completed the required tasks
- I embedded the whole standard works and then searched it. I wrote two scripts: `embed_corpus.py` embeds every verse once and saves it to disk, and `search.py` runs queries against that saved copy so I only pay to embed the query.
    * 41,995 verses, about 1.2 million words. It took 148 seconds and cost about 3 cents with `text-embedding-3-small`.
- I picked foreordination and premortal life as my topic on purpose, because it is spread across all five volumes and the scriptures almost never use the words I would search for.
    * "foreordain" shows up in 1 verse. "premortal" shows up in 0. "first estate" in 3, "noble and great" in 2.
    * The passages that actually teach it are Jeremiah 1:5, Job 38:7, Ephesians 1:4, Alma 13:3, Abraham 3:22-23, and D&C 138:55. Six different vocabularies, almost no shared words.
- I also embedded the same scriptures at the chapter level so I could compare chunk sizes.

## Additional exploration
- **Similar meaning, different wording.** Asking "God knew me before I came to earth" put Jeremiah 1:5 at the very top, which is exactly right since that verse never says foreordination. But the same query also pulled up Alma 36:5 ("if I had not been born of God"), which is about conversion, and Genesis 45:7 ("God sent me before you"), which is Joseph being sent to Egypt. Both only matched on the surface.
- **Where each known passage ranked for each query.** Low number means it was found easily, out of 41,995 verses.

  | Passage | "existed before I was born" | "God knew me before" | "chosen beforehand" | "foreordination and premortal existence" |
  | --- | --- | --- | --- | --- |
  | Jeremiah 1:5 | 8 | **1** | 157 | 36 |
  | Alma 13:3 | 6741 | 612 | **3** | 7 |
  | Ephesians 1:4 | 1733 | 63 | **28** | 617 |
  | Abraham 3:23 | 136 | **12** | 22 | 304 |
  | D&C 138:55 | 890 | 3502 | **33** | 2597 |
  | Job 38:7 | 6797 | 5250 | 30428 | 6191 |

    * No single query found the doctrine. Every passage had a different query that worked for it, and the query that found one buried another. Jeremiah 1:5 was 1st for one phrasing and 836th for another.
    * Job 38:7 was never found. Its best rank was 5,250 out of 41,995. "The morning stars sang together, and all the sons of God shouted for joy" does not describe the doctrine, it pictures it, so you have to already know what it means.
    * Using the actual doctrinal words did worse than plain English. "Foreordination and the premortal existence" put Ephesians at 617 and D&C 138 at 2597, while simpler phrasings found both much faster.
- **Similar and dissimilar pairs, measured.** Same doctrine scored higher than shared words, but not by as much as I expected.

  | Pair | Score | |
  | --- | --- | --- |
  | Ephesians 1:4 ↔ Alma 13:3 | 0.600 | same doctrine, both say "foundation of the world" |
  | Jeremiah 1:5 ↔ Abraham 3:23 | 0.521 | same doctrine, no shared wording |
  | Jeremiah 1:5 ↔ Alma 13:3 | 0.519 | same doctrine, different volumes |
  | Abraham 3:23 ↔ Genesis 1:1 | 0.384 | both about creation, different doctrine |
  | Jeremiah 1:5 ↔ Genesis 5:3 | 0.365 | both about being born, different doctrine |

- **Documents retrieved that should not have been.** Searching "foundation of the world" gave me 10 results and not one was about foreordination. They were all about God laying the foundations of the earth, like Psalms 104:5 and Job 38:4. The phrase appears in 45 verses but mostly means the physical creation.
- **The effect of text size.** I ran the same queries against verses and against whole chapters.

  | | verse level | chapter level |
  | --- | --- | --- |
  | Units | 41,995 | 1,582 |
  | Cache size | 258 MB | 10 MB |
  | Time to embed | 148s | 10s |
  | Mean top score | 0.531 | 0.407 |

    * Chapter level scored much lower on everything. Averaging 750 words together waters the signal down, so nothing looks like a strong match.
    * But chapter level was sometimes more right. For "God knew me before I came to earth" it returned Abraham 3 first, which is the actual foreordination chapter. Verse level returned four verses that sounded similar and only one that was on topic.
    * It also failed harder when it failed. For "chosen beforehand for a purpose" it gave me D&C 55 and D&C 78, which are chapters about calling missionaries. Verse level found Alma 13:3.
    * So neither one is better. Verses are precise but match on phrasing, and chapters are vaguer but sometimes catch the topic. If I built this for real I would search verses and show the surrounding chapter for context.

## Obstacles I encountered
- **Hit the token limit:** Batching 500 chapters in one request asked for 597,139 tokens against a 300,000 cap. Verses are short so a fixed batch size worked fine, but chapters are 750 words each. I had to change the batching to count tokens instead of items.
- **The cache is big:** 41,995 verses at 1,536 dimensions came out to 258 MB. That is fine on my laptop but it made me realize why real systems use a vector database instead of a numpy file.
- **Telling a real match from a surface match:** Looking at a results list, a verse that sounds similar and a verse that means the same thing look identical. I only caught the bad ones because I already knew the doctrine. That is the part I do not have a good answer for.

## What I learned
- I learned that embeddings match how something is said more than what it means. Job 3:16 came back for "I existed before I was born" because Job is talking about never having been born, which is close to the opposite of what I was asking.
- I learned that there is no single good query. I thought I would find one phrasing that pulled the whole doctrine together and there was not one. Each passage needed its own wording.
- I learned that the right vocabulary can hurt. Searching the actual doctrinal term did worse than describing the idea in plain words, probably because the scriptures never use that term.
- I learned that chunk size is a real tradeoff and not just a performance setting. Small chunks are sharp but shallow, big chunks are blurry but hold context, and neither one wins.
- I learned that a verse that teaches a doctrine through a picture instead of a statement is close to invisible to search. Job 38:7 is one of the clearest premortal passages and I could not get it to show up at all.

## Why this matters in the context of agent engineering
Any agent that answers questions from documents is doing what I just did, so the quality of its answers is capped by whether retrieval found the right material. My searches looked successful every time. I always got ten verses back with decent scores, and most of them were wrong. An agent would have written a confident answer on top of those.

Chunk size is a design decision I would have treated as a setting before this. Verse level and chapter level gave genuinely different answers to the same question, and I could not pick a winner. That means the chunking choice is part of what the system believes, not just how fast it runs.

The failure I care about most is Job 38:7, because nothing in the output told me it was missing. A missed document leaves no trace. I only knew to look for it because I already knew it should be there, and an agent searching a corpus it has never seen has no way to notice what it did not find.

## How many hours I spent
