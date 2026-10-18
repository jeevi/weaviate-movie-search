import sys
from datetime import datetime, timezone

from weaviate.classes.query import Filter, MetadataQuery

from client import get_client

RETURN_PROPERTIES = [
  "title", "overview", "release_date", "vote_average", "genres", "poster_path", "tmdb_id",
]
MODES = ("keyword", "hybrid", "semantic")


def search(client, query_text, mode="hybrid", limit=10, alpha=0.5, release_date=None):
  """Search movies by keyword (BM25), semantic (vector) or hybrid (both)."""
  movies = client.collections.use("Movies")
  common = dict(limit=limit, return_properties=RETURN_PROPERTIES)

  if release_date:
    filters = Filter.by_property("release_date").greater_than(datetime.strptime(release_date, "%Y-%m-%d").replace(tzinfo=timezone.utc))
  else:
    filters = None
  if mode == "keyword":
    response = movies.query.bm25(query=query_text, return_metadata=MetadataQuery(score=True), filters=filters, **common)
  elif mode == "semantic":
    response = movies.query.near_text(query=query_text, return_metadata=MetadataQuery(distance=True), filters=filters, **common)
  elif mode == "hybrid":
    response = movies.query.hybrid(query=query_text, return_metadata=MetadataQuery(score=True), alpha=alpha, filters=filters, **common)
  else:
    raise ValueError(f"Unknown mode '{mode}', expected one of {MODES}")

  results = []
  for obj in response.objects:
    m = obj.metadata
    # Semantic search returns a distance (lower is better); convert to similarity
    score = 1 - m.distance if m.distance is not None else m.score
    results.append({**obj.properties, "score": score})
  return results


if __name__ == "__main__":
  mode = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in MODES else "hybrid"
  query = " ".join(a for a in sys.argv[1:] if a != mode) or "a heartwarming story about friendship"
  with get_client() as client:
    for m in search(client, query, mode):
      year = m["release_date"].year if m.get("release_date") else "?"
      print(f"{m['score']:.3f}  {m['title']} ({year}) - {', '.join(m['genres'])}")
