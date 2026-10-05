from weaviate.classes.config import Configure, DataType, Property

from client import get_client

COLLECTION = "Movies"

with get_client() as client:
  if client.collections.exists(COLLECTION):
    print(f"Collection '{COLLECTION}' already exists, skipping.")
  else:
    client.collections.create(
      name=COLLECTION,
      description="A collection of movies",
      properties=[
        Property(name="title", data_type=DataType.TEXT),
        Property(name="overview", data_type=DataType.TEXT),
        Property(name="release_date", data_type=DataType.DATE),
        Property(name="vote_average", data_type=DataType.NUMBER),
        Property(name="vote_count", data_type=DataType.INT),
        Property(name="popularity", data_type=DataType.NUMBER),
        Property(name="genres", data_type=DataType.TEXT_ARRAY),
        Property(name="original_language", data_type=DataType.TEXT, skip_vectorization=True),
        Property(name="original_title", data_type=DataType.TEXT),
        Property(name="poster_path", data_type=DataType.TEXT, skip_vectorization=True),
        Property(name="backdrop_path", data_type=DataType.TEXT, skip_vectorization=True),
        Property(name="genre_ids", data_type=DataType.INT_ARRAY),
        # "id" is reserved in Weaviate, so the TMDB id is stored as tmdb_id
        Property(name="tmdb_id", data_type=DataType.INT),
      ],
      vector_config=Configure.Vectors.text2vec_cohere(
        model="embed-v4.0",
        source_properties=["title", "overview", "genres"],
        # Weaviate Cloud only allows the hfresh index type on this cluster
        vector_index_config=Configure.VectorIndex.hfresh(),
      ),
      generative_config=Configure.Generative.cohere(model="command-a-03-2025"),
    )
    print(f"Created collection '{COLLECTION}'.")
