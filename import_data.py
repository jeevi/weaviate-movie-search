import ast
import json
from datetime import datetime, timezone
from urllib.request import urlopen

from weaviate.util import generate_uuid5

from client import get_client

DATA_URL = "https://raw.githubusercontent.com/weaviate-tutorials/edu-datasets/main/movies_data_1990_2024.json"

# TMDB genre ids -> names
GENRES = {
  12: "Adventure", 14: "Fantasy", 16: "Animation", 18: "Drama", 27: "Horror",
  28: "Action", 35: "Comedy", 36: "History", 37: "Western", 53: "Thriller",
  80: "Crime", 99: "Documentary", 878: "Science Fiction", 9648: "Mystery",
  10402: "Music", 10749: "Romance", 10751: "Family", 10752: "War", 10770: "TV Movie",
}


def load_movies():
  with urlopen(DATA_URL) as resp:
    columns = json.load(resp)
  for i in columns["id"]:
    yield {col: values[i] for col, values in columns.items()}


with get_client() as client:
  if not client.collections.exists("Movies"):
    raise SystemExit("Collection 'Movies' not found. Run create_collection.py first.")
  movies = client.collections.use("Movies")
  count = 0

  with movies.batch.fixed_size(batch_size=100) as batch:
    for row in load_movies():
      genre_ids = [int(g) for g in ast.literal_eval(row["genre_ids"])]
      release_date = datetime.strptime(row["release_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
      movie = {
        "title": row["title"],
        "overview": row["overview"],
        "release_date": release_date,
        "vote_average": float(row["vote_average"]),
        "vote_count": int(row["vote_count"]),
        "popularity": float(row["popularity"]),
        "genres": [GENRES.get(g, "Unknown") for g in genre_ids],
        "original_language": row["original_language"],
        "original_title": row["original_title"],
        "poster_path": row["poster_path"],
        "backdrop_path": row["backdrop_path"],
        "genre_ids": genre_ids,
        "tmdb_id": int(row["id"]),
      }
      batch.add_object(properties=movie, uuid=generate_uuid5(row["id"]))
      count += 1

  failed = movies.batch.failed_objects
  print(f"Imported {count - len(failed)}/{count} movies.")
  for obj in failed[:10]:
    print(obj.original_uuid, obj.message)
