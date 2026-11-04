"""trakt import: api, oauth.

history is episodes and films with timestamps. episodes roll up to shows
with the episode count kept visible: a show is a candidate when the
history backs it, and one episode is a sample, not a series commitment.

the network call is a thin function and the shaping is pure, so the
adapter is testable without a token and without the network.
"""

import json
import os
import urllib.parse
import urllib.request

from src.ingest.rows import row

source = "trakt"
api_base = "https://api.trakt.tv"


def _headers(client_id, token):
    return {
        "Content-Type": "application/json",
        "trakt-api-version": "2",
        "trakt-api-key": client_id,
        "Authorization": f"Bearer {token}",
    }


def fetch_history(client_id, token, limit=1000, http=None):
    """GET /sync/history. injectable `http` for tests, urllib by default."""
    url = f"{api_base}/sync/history?{urllib.parse.urlencode({'limit': limit, 'extended': 'full'})}"

    def default_http(request):
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    caller = http or default_http
    request = urllib.request.Request(url, headers=_headers(client_id, token))
    return caller(request)


def rows_from_history(payload):
    """shape one /sync/history payload into candidate rows. pure."""
    out = []
    shows = {}
    for entry in payload or []:
        kind = entry.get("type")
        when = entry.get("watched_at")
        if kind == "movie":
            movie = entry.get("movie") or {}
            out.append(
                row(
                    movie.get("title") or "",
                    movie.get("year"),
                    medium="film",
                    source=source,
                    source_id=(movie.get("ids") or {}).get("trakt"),
                    watched_at=when,
                )
            )
        elif kind == "episode":
            show = entry.get("show") or {}
            episode = entry.get("episode") or {}
            key = str((show.get("ids") or {}).get("trakt") or show.get("title") or "").lower()
            slot = shows.setdefault(
                key,
                {
                    "title": show.get("title") or "",
                    "year": show.get("year"),
                    "source_id": (show.get("ids") or {}).get("trakt"),
                    "episodes": 0,
                    "seasons": set(),
                    "first": when,
                    "last": when,
                },
            )
            slot["episodes"] += 1
            if episode.get("season") is not None:
                slot["seasons"].add(episode["season"])
            if when:
                slot["first"] = min(filter(None, [slot["first"], when]))
                slot["last"] = max(filter(None, [slot["last"], when]))
    for slot in shows.values():
        out.append(
            row(
                slot["title"],
                slot["year"],
                medium="tv",
                source=source,
                source_id=slot["source_id"],
                watched_at=slot["first"],
                detail={
                    "episodes": slot["episodes"],
                    "seasons": len(slot["seasons"]),
                    "last_watched_at": slot["last"],
                },
            )
        )
    return [entry for entry in out if entry["title"]]


def collect(client_id=None, token=None, http=None):
    """candidate doc from trakt history. raises nothing on missing env.

    returns (doc or None, message) so the cli can report honestly instead
    of pretending an import happened.
    """
    from src.ingest.rows import candidate_doc

    client_id = client_id or os.environ.get("TRAKT_CLIENT_ID")
    token = token or os.environ.get("TRAKT_ACCESS_TOKEN")
    if not client_id or not token:
        return None, "trakt import needs TRAKT_CLIENT_ID and TRAKT_ACCESS_TOKEN in the environment"
    payload = fetch_history(client_id, token, http=http)
    return candidate_doc(rows_from_history(payload), source), None
