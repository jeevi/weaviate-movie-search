import os

import weaviate
from weaviate.classes.init import AdditionalConfig, Timeout


def get_client():
  """Return a connected Weaviate client. Caller must close it.

  Set WEAVIATE_LOCAL=1 to use a local instance (localhost:8080 / gRPC 50051);
  otherwise connects to Weaviate Cloud using WEAVIATE_URL and WEAVIATE_API_KEY.
  """
  headers = {"X-Cohere-Api-Key": os.environ["COHERE_APIKEY"]}

  if os.environ.get("WEAVIATE_LOCAL") == "1":
    # Long query timeout so requests survive sitting at a debugger breakpoint
    # (the client default is 30s).
    return weaviate.connect_to_local(
      headers=headers,
      additional_config=AdditionalConfig(timeout=Timeout(query=600)),
    )

  return weaviate.connect_to_weaviate_cloud(
    cluster_url=os.environ["WEAVIATE_URL"],
    auth_credentials=os.environ["WEAVIATE_API_KEY"],
    headers=headers,
  )
