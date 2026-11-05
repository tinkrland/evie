"""the storygraph adapter: read status decides, moods stay foreign.

the rules under test are the ones that keep this import honest:
read-only candidates, did-not-finish counted but never promoted,
isbn as the only hard identity, and the user's own tags untouched.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ingest import storygraph

fixtures = Path(__file__).resolve().parent / "fixtures" / "storygraph"


def test_only_read_rows_become_candidates():
    doc = storygraph.collect(fixtures)
    titles = {row["title"] for row in doc["rows"]}
    assert titles == {"Piranesi", "The Remains of the Day", "A Book With No Isbn"}
    assert "Ulysses" not in titles
    assert "The Pale King" not in titles
    assert "Finnegans Wake" not in titles


def test_did_not_finish_is_reported_not_promoted():
    doc = storygraph.collect(fixtures)
    assert doc["summary"]["excluded_by_status"]["did-not-finish"] == 1
    assert all(row["title"] != "Finnegans Wake" for row in doc["rows"])


def test_isbn_is_the_hard_identity_and_uid_is_not():
    doc = storygraph.collect(fixtures)
    by_title = {row["title"]: row for row in doc["rows"]}
    assert by_title["Piranesi"]["source_id"] == "9781635575637"
    # a storygraph uid is not an isbn: it stays detail, source_id stays absent
    assert by_title["A Book With No Isbn"]["source_id"] is None
    assert by_title["A Book With No Isbn"]["detail"]["storygraph_uid"] == "uid-9931"


def test_editions_collapse_by_isbn():
    doc = storygraph.collect(fixtures)
    piranesi = next(row for row in doc["rows"] if row["title"] == "Piranesi")
    assert piranesi["detail"]["views"] == 2
    assert piranesi["detail"]["last_watched_at"] == "2024/07/19"


def test_tags_are_detail_never_axes():
    doc = storygraph.collect(fixtures)
    piranesi = next(row for row in doc["rows"] if row["title"] == "Piranesi")
    assert piranesi["detail"]["tags"] == "fiction, speculative"
    # nothing in a candidate row is an evie axis value
    assert "genre_tradition" not in piranesi
    assert "mood" not in piranesi


def test_tags_csv_is_not_mistaken_for_the_library():
    assert len(storygraph.library_files(fixtures)) == 1


def test_collect_is_deterministic():
    first = storygraph.collect(fixtures)
    second = storygraph.collect(fixtures)
    assert first == second
