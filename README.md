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

In **Hybrid** mode an **Alpha** slider sets the balance between keyword (0) and semantic (1) scoring. **Released after** limits results to movies released after the chosen date, in any mode.

### Command line

```bash
.venv/bin/python search.py semantic "lonely robot finds love"
.venv/bin/python search.py keyword dinosaur
```

The mode is optional and defaults to `hybrid`.

### API

```
GET /api/search?q=<query>&mode=<keyword|hybrid|semantic>&alpha=<0..1>&release_date=<YYYY-MM-DD>
```

`alpha` (default `0.5`) only affects hybrid search. `release_date` is optional and keeps movies released strictly after that date. Invalid values return `400`.

Returns `{"query", "mode", "alpha", "release_date", "results": [...]}`. Each result includes `title`, `overview`, `release_date`, `vote_average`, `genres`, `poster_path`, `tmdb_id` and `score`. Higher scores are better in every mode (semantic distances are converted to similarity).

## Running against a local Weaviate

Set `WEAVIATE_LOCAL=1` to connect to `localhost:8080` (gRPC `50051`) instead of Weaviate Cloud. Only `COHERE_APIKEY` is needed. Locally the collection uses the `hnsw` index and queries get a 10-minute timeout so they survive debugger breakpoints.

```bash
docker compose up -d                                   # Weaviate 1.39 in Docker
WEAVIATE_LOCAL=1 .venv/bin/python create_collection.py
WEAVIATE_LOCAL=1 .venv/bin/python import_data.py
WEAVIATE_LOCAL=1 .venv/bin/python server.py
```

To debug Weaviate itself, stop the container (`docker compose stop`) and run `./run_weaviate_debug.sh`. It builds Weaviate from a source checkout (`$WEAVIATE_SRC`, default `~/workspace/weaviate`) and runs it under a headless Delve debugger. Attach with `dlv connect 127.0.0.1:2345`, and leave with `quit -c` so Weaviate keeps running. Data is stored in `.weaviate-debug-data/`.

## Project layout

| File | Purpose |
|---|---|
| `client.py` | `get_client()` – connects to Weaviate Cloud, or a local instance when `WEAVIATE_LOCAL=1` |
| `docker-compose.yml` | Single-node local Weaviate |
| `run_weaviate_debug.sh` | Runs Weaviate from source under Delve |
| `create_collection.py` | Creates the `Movies` collection (Cohere vectorizer + generative config) if it doesn't exist |
| `import_data.py` | Downloads the dataset and batch-imports it |
| `search.py` | `search(client, query, mode, alpha=, release_date=)` and a small CLI |
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
