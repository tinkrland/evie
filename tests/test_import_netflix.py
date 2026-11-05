"""netflix: two columns, and every gap they leave is deliberate."""

import shutil
from pathlib import Path

import pytest

from src.ingest import netflix

fixture_dir = Path(__file__).resolve().parent / "fixtures" / "netflix"


def _collect(tmp_path=None):
    return netflix.collect(tmp_path or fixture_dir)


def test_episodes_are_not_series():
    """a show title with an episode baked in is one row, not a series."""
    rows = {row["title"] for row in _collect()["rows"]}
    assert "The Office: Season 1: Episode 1" in rows
    assert "The Office" not in rows


def test_missing_fields_stay_missing():
    for entry in _collect()["rows"]:
        assert entry["source_id"] is None
        assert entry["year"] is None
        assert entry["medium"] is None


def test_the_source_wording_is_kept():
    row = next(r for r in _collect()["rows"] if "office" in r["title"].lower())
    assert "netflix_title" in row["detail"]
    assert row["detail"]["netflix_title"].lower().startswith("the office")


def test_a_household_profile_row_is_not_discarded():
    """who is who is the owner's call, not a title-matching guess."""
    rows = _collect()["rows"]
    assert any("kids profile" in row["title"].lower() for row in rows)


def test_views_count_repeat_rows():
    rows = _collect()["rows"]
    office = [r for r in rows if "episode 1" in r["title"].lower()][0]
    assert office["detail"]["views"] == 1


def test_missing_file_is_an_empty_import_not_an_error(tmp_path):
    doc = netflix.collect(tmp_path)
    assert doc["summary"]["rows"] == 0


def test_the_download_is_found_by_columns_not_name(tmp_path):
    """netflix renames its own file; the header is the stable part."""
    shutil.copy(fixture_dir / "NetflixViewingActivity.csv", tmp_path / "weird name from netflix.csv")
    (tmp_path / "something else.csv").write_text("a,b\n1,2\n")
    doc = netflix.collect(tmp_path)
    assert doc["summary"]["rows"] == 4


def test_a_csv_that_is_not_viewing_activity_is_ignored(tmp_path):
    (tmp_path / "elsewhere.csv").write_text("Tag,Count\nfiction,3\n")
    assert netflix.collect(tmp_path)["summary"]["rows"] == 0


def test_import_writes_nothing_into_a_taste_context():
    from src.ingest.rows import dump_candidates

    text = dump_candidates(_collect())
    assert "candidates are not taste" in text


@pytest.mark.parametrize("column", ["Title", "Date"])
def test_the_expected_columns_are_the_ones_netflix_ships(column):
    header = (fixture_dir / "NetflixViewingActivity.csv").read_text().splitlines()[0]
    assert column in header
