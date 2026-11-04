"""goodreads import: shelf rules, isbn identity, no taste."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ingest.goodreads import clean_isbn, collect, rows_from_export

root = Path(__file__).resolve().parents[1]
export_dir = root / "tests" / "fixtures" / "goodreads"


def test_only_the_read_shelf_becomes_candidates():
    rows = rows_from_export(export_dir)
    titles = {r["title"] for r in rows}
    assert "Ulysses" not in titles, "a to-read shelf is intentions, not interest"
    assert "The Pale King" not in titles, "currently-reading is unfinished, not a judgement"
    assert "Piranesi" in titles


def test_isbn_armour_is_unwrapped():
    assert clean_isbn('=""9780571258246""') == "9780571258246"
    assert clean_isbn('="0571258248"') == "0571258248"
    assert clean_isbn('=""""') is None
    assert clean_isbn("") is None
    assert clean_isbn("12345") is None, "not an isbn, so not an identity"


def test_editions_of_one_book_are_one_candidate():
    doc = collect(export_dir)
    remains = [r for r in doc["rows"] if r["title"] == "The Remains of the Day"]
    assert len(remains) == 1, "same isbn13 means same book, however many rows"
    assert remains[0]["detail"]["views"] == 3, "read counts add up across editions rows"
    assert remains[0]["source_id"] == "9780571258246"


def test_no_isbn_falls_back_to_title_key():
    doc = collect(export_dir)
    old = [r for r in doc["rows"] if r["title"] == "Old Bones"]
    assert len(old) == 1
    assert old[0]["source_id"] is None, "absent identity stays absent, never invented"


def test_ratings_are_detail_not_taste():
    doc = collect(export_dir)
    for row in doc["rows"]:
        assert "rating" in row["detail"] or row["title"] == "Old Bones"
        assert "taste" not in str(row).lower()
    piranesi = next(r for r in doc["rows"] if r["title"] == "Piranesi")
    assert piranesi["detail"]["rating"] == "5"
    assert piranesi["watched_at"] == "2024/07/19"


def test_import_is_deterministic():
    first = collect(export_dir)
    second = collect(export_dir)
    assert first == second


def test_no_work_id_is_assigned_at_import():
    doc = collect(export_dir)
    for row in doc["rows"]:
        assert "work_id" not in row
        assert row["source"] == "goodreads"
        assert row["medium"] == "book"


def test_missing_file_is_an_empty_import_not_a_crash():
    doc = collect(root / "tests" / "fixtures" / "no-such-export")
    assert doc["rows"] == []
    assert doc["summary"]["rows"] == 0
