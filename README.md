# Movie Search

A small movie search app backed by [Weaviate Cloud](https://weaviate.io/). It indexes ~680 movies (1990–2024) and lets you search them three ways from a simple web page:

- **Keyword** – BM25 matching on the exact words in titles, overviews and genres.
- **Semantic** – vector search using Cohere embeddings, so results match on meaning even without shared words.
- **Hybrid** – a blend of keyword and semantic scores.

The backend uses only the Python standard library plus `weaviate-client`.

## Requirements

- Python 3.10+ (the current `weaviate-client` does not support 3.9)
- A Weaviate Cloud cluster and an **Admin** API key
- A Cohere API key (used by Weaviate to embed movies and queries)

## Setup

1. **Create a virtual environment and install dependencies**

   ```bash
   uv venv --python 3.12 .venv
   uv pip install --python .venv/bin/python -r requirements.txt
   ```

   Or without `uv`:

   ```bash
   python3.12 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```

2. **Set environment variables** (e.g. in `~/.zshrc`, then `source ~/.zshrc`)

   ```bash
   export WEAVIATE_URL="your-cluster.weaviate.cloud"   # REST endpoint, no https://
   export WEAVIATE_API_KEY="..."                         # Admin key for that cluster
   export COHERE_APIKEY="..."
   ```

3. **Create the collection** (run once)

   ```bash
   .venv/bin/python create_collection.py
   ```

4. **Import the movies**

   ```bash
   .venv/bin/python import_data.py
   ```

   This downloads the dataset and embeds every movie with Cohere, so it uses some Cohere quota. Re-running it is safe: objects use deterministic UUIDs and are overwritten rather than duplicated.

## Usage

### Web UI

```bash
.venv/bin/python server.py
```

Open <http://localhost:8000>, type a query, and pick **Keyword**, **Hybrid** or **Semantic**. Switching modes re-runs the current search so you can compare results.

### Command line

```bash
.venv/bin/python search.py semantic "lonely robot finds love"
.venv/bin/python search.py keyword dinosaur
```

The mode is optional and defaults to `hybrid`.

### API

```
GET /api/search?q=<query>&mode=<keyword|hybrid|semantic>
```

Returns `{"query", "mode", "results": [...]}`. Each result includes `title`, `overview`, `release_date`, `vote_average`, `genres`, `poster_path`, `tmdb_id` and `score`. Higher scores are better in every mode (semantic distances are converted to similarity).

## Project layout

| File | Purpose |
|---|---|
| `client.py` | `get_client()` – connects to Weaviate Cloud using the env vars above |
| `create_collection.py` | Creates the `Movies` collection (Cohere vectorizer + generative config) if it doesn't exist |
| `import_data.py` | Downloads the dataset and batch-imports it |
| `search.py` | `search(client, query, mode)` and a small CLI |
| `server.py` | Standard-library HTTP server for the UI and `/api/search` |
| `static/index.html` | The search page |
| `test.py` | Prints the installed `weaviate-client` version |

## Troubleshooting

- **`401 ... invalid api key`** – the key doesn't belong to the cluster in `WEAVIATE_URL`, or your shell has a stale value. Run `source ~/.zshrc` (or open a new terminal) and test directly:

  ```bash
  curl -s -o /dev/null -w "%{http_code}\n" -H "Authorization: Bearer $WEAVIATE_API_KEY" "https://$WEAVIATE_URL/v1/meta"
  ```

  `200` means the key works; `401` means create a new Admin key for that cluster.

- **`hnsw is not allowed for vector_index_type`** – your `weaviate-client` is too old for the cluster. Upgrade it (requires Python 3.10+).

- **`could not vectorize input ... Make sure a vectorizer module is configured`** – the `Movies` collection was created without a vectorizer (for example by importing before running `create_collection.py`). Delete the collection, then run steps 3 and 4 again.

## Data

Movie data comes from Weaviate's [edu-datasets](https://github.com/weaviate-tutorials/edu-datasets) (sourced from TMDB). Posters are loaded from `image.tmdb.org`.
