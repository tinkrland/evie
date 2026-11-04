"""import adapters: candidates, never taste. deterministic, offline-testable."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ingest import letterboxd, trakt
from src.ingest.rows import candidate_doc, dedupe, dump_candidates, row

root = Path(__file__).resolve().parents[1]


def write_export(tmp_path, files):
    import csv

    for name, rows in files.items():
        with (tmp_path / name).open("w", newline="") as handle:
            writer = csv.writer(handle)
            for entry in rows:
                writer.writerow(entry)
    return tmp_path


def test_letterboxd_diary_rows_dedupe_to_one_candidate(tmp_path):
    export = write_export(
        tmp_path,
        {
            "watched.csv": [
                ["Date", "Name", "Year", "Letterboxd URI"],
                ["2024-05-03", "The Sting", "1973", "https://boxd.it/1"],
            ],
            "diary.csv": [
                ["Date", "Name", "Year", "Letterboxd URI", "Rating", "Rewatch", "Tags", "Watched Date"],
                ["2024-05-03", "The Sting", "1973", "https://boxd.it/1", "4.5", "No", "", "2024-05-03"],
                ["2024-09-12", "The Sting", "1973", "https://boxd.it/1", "5.0", "Yes", "", "2024-09-12"],
            ],
        },
    )
    doc = letterboxd.collect(export)
    assert doc["summary"]["rows"] == 1
    only = doc["rows"][0]
    assert only["title"] == "The Sting"
    assert only["medium"] == "film"
    assert only["detail"]["views"] == 2, "two diary viewings, not three file appearances"
    assert only["watched_at"] == "2024-05-03"
    assert only["detail"]["last_watched_at"] == "2024-09-12"


def test_letterboxd_tolerates_missing_files(tmp_path):
    export = write_export(
        tmp_path,
        {"ratings.csv": [["Date", "Name", "Year", "Letterboxd URI", "Rating"], ["2024-01-01", "Heat", "1995", "u", "4.0"]]},
    )
    doc = letterboxd.collect(export)
    assert [r["title"] for r in doc["rows"]] == ["Heat"]
    assert doc["rows"][0]["detail"]["views"] == 1


def test_letterboxd_candidates_are_deterministic(tmp_path):
    export = write_export(
        tmp_path,
        {
            "watched.csv": [
                ["Date", "Name", "Year", "Letterboxd URI"],
                ["2024-05-03", "Zulu", "1964", "a"],
                ["2024-05-04", "Alien", "1979", "b"],
            ]
        },
    )
    first = dump_candidates(letterboxd.collect(export))
    second = dump_candidates(letterboxd.collect(export))
    assert first == second
    assert first.index("Alien") < first.index("Zulu"), "sorted by title"


def test_row_shape_is_narrow():
    entry = row("Heat", 1995, medium="film", source="x")
    assert entry["detail"] == {}
    assert entry["source_id"] is None
    assert entry["watched_at"] is None


def test_dedupe_sums_views_and_keeps_dates():
    rows = [
        row("Heat", 1995, "film", "a", watched_at="2020-01-01", detail={"views": 1}),
        row("heat", 1995, "film", "a", watched_at="2021-01-01", detail={"views": 1}),
    ]
    merged = dedupe(rows)
    assert len(merged) == 1
    assert merged[0]["detail"]["views"] == 2
    assert merged[0]["watched_at"] == "2020-01-01"
    assert merged[0]["detail"]["last_watched_at"] == "2021-01-01"


def test_trakt_episodes_roll_up_to_shows_with_counts():
    payload = [
        {"type": "episode", "watched_at": "2024-01-01T00:00:00.000Z",
         "show": {"title": "Slow Horses", "year": 2022, "ids": {"trakt": 1}},
         "episode": {"season": 1, "number": 1}},
        {"type": "episode", "watched_at": "2024-01-08T00:00:00.000Z",
         "show": {"title": "Slow Horses", "year": 2022, "ids": {"trakt": 1}},
         "episode": {"season": 1, "number": 2}},
        {"type": "episode", "watched_at": "2024-02-01T00:00:00.000Z",
         "show": {"title": "Slow Horses", "year": 2022, "ids": {"trakt": 1}},
         "episode": {"season": 2, "number": 1}},
    ]
    rows = trakt.rows_from_history(payload)
    assert len(rows) == 1
    show = rows[0]
    assert show["medium"] == "tv"
    assert show["detail"]["episodes"] == 3
    assert show["detail"]["seasons"] == 2
    assert show["watched_at"] == "2024-01-01T00:00:00.000Z"


def test_trakt_movies_and_shows_coexist():
    payload = [
        {"type": "movie", "watched_at": "2024-01-01T00:00:00.000Z",
         "movie": {"title": "Heat", "year": 1995, "ids": {"trakt": 9}}},
        {"type": "episode", "watched_at": "2024-01-02T00:00:00.000Z",
         "show": {"title": "Monk", "year": 2002, "ids": {"trakt": 2}},
         "episode": {"season": 1, "number": 1}},
    ]
    doc = candidate_doc(trakt.rows_from_history(payload), "trakt")
    assert [r["title"] for r in doc["rows"]] == ["Heat", "Monk"]
    assert doc["rows"][0]["medium"] == "film"
    assert doc["rows"][1]["medium"] == "tv"


def test_trakt_refuses_without_credentials(monkeypatch):
    monkeypatch.delenv("TRAKT_CLIENT_ID", raising=False)
    monkeypatch.delenv("TRAKT_ACCESS_TOKEN", raising=False)
    doc, message = trakt.collect()
    assert doc is None
    assert "TRAKT_CLIENT_ID" in message


def test_trakt_fetch_is_injectable():
    seen = {}

    def fake_http(request):
        seen["url"] = request.full_url
        return [{"type": "movie", "watched_at": "2024-01-01T00:00:00.000Z",
                 "movie": {"title": "Heat", "year": 1995, "ids": {"trakt": 9}}}]

    doc, message = trakt.collect(client_id="cid", token="tok", http=fake_http)
    assert message is None
    assert "/sync/history" in seen["url"]
    assert doc["summary"]["rows"] == 1


def test_candidates_never_write_a_taste_context(tmp_path):
    export = write_export(
        tmp_path,
        {"watched.csv": [["Date", "Name", "Year", "Letterboxd URI"], ["2024-01-01", "Heat", "1995", "a"]]},
    )
    doc = letterboxd.collect(export)
    assert doc["kind"] == "import-candidates"
    dumped = dump_candidates(doc)
    assert "liked:" not in dumped
    assert "taste context" in dumped
