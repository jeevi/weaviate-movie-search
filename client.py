import os

import weaviate


def get_client():
  """Return a connected Weaviate Cloud client. Caller must close it."""
  return weaviate.connect_to_weaviate_cloud(
    cluster_url=os.environ["WEAVIATE_URL"],
    auth_credentials=os.environ["WEAVIATE_API_KEY"],
    headers={"X-Cohere-Api-Key": os.environ["COHERE_APIKEY"]},
  )
