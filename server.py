import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from client import get_client
from search import MODES, search

PORT = 8000
INDEX_HTML = Path(__file__).parent / "static" / "index.html"

client = get_client()


class Handler(BaseHTTPRequestHandler):
  def do_GET(self):
    url = urlparse(self.path)
    if url.path == "/":
      self._send(200, INDEX_HTML.read_bytes(), "text/html; charset=utf-8")
    elif url.path == "/api/search":
      self._search(parse_qs(url.query))
    else:
      self._json(404, {"error": "Not found"})

  def _search(self, params):
    query = params.get("q", [""])[0].strip()
    mode = params.get("mode", ["hybrid"])[0]
    if not query:
      return self._json(400, {"error": "Enter a search query."})
    if mode not in MODES:
      return self._json(400, {"error": f"Mode must be one of: {', '.join(MODES)}"})
    try:
      results = search(client, query, mode)
    except Exception as e:  # surface Weaviate errors (e.g. no vectorizer) to the UI
      return self._json(502, {"error": f"{type(e).__name__}: {e}"})
    for r in results:
      if r.get("release_date"):
        r["release_date"] = r["release_date"].date().isoformat()
    self._json(200, {"query": query, "mode": mode, "results": results})

  def _json(self, status, payload):
    self._send(status, json.dumps(payload).encode(), "application/json")

  def _send(self, status, body, content_type):
    self.send_response(status)
    self.send_header("Content-Type", content_type)
    self.send_header("Content-Length", str(len(body)))
    self.end_headers()
    self.wfile.write(body)


if __name__ == "__main__":
  server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
  print(f"Movie search running at http://localhost:{PORT}")
  try:
    server.serve_forever()
  except KeyboardInterrupt:
    pass
  finally:
    server.server_close()
    client.close()
