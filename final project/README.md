# Final project: semantic search across Church and BYU texts

Search the scriptures, October 2026 general conference, and selected BYU Speeches with one embedding model. Results show the matching passage, a cosine similarity score, and a link to the original source. This is retrieval only; it does not generate an answer or claim that the highest score is doctrinally correct.

## Data included in this first version

- **Scriptures:** 41,995 verses from all five standard works. The project reuses the `hw2d/cache-verse` embeddings and text already created for class, so these verses do not need to be embedded again.
- **General conference:** the 38 local text files in `hw2e/talks`, corresponding to October 2026. The builder checks their order and titles against the [official conference index](https://www.churchofjesuschrist.org/study/general-conference/2026/10?lang=eng) so each result gets the right source URL. More conference folders can be added in `conferences.json`.
- **BYU Speeches:** four published transcripts listed in `speeches.txt`. Add more BYU Speeches URLs to that file and rebuild. Speeches without published text are skipped; [BYU explains why some transcripts are unavailable](https://speeches.byu.edu/faq/).

Talks and speeches are split into overlapping passages of about 180 words. All three sources use OpenAI `text-embedding-3-small`, and search compares normalized vectors with cosine similarity. The generated indexes stay in `data/`, which Git ignores. Do not commit the downloaded text or generated index if you plan to share this repository publicly without checking the source publishers' permissions.

## Run it

From `CS 301R/final project` in PowerShell:

```powershell
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\.venv\Scripts\python.exe build_index.py
..\.venv\Scripts\python.exe search.py "God knew me before I was born"
..\.venv\Scripts\python.exe search.py "God knew me before I was born" --per-source --limit 2
..\.venv\Scripts\python.exe search.py "grace helps us change" --source byu
..\.venv\Scripts\python.exe search.py "temple covenants" --source conference --limit 10
..\.venv\Scripts\python.exe search.py --stats
```

The OpenAI key is read from the course root `.env` as `OPENAI_API_KEY`. Building the conference and BYU indexes makes embedding API calls; each search embeds only the query. The existing scripture index was built with the same model. By default, results rank together across sources. Use `--per-source` to see the strongest matches from each collection, or `--json` for structured results for an app or evaluation script.

To add speeches, put one `https://speeches.byu.edu/talks/.../` URL per line in `speeches.txt` and run `build_index.py --source byu`. To add a conference, use the existing `classwork/2e/download_gc_talks.py` downloader to save its talks to a folder, add that folder and its official conference index URL to `conferences.json`, then run `build_index.py --source conference`. Folder paths in `conferences.json` are relative to that file. Matching conference folders and URLs are required so citations remain correct.

The initial BYU list is deliberately small enough to verify by hand. Expanding to the full BYU archive or many decades of conference talks would need a source inventory, incremental indexing, and retrieval evaluation. Embeddings can miss passages that express an idea indirectly, as the `hw2d` experiments showed, so inspect the linked source before relying on a result.
