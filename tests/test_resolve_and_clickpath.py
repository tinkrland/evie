"""resolution and click paths: matching rows to works, and reaching a file."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ingest import clickpath, manual, resolve
from src.ingest.rows import candidate_doc, row


def _works():
    return {
        "piranesi-2020": {
            "title": "Piranesi",
            "first_release": 2020,
            "external_ids": {"isbn": "9781635575637"},
        },
        "remains-1993": {
            "title": "The Remains of the Day",
            "first_release": 1993,
            "external_ids": {},
        },
        "twin-a": {"title": "Twin", "first_release": 2001, "external_ids": {}},
        "twin-b": {"title": "Twin", "first_release": 2001, "external_ids": {}},
    }


def _candidate(title, year=None, source_id=None):
    return row(title, year, medium="book", source="goodreads", source_id=source_id)


def test_isbn_wins_and_needs_no_title():
    doc = candidate_doc([_candidate("A Totally Different Title", 2020, "9781635575637")], "goodreads")
    out = resolve.resolve_doc(doc, _works())
    assert out["rows"][0]["resolution"]["status"] == "resolved"
    assert out["rows"][0]["resolution"]["method"] == "isbn"
    assert out["rows"][0]["resolution"]["work_ids"] == ["piranesi-2020"]


def test_title_and_year_resolve_without_a_hard_id():
    doc = candidate_doc([_candidate("the remains of the day!", 1993)], "goodreads")
    out = resolve.resolve_doc(doc, _works())
    resolution = out["rows"][0]["resolution"]
    assert resolution["status"] == "resolved"
    assert resolution["method"] == "title-year"
    assert resolution["work_ids"] == ["remains-1993"]


def test_no_fuzzy_matching():
    doc = candidate_doc([_candidate("Piranes", 2020)], "goodreads")
    out = resolve.resolve_doc(doc, _works())
    assert out["rows"][0]["resolution"]["status"] == "unmatched"
    assert out["rows"][0]["resolution"]["work_ids"] == []


def test_two_works_with_one_name_are_ambiguous_not_a_coin_toss():
    doc = candidate_doc([_candidate("Twin", 2001)], "goodreads")
    out = resolve.resolve_doc(doc, _works())
    resolution = out["rows"][0]["resolution"]
    assert resolution["status"] == "ambiguous"
    assert resolution["work_ids"] == ["twin-a", "twin-b"]


def test_unmatched_is_counted_not_dropped():
    doc = candidate_doc([_candidate("Piranesi", 2020, "9781635575637"), _candidate("Nothing", 1999)], "goodreads")
    out = resolve.resolve_doc(doc, _works())
    assert out["summary"] == {"rows": 2, "resolved": 1, "unmatched": 1, "ambiguous": 0}


def test_resolution_dump_is_stable():
    doc = candidate_doc([_candidate("Piranesi", 2020, "9781635575637")], "goodreads")
    first = resolve.dump(resolve.resolve_doc(doc, _works()))
    second = resolve.dump(resolve.resolve_doc(doc, _works()))
    assert first == second
    assert "guessing a work id" in first


def test_every_click_path_in_the_repo_validates():
    paths = sorted(Path("data/clickpaths").glob("*.yaml"))
    assert paths, "no click paths found"
    for path in paths:
        doc = clickpath.load(path.stem)
        assert doc["steps"]
        assert doc["artifact"]["pattern"]


def test_plan_is_followable_by_a_human():
    text = clickpath.plan("repov")
    assert "1. click: My Space" in text
    assert "artifact:" in text
    assert "verified: False" in text


class FakeDriver:
    """stands in for a browser: records clicks, hands back an artifact."""

    def __init__(self, artifact="repov-export.zip"):
        self.clicks = []
        self.artifact = artifact

    def click(self, label):
        self.clicks.append(label)

    def wait_for_file(self, pattern):
        return self.artifact


def test_capture_drives_the_declared_steps_only():
    driver = FakeDriver()
    result = clickpath.capture("repov", driver, downloads=None)
    assert driver.clicks == ["My Space", "Settings", "Export"]
    assert result["artifact"].endswith("repov-export.zip")
    assert result["verified"] is False


def test_a_driver_missing_methods_is_refused_by_name():
    class HalfDriver:
        def click(self, label):
            pass

    with pytest.raises(TypeError, match="wait_for_file"):
        clickpath.capture("repov", HalfDriver(), downloads=None)


def test_missing_click_path_raises():
    with pytest.raises(FileNotFoundError):
        clickpath.load("nonexistent-source")


def test_landing_zone_identifies_by_columns_not_filename(tmp_path):
    goodreads_csv = tmp_path / "data.csv"
    goodreads_csv.write_text(
        "Title,Author,ISBN,ISBN13,My Rating,Date Read,Exclusive Shelf\n"
        'Piranesi,Susanna Clarke,"",9781635575637,5,2024/07/19,read\n'
    )
    storygraph_csv = tmp_path / "library-2026.csv"
    storygraph_csv.write_text(
        "Title,Authors,ISBN/UID,Read Status,Read Count\nPiranesi,Susanna Clarke,9781635575637,read,1\n"
    )
    (tmp_path / "notes.yaml").write_text("not: a csv\n")
    (tmp_path / "archive.zip").write_bytes(b"PK")

    report = manual.scan(tmp_path)
    by_file = {entry["file"]: entry["source"] for entry in report["files"]}
    assert by_file["data.csv"] == "goodreads"
    assert by_file["library-2026.csv"] == "storygraph"
    assert by_file["notes.yaml"] == "unknown"
    assert by_file["archive.zip"] == "archive"
    assert report["summary"]["by_source"]["unknown"] == 1


def test_manual_collect_merges_recognisable_files_and_names_the_rest(tmp_path):
    (tmp_path / "goodreads_library_export.csv").write_text(
        "Title,Author,ISBN,ISBN13,My Rating,Date Read,Exclusive Shelf\n"
        'Piranesi,Susanna Clarke,"",9781635575637,5,2024/07/19,read\n'
        'Ulysses,James Joyce,"",9780394740157,0,,to-read\n'
    )
    (tmp_path / "mystery.csv").write_text("Alpha,Beta\n1,2\n")
    doc = manual.collect(tmp_path)
    assert doc["summary"]["rows"] == 1
    assert doc["summary"]["files_used"] == ["goodreads_library_export.csv"]
    assert doc["summary"]["unknown"] == ["mystery.csv"]
