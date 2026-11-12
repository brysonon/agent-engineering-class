# Semantic Search Across Church and BYU Texts

This project evaluates semantic retrieval for personal gospel study across three source types: the standard works, the general conference archive from 1971 through October 2026, and selected BYU speeches. It is intentionally a search system rather than a free-form answer generator. The goal is to return relevant passages, similarity scores, and source links so the user can inspect the evidence directly.

## Highlights

- Searches **41,995 scripture verses**, **4,305 general conference talks**, and selected **BYU speeches**
- Uses one embedding model and a shared indexing pipeline across all corpora
- Compares **vector**, **keyword**, and **hybrid** retrieval on a labeled question set
- Returns source-aware results with canonical links back to the original text

## Data included in this version

- **Scriptures:** 41,995 verses from all five standard works. The project reuses the `hw2d/cache-verse` embeddings and text already created for class, so these verses do not need to be embedded again.
- **General conference:** 112 conferences from **April 1971 through October 2026**, downloaded into `conference_talks/` and listed in `conferences.json`. The importer validates talk order against the official conference pages, keeps one-line summaries when available, and now handles edge cases like video-only pages and duplicate talk titles across years.
- **BYU Speeches:** four published transcripts listed in `speeches.txt`. Add more BYU Speeches URLs to that file and rebuild. Speeches without published text are skipped.

Talks and speeches are split into overlapping passages of about 180 words. All three sources use OpenAI `text-embedding-3-small`, and search compares normalized vectors with cosine similarity. The generated indexes stay in `data/`, which Git ignores.

## Run locally

From `CS 301R/final project` in PowerShell:

```powershell
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\.venv\Scripts\python.exe import_conferences.py --skip-existing
..\.venv\Scripts\python.exe build_index.py
..\.venv\Scripts\python.exe search.py "God knew me before I was born"
..\.venv\Scripts\python.exe search.py "God knew me before I was born" --per-source --limit 2
..\.venv\Scripts\python.exe search.py "grace helps us change" --source byu
..\.venv\Scripts\python.exe search.py "temple covenants" --source conference --limit 10
..\.venv\Scripts\python.exe search.py --stats
..\.venv\Scripts\python.exe evaluate.py
..\.venv\Scripts\python.exe evaluate.py --gold-source conference --show-misses 8
..\.venv\Scripts\python.exe evaluate.py --json
```

The OpenAI key is read from the course root `.env` as `OPENAI_API_KEY`. Building the conference and BYU indexes makes embedding API calls; each search embeds only the query. The existing scripture index was built with the same model. By default, results rank together across sources. Use `--per-source` to see the strongest matches from each collection, or `--json` for structured results.

## Evaluation

`evaluate.py` measures retrieval quality on a gold question set stored in `eval_questions_church.json`. The evaluator reports `hit@k` and `MRR`, comparing four retrieval views:

- `vector`: the default cross-source semantic search behavior
- `vector-per-source`: semantic search restricted to the gold source
- `keyword`: a BM25-style lexical baseline over the same indexed passages
- `hybrid`: a simple reciprocal-rank fusion of vector and keyword results

Useful options:

- `--gold-source scripture` or `--gold-source conference` to score one subset
- `--tag faith` or other repeated `--tag` filters to focus on a topic
- `--show-misses 10` to print hard failures for manual review
- `--question-limit 5` for a quick smoke test while iterating

To add speeches, put one `https://speeches.byu.edu/talks/.../` URL per line in `speeches.txt` and run `build_index.py --source byu`. To refresh conference data, run `import_conferences.py --skip-existing` for the full archive or pass `--start-year` and `--end-year` for a smaller range, then run `build_index.py --source conference`. Folder paths in `conferences.json` are relative to that file.

The BYU list stays small enough to verify by hand. The project keeps the scope at retrieval so results remain inspectable and grounded in the linked source text.
